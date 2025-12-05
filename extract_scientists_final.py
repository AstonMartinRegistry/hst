#!/usr/bin/env python3
"""
Final Scientist Network Extractor
Uses improved column-aware text extraction to find scientists and their relationships.
"""

import re
import json
import pdfplumber
from pathlib import Path
from typing import Dict, List, Set


class Scientist:
    """Represents a scientist with their biography and connections."""
    
    def __init__(self, id: int, name: str, biography: str, page_number: int):
        self.id = id
        self.name = name
        self.biography = biography
        self.page_number = page_number
        self.connections: Set[int] = set()  # Set of scientist IDs this scientist references
    
    def to_dict(self):
        """Convert to dictionary for JSON output."""
        return {
            "id": self.id,
            "name": self.name,
            "biography_length": len(self.biography),
            "page_number": self.page_number,
            "biography_full": self.biography,  # Include the full biography
            "connections": list(self.connections)
        }


class FinalScientistExtractor:
    """Extracts scientist network using improved column-aware text extraction."""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.scientists: Dict[int, Scientist] = {}
        self.relationships: List[Dict] = []
        
    def extract_text_in_columns(self, page) -> str:
        """Extract text from a page handling two-column layout properly."""
        words = page.extract_words()
        
        if not words:
            return ""
        
        # Remove the first line (page header) by filtering out words at the top
        # Find the y-position of the first few words to identify the header line
        if words:
            # Sort words by y position to find the top line
            sorted_words = sorted(words, key=lambda w: w['top'])
            top_y = sorted_words[0]['top']
            
            # Filter out words that are on the same line as the header (within 5 pixels)
            header_threshold = top_y + 5
            content_words = [w for w in words if w['top'] > header_threshold]
            
            if not content_words:
                content_words = words  # Fallback if we filtered out everything
        else:
            content_words = words
        
        # Determine column boundary (find the gap between columns)
        x_positions = [w['x0'] for w in content_words]
        x_positions.sort()
        
        # Look for the largest gap in x positions (this should be between columns)
        gaps = []
        for j in range(len(x_positions) - 1):
            gap = x_positions[j+1] - x_positions[j]
            gaps.append((gap, x_positions[j], x_positions[j+1]))
        
        # Sort gaps by size and find the largest
        gaps.sort(reverse=True)
        if gaps:
            column_boundary = (gaps[0][1] + gaps[0][2]) / 2
        else:
            column_boundary = page.width / 2
        
        # Separate words into columns
        left_column_words = []
        right_column_words = []
        
        for word in content_words:
            if word['x0'] < column_boundary:
                left_column_words.append(word)
            else:
                right_column_words.append(word)
        
        # Sort each column by y position (top to bottom)
        left_column_words.sort(key=lambda w: w['top'])
        right_column_words.sort(key=lambda w: w['top'])
        
        # Reconstruct text for each column
        left_text = ' '.join([w['text'] for w in left_column_words])
        right_text = ' '.join([w['text'] for w in right_column_words])
        
        # Combine columns in reading order (left then right)
        return left_text + "\n\n" + right_text
    
    def extract_text_from_pdf(self, start_page: int = 33, num_pages: int = 4) -> str:
        """Extract text from PDF using column-aware extraction."""
        print(f"Extracting text from {self.pdf_path}")
        print(f"Pages: {start_page} to {start_page + num_pages - 1}")
        print("Using column-aware text extraction...")
        
        full_text = ""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"PDF has {total_pages} total pages")
                
                # Convert to 0-indexed
                start_idx = start_page - 1
                
                for i in range(num_pages):
                    page_num = start_idx + i
                    if page_num >= total_pages:
                        print(f"Page {page_num + 1} does not exist")
                        break
                        
                    page = pdf.pages[page_num]
                    print(f"Processing page {page_num + 1}/{total_pages}")
                    
                    text = self.extract_text_in_columns(page)
                    if text:
                        full_text += f"\n---PAGE_{page_num + 1}---\n{text}"
                        
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
            
        print(f"Extracted {len(full_text)} characters of text")
        return full_text
    
    def parse_scientist_entries(self, text: str) -> None:
        """Parse the text to extract individual scientist entries using intelligent bracket analysis."""
        print("Parsing scientist entries...")
        
        # First, let's clean up the text to make parsing easier
        # Remove page boundary markers and normalize whitespace
        clean_text = re.sub(r'\n---PAGE_\d+---\n', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # Find all bracket patterns: [number] followed by optional text
        bracket_pattern = r'\[(\d+)\]([^[]*)'
        matches = re.finditer(bracket_pattern, clean_text)
        
        current_scientist = None
        current_biography = ""
        
        for match in matches:
            scientist_id = int(match.group(1))
            text_after_bracket = match.group(2).strip()
            
            # Analyze what comes after [number]
            # Look for a word with multiple capital letters (indicating a new scientist)
            words = text_after_bracket.split()
            if words:
                first_word = words[0]
                capital_count = sum(1 for c in first_word if c.isupper())
                
                # If we have a current scientist, save their biography
                if current_scientist:
                    # Clean up the biography
                    biography = current_biography.strip()
                    biography = re.sub(r'\s+', ' ', biography).strip()
                    
                    # Find which page this scientist appears on
                    page_match = re.search(r'---PAGE_(\d+)---', text[:match.start()])
                    page_number = int(page_match.group(1)) if page_match else 0
                    
                    current_scientist.page_number = page_number
                    current_scientist.biography = biography
                    
                    # Save the completed scientist
                    self.scientists[current_scientist.id] = current_scientist
                
                # Determine if this is a new scientist entry or a reference
                if capital_count >= 2 and len(first_word) > 2:
                    # This is a new scientist entry (e.g., [3] THALES)
                    scientist_name = first_word
                    print(f"Found scientist {scientist_id}: {scientist_name}")
                    
                    # Start new scientist
                    current_scientist = Scientist(
                        id=scientist_id,
                        name=scientist_name,
                        biography="",
                        page_number=0
                    )
                    current_biography = ""
                    
                    # Add the rest of the text after the name to the biography
                    if len(words) > 1:
                        current_biography = ' '.join(words[1:])
                    
                else:
                    # This is a reference to another scientist (e.g., [4])
                    if current_scientist:
                        current_scientist.connections.add(scientist_id)
                        print(f"  {current_scientist.name} -> [{scientist_id}]")
                    
                    # Add this text to the current biography
                    if current_scientist:
                        current_biography += f" [{scientist_id}] {text_after_bracket}"
                    else:
                        # If we don't have a current scientist yet, this might be a reference
                        # before the first scientist entry
                        pass
            else:
                # Empty text after bracket - just a reference
                if current_scientist:
                    current_scientist.connections.add(scientist_id)
                    print(f"  {current_scientist.name} -> [{scientist_id}]")
                    current_biography += f" [{scientist_id}]"
        
        # Don't forget the last scientist
        if current_scientist:
            biography = current_biography.strip()
            biography = re.sub(r'\s+', ' ', biography).strip()
            
            # Find which page this scientist appears on
            page_match = re.search(r'---PAGE_(\d+)---', text[:len(text)-len(current_biography)])
            page_number = int(page_match.group(1)) if page_match else 0
            
            current_scientist.page_number = page_number
            current_scientist.biography = biography
            
            self.scientists[current_scientist.id] = current_scientist
        
        print(f"Found {len(self.scientists)} scientist entries")
    
    def extract_connections(self) -> None:
        """Extract connections between scientists based on cross-references."""
        print("Extracting connections between scientists...")
        
        for scientist_id, scientist in self.scientists.items():
            # Look for references to other scientists in the biography
            # Pattern: [number] which should reference other scientist IDs
            ref_pattern = r'\[(\d+)\]'
            references = re.findall(ref_pattern, scientist.biography)
            
            # Convert to integers and capture ALL references (even to future scientists)
            for ref in references:
                try:
                    ref_id = int(ref)
                    if ref_id != scientist_id:  # Don't self-reference
                        scientist.connections.add(ref_id)
                        print(f"  {scientist.name} -> [{ref_id}]")
                except ValueError:
                    continue
        
        # Count total connections
        total_connections = sum(len(s.connections) for s in self.scientists.values())
        print(f"Found {total_connections} total connections")
        
        # Show all unique references found
        all_references = set()
        for scientist in self.scientists.values():
            all_references.update(scientist.connections)
        all_references = sorted(all_references)
        print(f"All referenced scientist IDs: {all_references}")
        
        # Show which references are to scientists we haven't found yet
        found_ids = set(self.scientists.keys())
        future_references = [ref for ref in all_references if ref not in found_ids]
        if future_references:
            print(f"References to future scientists: {future_references}")
    
    def create_relationships(self) -> None:
        """Create relationship objects for the network."""
        print("Creating relationship objects...")
        
        for scientist_id, scientist in self.scientists.items():
            for target_id in scientist.connections:
                # Check if we have the target scientist in our current dataset
                if target_id in self.scientists:
                    target_name = self.scientists[target_id].name
                else:
                    target_name = f"Unknown Scientist {target_id}"
                
                relationship = {
                    "source": scientist_id,
                    "target": target_id
                }
                self.relationships.append(relationship)
        
        print(f"Created {len(self.relationships)} relationships")
        
        # Count relationships to known vs unknown scientists
        found_ids = set(self.scientists.keys())
        known_targets = sum(1 for r in self.relationships if r["target"] in found_ids)
        unknown_targets = len(self.relationships) - known_targets
        print(f"Relationships to known scientists: {known_targets}")
        print(f"Relationships to future scientists: {unknown_targets}")
    
    def generate_network_json(self, output_path: str) -> None:
        """Generate the final network JSON file."""
        print(f"Generating network JSON to {output_path}")
        
        # Prepare nodes
        nodes = []
        for scientist in self.scientists.values():
            nodes.append(scientist.to_dict())
        
        # Prepare the complete network
        network = {
            "metadata": {
                "total_scientists": len(self.scientists),
                "total_relationships": len(self.relationships),
                "source": "Asimov's Biography of Scientists",
                "extraction_method": "Column-Aware PDF Parser"
            },
            "nodes": nodes,
            "links": self.relationships
        }
        
        # Write to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(network, f, indent=2, ensure_ascii=False)
        
        print(f"Network JSON saved to {output_path}")
    
    def generate_summary_stats(self) -> None:
        """Print comprehensive summary statistics."""
        print("\n" + "="*60)
        print("FINAL NETWORK SUMMARY STATISTICS")
        print("="*60)
        print(f"Total Scientists: {len(self.scientists)}")
        print(f"Total Relationships: {len(self.relationships)}")
        
        # Connection distribution
        connection_counts = [len(s.connections) for s in self.scientists.values()]
        if connection_counts:
            avg_connections = sum(connection_counts) / len(connection_counts)
            max_connections = max(connection_counts)
            min_connections = min(connection_counts)
            
            print(f"Average Connections per Scientist: {avg_connections:.2f}")
            print(f"Max Connections: {max_connections}")
            print(f"Min Connections: {min_connections}")
            
            # Connection distribution
            isolated = sum(1 for c in connection_counts if c == 0)
            connected = len(connection_counts) - isolated
            print(f"Isolated Scientists (0 connections): {isolated}")
            print(f"Connected Scientists: {connected}")
        
        # Most connected scientists
        most_connected = sorted(self.scientists.values(), 
                              key=lambda x: len(x.connections), reverse=True)[:10]
        print("\nTop 10 Most Connected Scientists:")
        for i, scientist in enumerate(most_connected, 1):
            print(f"  {i:2d}. {scientist.name:<25} (ID: {scientist.id:4d}) - {len(scientist.connections):3d} connections")
        
        # Page distribution
        pages_with_scientists = set(s.page_number for s in self.scientists.values() if s.page_number)
        if pages_with_scientists:
            print(f"\nScientists found across {len(pages_with_scientists)} pages")
        
        print("="*60)
    
    def process(self, start_page: int = 33, num_pages: int = 4, output_path: str = "scientist_network_final.json") -> None:
        """Main processing pipeline."""
        print("Starting Final Scientist Network Extraction...")
        print("="*60)
        
        # Step 1: Extract text from PDF using column-aware method
        text = self.extract_text_from_pdf(start_page, num_pages)
        if not text:
            print("Failed to extract text from PDF")
            return
        
        # Step 2: Parse scientist entries
        self.parse_scientist_entries(text)
        
        # Step 3: Extract connections
        self.extract_connections()
        
        # Step 4: Create relationships
        self.create_relationships()
        
        # Step 5: Generate JSON output
        self.generate_network_json(output_path)
        
        # Step 6: Print summary statistics
        self.generate_summary_stats()
        
        print("\nProcessing complete!")


def main():
    """Main function."""
    pdf_path = "book.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file '{pdf_path}' not found")
        print("Please make sure 'book.pdf' is in the same directory as this script.")
        return
    
    # Create extractor and process
    extractor = FinalScientistExtractor(pdf_path)
    # Process more pages to get more scientists and capture more references
    extractor.process(start_page=33, num_pages=923)  # Process from page 33 to 955 (923 pages)


if __name__ == "__main__":
    main() 