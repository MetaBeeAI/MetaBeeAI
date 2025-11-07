#!/usr/bin/env python3
import PyPDF2
import os
import sys
import argparse
from pathlib import Path

def split_pdfs(papers_dir=None, pages_per_split=1):
    """
    Split PDFs in the specified directory into single-page or overlapping 2-page segments.
    
    Args:
        papers_dir: Directory containing paper subfolders (defaults to config)
        pages_per_split: Number of pages per split (1 or 2). Default is 1.
                        1 = single-page documents
                        2 = overlapping 2-page documents
    """
    # Validate pages_per_split
    if pages_per_split not in [1, 2]:
        print(f"Error: pages_per_split must be 1 or 2, got {pages_per_split}")
        return
    
    # Import centralized configuration if papers_dir not provided
    if papers_dir is None:
        import sys
        sys.path.append('..')
        from config import get_papers_dir
        papers_dir = get_papers_dir()
    
    # Validate papers directory
    if not os.path.exists(papers_dir):
        print(f"Error: Directory '{papers_dir}' does not exist")
        return
    
    # Get all subfolders in the specified directory
    subfolders = [f for f in os.listdir(papers_dir) if os.path.isdir(os.path.join(papers_dir, f))]
    
    if not subfolders:
        print(f"No subfolders found in '{papers_dir}'")
        return
    
    mode = "single-page" if pages_per_split == 1 else "overlapping 2-page"
    print(f"Found {len(subfolders)} subfolders to process in {mode} mode")
    
    for subfolder in subfolders:
        # Create pages directory if it doesn't exist
        pages_dir = os.path.join(papers_dir, subfolder, "pages")
        os.makedirs(pages_dir, exist_ok=True)
        
        # Construct path to main PDF using subfolder name
        pdf_path = os.path.join(papers_dir, subfolder, f"{subfolder}_main.pdf")
        
        if not os.path.exists(pdf_path):
            print(f"PDF file not found at {pdf_path}, skipping...")
            continue
        
        try:
            # read the PDF
            print(f"Processing {pdf_path}...")
            pdf_reader = PyPDF2.PdfReader(pdf_path)
            total_pages = len(pdf_reader.pages)
            
            if pages_per_split == 1:
                # Create single-page PDFs
                splits_created = 0
                for i in range(total_pages):
                    pdf_writer = PyPDF2.PdfWriter()
                    pdf_writer.add_page(pdf_reader.pages[i])
                    
                    output_path = os.path.join(pages_dir, f"main_p{i+1:02d}.pdf")
                    with open(output_path, "wb") as output_file:
                        pdf_writer.write(output_file)
                    splits_created += 1
                
                print(f"Successfully processed {subfolder}_main.pdf ({total_pages} pages, created {splits_created} single-page PDFs)")
            
            elif pages_per_split == 2:
                # Create overlapping 2-page PDFs
                splits_created = 0
                for i in range(total_pages - 1):  # Stop at second-to-last page
                    pdf_writer = PyPDF2.PdfWriter()
                    # Add current page and next page
                    pdf_writer.add_page(pdf_reader.pages[i])
                    pdf_writer.add_page(pdf_reader.pages[i + 1])
                    
                    output_path = os.path.join(pages_dir, f"main_p{i+1:02d}-{i+2:02d}.pdf")
                    with open(output_path, "wb") as output_file:
                        pdf_writer.write(output_file)
                    splits_created += 1
                
                print(f"Successfully processed {subfolder}_main.pdf ({total_pages} pages, created {splits_created} overlapping 2-page PDFs)")
            
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")

if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description='Split PDFs into single-page or overlapping 2-page documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Split into single-page documents (default)
  %(prog)s /path/to/papers
  %(prog)s /path/to/papers --pages 1
  
  # Split into overlapping 2-page documents
  %(prog)s /path/to/papers --pages 2
        """
    )
    parser.add_argument('directory', type=str, help='Directory containing paper subfolders')
    parser.add_argument(
        '--pages', 
        type=int, 
        default=1, 
        choices=[1, 2],
        help='Number of pages per split: 1 for single-page (default), 2 for overlapping 2-page'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the main function
    split_pdfs(args.directory, pages_per_split=args.pages)
    print("Processing complete!") 