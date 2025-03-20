import os
import PyPDF2
from fpdf import FPDF
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API credentials from environment variables
LLM_API_URL = os.getenv("LLM_API_URL")
API_KEY = os.getenv("LLM_API_KEY")

def translate_page(text, source_lang="en", target_lang="pt"):
    # Sends a page's text to the LLM API for translation.
    response = requests.post(
        LLM_API_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"text": text, "source_lang": source_lang, "target_lang": target_lang}
    )
    if response.status_code == 200:
        return response.json().get("translated_text", "")
    else:
        raise Exception(f"Translation API failed: {response.status_code} - {response.text}")

def extract_text_from_pdf(pdf_path):
    # Extracts text from each page of the PDF.
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        pages_text = [page.extract_text() for page in reader.pages]
    return pages_text

def create_translated_pdf(translated_pages, output_path):
    # Creates a new PDF with the translated text.
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for page_text in translated_pages:
        pdf.add_page()
        pdf.multi_cell(0, 10, page_text)

    pdf.output(output_path)

def main():
    # Check if API credentials are properly loaded
    if not LLM_API_URL or not API_KEY:
        print("Error: Missing API credentials. Please check your .env file.")
        return

    input_pdf = input("Enter the path to the PDF file: ").strip()
    output_pdf = input("Enter the path for the translated PDF output: ").strip()

    if not os.path.exists(input_pdf):
        print("The specified PDF file does not exist.")
        return

    # Extract text from PDF
    print("Extracting text from PDF...")
    pages_text = extract_text_from_pdf(input_pdf)

    # Translate pages
    print("Translating pages...")
    translated_pages = []
    for i, page_text in enumerate(pages_text):
        print(f"Translating page {i + 1}...")
        translated_text = translate_page(page_text)
        translated_pages.append(translated_text)

    # Create translated PDF
    print("Creating translated PDF...")
    create_translated_pdf(translated_pages, output_pdf)

    print(f"Translation complete. Translated PDF saved to {output_pdf}")

if __name__ == "__main__":
    main()
