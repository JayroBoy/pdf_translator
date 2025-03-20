from google import genai
from google.genai import types
import pathlib
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")
client = genai.Client(api_key=api_key)

# Retrieve and encode the PDF byte
filepath = pathlib.Path(input("Digite o caminho do arquivo(sem extensão)") + '.pdf')
assert filepath.exists(), "File not found"
assert filepath.is_file(), "Not a file"
assert filepath.suffix == ".pdf", "Not a PDF file"

prompt = "translate the text of the pdf file into brazilian portuguese"
response = client.models.generate_content(
  model="gemini-1.5-flash",
  contents=[
      types.Part.from_bytes(
        data=filepath.read_bytes(),
        mime_type='application/pdf',
      ),
      prompt])


with open("output.txt", "w") as f:
    f.write(response.text)
