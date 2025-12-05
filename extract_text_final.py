#!/usr/bin/env python3
"""
Final Text Extractor
Properly reconstructs text in column order using pdfplumber's word positioning.
"""

import pdfplumber
from pathlib import Path


def extract_text_in_columns(pdf_path: str, start_page: int = 33, num_pages: int = 4):
    """Extract text properly handling two-column layout."""
    print(f"Extracting text from {pdf_path}")
    print(f"Pages: {start_page} to {start_page + num_pages - 1}")
    print("Using proper column-aware text reconstruction...")
    print("="*80)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
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
                
                print(f"\n{'='*20} PAGE {page_num + 1} {'='*20}")
                
                # Get words with positioning
                words = page.extract_words()
                print(f"Found {len(words)} words")
                
                # Determine column boundary (find the gap between columns)
                x_positions = [w['x0'] for w in words]
                x_positions.sort()
                
                # Look for the largest gap in x positions (this should be between columns)
                gaps = []
                for j in range(len(x_positions) - 1):
                    gap = x_positions[j+1] - x_positions[j]
                    gaps.append((gap, x_positions[j], x_positions[j+1]))
                
                # Sort gaps by size and find the largest
                gaps.sort(reverse=True)
                column_boundary = (gaps[0][1] + gaps[0][2]) / 2
                
                print(f"Detected column boundary at x = {column_boundary:.1f}")
                
                # Separate words into columns
                left_column_words = []
                right_column_words = []
                
                for word in words:
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
                
                print(f"\n--- LEFT COLUMN ({len(left_column_words)} words) ---")
                print(left_text)
                
                print(f"\n--- RIGHT COLUMN ({len(right_column_words)} words) ---")
                print(right_text)
                
                # Combine columns in reading order (left then right)
                combined_text = left_text + "\n\n" + right_text
                print(f"\n--- COMBINED TEXT ({len(combined_text)} chars) ---")
                print(combined_text)
                
                print("-" * 60)
                
    except Exception as e:
        print(f"Error reading PDF: {e}")


def main():
    """Main function."""
    pdf_path = "book.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file '{pdf_path}' not found")
        print("Please make sure 'book.pdf' is in the same directory as this script.")
        return
    
    extract_text_in_columns(pdf_path, start_page=33, num_pages=4)


if __name__ == "__main__":
    main() 