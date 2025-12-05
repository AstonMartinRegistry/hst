#!/usr/bin/env python3
"""
Simple Text Extractor
Extracts and displays raw text from pages 33-36 of the PDF for analysis.
"""

import pdfplumber
from pathlib import Path


def extract_text_from_pages(pdf_path: str, start_page: int = 33, num_pages: int = 4):
    """Extract text from specified pages and display it."""
    print(f"Extracting text from {pdf_path}")
    print(f"Pages: {start_page} to {start_page + num_pages - 1}")
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
                text = page.extract_text()
                
                print(f"\n{'='*20} PAGE {page_num + 1} {'='*20}")
                print(f"Text length: {len(text)} characters")
                print("-" * 60)
                print(text)
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
    
    extract_text_from_pages(pdf_path, start_page=33, num_pages=4)


if __name__ == "__main__":
    main() 