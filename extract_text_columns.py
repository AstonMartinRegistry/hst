#!/usr/bin/env python3
"""
Two-Column Text Extractor
Extracts text from PDF with two-column layout by processing each column separately.
"""

import pdfplumber
from pathlib import Path


def extract_text_by_columns(pdf_path: str, start_page: int = 33, num_pages: int = 4):
    """Extract text from PDF handling two-column layout properly."""
    print(f"Extracting text from {pdf_path}")
    print(f"Pages: {start_page} to {start_page + num_pages - 1}")
    print("Handling two-column layout...")
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
                
                # Get page dimensions
                width = page.width
                height = page.height
                print(f"Page dimensions: {width:.1f} x {height:.1f}")
                
                # Define column boundaries with some margin
                margin = 20  # pixels
                left_col_width = (width - 2 * margin) * 0.5
                right_col_width = (width - 2 * margin) * 0.5
                
                # Extract left column
                left_col = page.crop((margin, margin, margin + left_col_width, height - margin))
                left_text = left_col.extract_text()
                
                # Extract right column  
                right_col = page.crop((margin + left_col_width, margin, width - margin, height - margin))
                right_text = right_col.extract_text()
                
                print(f"\n--- LEFT COLUMN ({len(left_text)} chars) ---")
                print(left_text)
                print(f"\n--- RIGHT COLUMN ({len(right_text)} chars) ---")
                print(right_text)
                
                # Combine columns in reading order (left column first, then right)
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
    
    extract_text_by_columns(pdf_path, start_page=33, num_pages=4)


if __name__ == "__main__":
    main() 