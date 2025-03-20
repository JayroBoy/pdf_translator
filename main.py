import os
import PyPDF2
from fpdf import FPDF
import requests
from dotenv import load_dotenv
import time
import re
from tqdm import tqdm
from google import genai

# Load environment variables from .env file
load_dotenv()

# Get API credentials from environment variables
LLM_API_URL = os.getenv("LLM_API_URL")
API_KEY = os.getenv("LLM_API_KEY")
CLIENT = genai.Client( api_key = API_KEY)

def clean_text(text):
    # Remove or replace unwanted characters
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
    return text

def chunk_text(text, chunk_size=1000):
    # Split text into smaller chunks to avoid API limits
    chunks = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def translate_page(text, source_lang="en", target_lang="pt"):
    # Translate a page by breaking it into chunks if needed
    if len(text) <= 1000:
        return translate_chunk(text, source_lang, target_lang)
    
    # Otherwise, split into chunks and translate each
    chunks = chunk_text(text)
    translated_chunks = []
    
    for chunk in tqdm(chunks, desc="Translating chunks", leave=False):
        translated_chunk = translate_chunk(chunk, source_lang, target_lang)
        translated_chunks.append(translated_chunk)
        time.sleep(10)  # Rate limiting between chunk requests
    
    return " ".join(translated_chunks)

def translate_chunk(text, source_lang="en", target_lang="pt"):
    # Send a chunk of text to the LLM API for translation with retries
    max_retries = 3
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            response = CLIENT
            response.raise_for_status()

            if response.status_code == 200:
                return response.json().get("translated_text", "")
            else:
                print(f"Attempt {attempt + 1} failed with status code: {response.status_code}")
                time.sleep(retry_delay)

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed with exception: {e}")
            time.sleep(retry_delay)

    raise Exception(f"Translation failed after {max_retries} attempts.")

def extract_text_from_pdf(pdf_path):
    # Extract text from a PDF file
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        pages_text = []
        total_pages = len(reader.pages)
        
        print(f"Total pages: {total_pages}")
        for i, page in enumerate(tqdm(reader.pages, desc="Extracting text")):
            text = page.extract_text()
            cleaned_text = clean_text(text)
            pages_text.append(cleaned_text)
    return pages_text

def create_translated_pdf(translated_pages, output_path):
    # Create a translated PDF file
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for page_text in tqdm(translated_pages, desc="Creating PDF"):
        pdf.add_page()
        try:
            pdf.multi_cell(0, 10, page_text)
        except Exception as e:
            pdf.multi_cell(0, 10, "Translation Error")

    pdf.output(output_path)

def main():
    # Check if API credentials are properly loaded
    if not LLM_API_URL or not API_KEY:
        print("Error: Missing API credentials. Please check your .env file.")
        return

    # Get input and output PDF paths from the user
    input_pdf = input("Enter the path to the PDF file: ").strip()
    output_pdf = input("Enter the path for the translated PDF output: ").strip()

    # Check if the input PDF file exists
    if not os.path.exists(input_pdf):
        print("The specified PDF file does not exist.")
        return

    # Extract text from PDF
    print("Extracting text from PDF...")
    pages_text = extract_text_from_pdf(input_pdf)

    # Translate pages
    print("Translating pages...")
    translated_pages = []
    for i, page_text in enumerate(tqdm(pages_text, desc="Translating pages")):
        try:
            translated_text = translate_page(page_text)
            translated_pages.append(translated_text)
        except Exception as e:
            print(f"Translation failed for page {i + 1}: {e}")
            translated_pages.append(f"Translation failed for page {i+1}")

    # Create translated PDF
    print("Creating translated PDF...")
    create_translated_pdf(translated_pages, output_pdf)

    # Notify the user that the translation is complete
    print(f"Translation complete. Translated PDF saved to {output_pdf}")

if __name__ == "__main__":
    main()
