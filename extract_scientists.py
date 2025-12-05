#!/usr/bin/env python3
"""
Scientist Network Extractor
Extracts scientist biographies from Asimov's biography PDF and creates a network graph.
"""

import re
import json
import sys
import pdfplumber
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Scientist:
    """Represents a scientist with their biography and connections."""
    id: int
    name: str
    biography: str
    connections: List[int]  # List of scientist IDs this scientist references


class ScientistNetworkExtractor:
    """Extracts scientist network from PDF text."""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.scientists: Dict[int, Scientist] = {}
        self.relationships: List[Dict] = []
        
    def extract_text_from_pdf(self) -> str:
        """Extract text content from PDF using pdfplumber, starting from page 33."""
        print(f"Extracting text from {self.pdf_path}...")
        
        full_text = ""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"Processing {total_pages} pages, starting from page 33...")
                
                # Start from page 33 (index 32) and only process 4 pages for testing
                start_page = 32  # 0-indexed, so page 33 is index 32
                end_page = start_page + 4  # Process only 4 pages (33, 34, 35, 36)
                
                print(f"Testing with pages {start_page + 1} to {end_page} only")
                
                for page_num, page in enumerate(pdf.pages[start_page:end_page], start_page + 1):
                    print(f"Processing page {page_num}/{total_pages}")
                    
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                        print(f"Page {page_num} text length: {len(text)} characters")
                        
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
            
        print(f"Extracted {len(full_text)} characters of text starting from page 33")
        
        # Debug: Show the first 2000 characters to see what we're working with
        print("\n" + "="*60)
        print("DEBUG: FIRST 2000 CHARACTERS OF EXTRACTED TEXT")
        print("="*60)
        print(full_text[:2000])
        print("="*60)
        
        return full_text
    
    def parse_scientist_entries(self, text: str) -> None:
        """Parse the text to extract individual scientist entries."""
        print("Parsing scientist entries...")
        
        # Find scientist entries with format: [number] NAME (pronunciation)
        # Look for patterns like [1] IMHOTEP (im-hoh'tep), [2] AHMOSE (ah'mose), etc.
        potential_entries = re.finditer(r'\[(\d+)\]\s*([A-Z][A-Z\s\-\'\.]+?)\s*\([^)]+\)', text, re.MULTILINE | re.DOTALL)
        
        # Filter out header references (like [3] THALES THALES [3] at top of pages)
        # and find actual biography entries
        valid_entries = []
        
        for match in potential_entries:
            scientist_id = int(match.group(1))
            name = match.group(2).strip()
            
            # Get the text after this match to see if it's a real entry
            start_pos = match.end()
            
            # Look for the next scientist entry with the same format [number] NAME (pronunciation)
            next_match = re.search(r'\[\d+\]\s*[A-Z][A-Z\s\-\'\.]+?\s*\([^)]+\)', text[start_pos:])
            
            if next_match:
                end_pos = start_pos + next_match.start()
            else:
                end_pos = len(text)
            
            biography_text = text[start_pos:end_pos].strip()
            
            # Check if this looks like a real biography entry
            # Real entries should have substantial text and not be just headers
            if (len(biography_text) > 30 and  # Lowered threshold for testing
                not re.search(r'\[[^\]]+\]\s*[A-Z]+\s*\[[^\]]+\]', biography_text[:100])):  # Not a header
                
                valid_entries.append({
                    'id': scientist_id,
                    'name': name,
                    'start': match.start(),
                    'end': end_pos,
                    'biography': biography_text
                })
        
        # Now create the scientist objects
        for entry in valid_entries:
            scientist = Scientist(
                id=entry['id'],
                name=entry['name'],
                biography=entry['biography'],
                connections=[]
            )
            
            self.scientists[entry['id']] = scientist
            
        print(f"Found {len(self.scientists)} valid scientist entries")
        
        # Debug: Show what we found
        if valid_entries:
            print("\nDEBUG: Found entries:")
            for entry in valid_entries[:3]:  # Show first 3
                print(f"  ID: {entry['id']}, Name: {entry['name']}")
                print(f"  Biography preview: {entry['biography'][:100]}...")
                print()
    
    def extract_connections(self) -> None:
        """Extract connections between scientists based on cross-references."""
        print("Extracting connections between scientists...")
        
        for scientist_id, scientist in self.scientists.items():
            # Look for references to other scientists in the biography
            # Pattern: [number] which should reference other scientist IDs
            ref_pattern = r'\[(\d+)\]'
            references = re.findall(ref_pattern, scientist.biography)
            
            # Convert to integers and filter valid scientist IDs
            valid_refs = []
            for ref in references:
                try:
                    ref_id = int(ref)
                    if ref_id in self.scientists and ref_id != scientist_id:
                        valid_refs.append(ref_id)
                except ValueError:
                    continue
            
            scientist.connections = list(set(valid_refs))  # Remove duplicates
            
        # Count total connections
        total_connections = sum(len(s.connections) for s in self.scientists.values())
        print(f"Found {total_connections} total connections")
    
    def create_relationships(self) -> None:
        """Create relationship objects for the network."""
        print("Creating relationship objects...")
        
        for scientist_id, scientist in self.scientists.items():
            for target_id in scientist.connections:
                relationship = {
                    "source": scientist_id,
                    "target": target_id,
                    "type": "references"
                }
                self.relationships.append(relationship)
        
        print(f"Created {len(self.relationships)} relationships")
    
    def generate_network_json(self, output_path: str) -> None:
        """Generate the final network JSON file."""
        print(f"Generating network JSON to {output_path}...")
        
        # Prepare nodes
        nodes = []
        for scientist in self.scientists.values():
            node = {
                "id": scientist.id,
                "name": scientist.name,
                "biography_length": len(scientist.biography),
                "connection_count": len(scientist.connections)
            }
            nodes.append(node)
        
        # Prepare the complete network
        network = {
            "metadata": {
                "total_scientists": len(self.scientists),
                "total_relationships": len(self.relationships),
                "source": "Asimov's Biography of Scientists"
            },
            "nodes": nodes,
            "relationships": self.relationships
        }
        
        # Write to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(network, f, indent=2, ensure_ascii=False)
        
        print(f"Network JSON saved to {output_path}")
    
    def generate_summary_stats(self) -> None:
        """Print summary statistics about the network."""
        print("\n" + "="*50)
        print("NETWORK SUMMARY STATISTICS")
        print("="*50)
        print(f"Total Scientists: {len(self.scientists)}")
        print(f"Total Relationships: {len(self.relationships)}")
        
        # Connection distribution
        connection_counts = [len(s.connections) for s in self.scientists.values()]
        avg_connections = sum(connection_counts) / len(connection_counts) if connection_counts else 0
        max_connections = max(connection_counts) if connection_counts else 0
        min_connections = min(connection_counts) if connection_counts else 0
        
        print(f"Average Connections per Scientist: {avg_connections:.2f}")
        print(f"Max Connections: {max_connections}")
        print(f"Min Connections: {min_connections}")
        
        # Most connected scientists
        most_connected = sorted(self.scientists.values(), 
                              key=lambda x: len(x.connections), reverse=True)[:5]
        print("\nTop 5 Most Connected Scientists:")
        for i, scientist in enumerate(most_connected, 1):
            print(f"  {i}. {scientist.name} (ID: {scientist.id}) - {len(scientist.connections)} connections")
        
        print("="*50)
    
    def process(self, output_path: str = "scientist_network.json") -> None:
        """Main processing pipeline."""
        print("Starting Scientist Network Extraction...")
        print("="*50)
        
        # Step 1: Extract text from PDF
        text = self.extract_text_from_pdf()
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
    """Main function to run the extraction."""
    # Hardcoded PDF path
    pdf_path = "book.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file '{pdf_path}' not found")
        print("Please make sure the PDF file is in the same directory as this script.")
        sys.exit(1)
    
    print(f"Using PDF: {pdf_path}")
    
    # Create extractor and process
    extractor = ScientistNetworkExtractor(pdf_path)
    extractor.process()


if __name__ == "__main__":
    main() 