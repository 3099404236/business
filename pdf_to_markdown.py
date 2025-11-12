#!/usr/bin/env python3
import fitz  # PyMuPDF
import os
import glob

def pdf_to_markdown(pdf_path):
    """Convert PDF to Markdown format"""
    print(f"Processing {pdf_path}...")

    # Open PDF
    doc = fitz.open(pdf_path)

    # Extract text from all pages
    markdown_content = []
    markdown_content.append(f"# {os.path.basename(pdf_path)}\n\n")

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        # Add page header
        markdown_content.append(f"## Page {page_num + 1}\n\n")
        markdown_content.append(text)
        markdown_content.append("\n\n---\n\n")

    doc.close()

    return "".join(markdown_content)

def main():
    # Find all PDF files
    pdf_files = glob.glob("*.pdf")

    if not pdf_files:
        print("No PDF files found!")
        return

    print(f"Found {len(pdf_files)} PDF files")

    # Create markdown directory if it doesn't exist
    os.makedirs("markdown", exist_ok=True)

    # Process each PDF
    for pdf_file in pdf_files:
        try:
            markdown_content = pdf_to_markdown(pdf_file)

            # Save to markdown file
            base_name = os.path.splitext(pdf_file)[0]
            md_file = f"markdown/{base_name}.md"

            with open(md_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            print(f"✓ Converted {pdf_file} -> {md_file}")

        except Exception as e:
            print(f"✗ Error processing {pdf_file}: {e}")

    print("\nConversion complete!")

if __name__ == "__main__":
    main()
