#!/usr/bin/env python3
"""
Smart Text Extractor
Uses pdfplumber's built-in text positioning and flow detection to handle columns properly.
"""

import pdfplumber
from pathlib import Path


def extract_text_smart(pdf_path: str, start_page: int = 33, num_pages: int = 4):
    """Extract text using pdfplumber's smart text flow detection."""
    print(f"Extracting text from {pdf_path}")
    print(f"Pages: {start_page} to {start_page + num_pages - 1}")
    print("Using smart text flow detection...")
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
                
                # Method 1: Use built-in text flow (most natural reading order)
                print("\n--- METHOD 1: Natural Text Flow ---")
                text_flow = page.extract_text()
                print(f"Text length: {len(text_flow)} characters")
                print(text_flow)
                
                # Method 2: Extract text with positioning info
                print(f"\n--- METHOD 2: Text with Position Info ---")
                chars = page.chars
                print(f"Found {len(chars)} text characters")
                
                # Group characters by approximate column
                left_chars = []
                right_chars = []
                page_width = page.width
                
                for char in chars:
                    x = char['x0']
                    if x < page_width / 2:
                        left_chars.append(char)
                    else:
                        right_chars.append(char)
                
                # Sort by y position (top to bottom) within each column
                left_chars.sort(key=lambda c: c['y0'])
                right_chars.sort(key=lambda c: c['y0'])
                
                # Extract text from each column
                left_text = ''.join([c['text'] for c in left_chars])
                right_text = ''.join([c['text'] for c in right_chars])
                
                print(f"\nLeft column ({len(left_chars)} chars):")
                print(left_text)
                print(f"\nRight column ({len(right_chars)} chars):")
                print(right_text)
                
                # Method 3: Use words with positioning and sort by reading order
                print(f"\n--- METHOD 3: Words with Position Info ---")
                words = page.extract_words()
                print(f"Found {len(words)} words")
                
                # Show first few words with their positions
                for i, word in enumerate(words[:20]):
                    print(f"Word {i+1}: '{word['text']}' at x={word['x0']:.1f}, y={word['top']:.1f}")
                
                # Method 4: Try to reconstruct text in proper reading order
                print(f"\n--- METHOD 4: Reconstructed Reading Order ---")
                
                # Sort words by y position first (top to bottom), then by x position (left to right)
                sorted_words = sorted(words, key=lambda w: (w['top'], w['x0']))
                
                # Reconstruct text
                reconstructed_text = ' '.join([w['text'] for w in sorted_words])
                print(f"Reconstructed text length: {len(reconstructed_text)} characters")
                print(reconstructed_text[:500] + "..." if len(reconstructed_text) > 500 else reconstructed_text)
                
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
    
    extract_text_smart(pdf_path, start_page=33, num_pages=4)


if __name__ == "__main__":
    main() 