import fitz  # PyMuPDF
import re
import os
import pandas as pd
import shutil
import csv

# Define folders
EXAMS_FOLDER = "Exams"
PROBLEMS_FOLDER = "Problems"
OUTPUT_CSV = "extracted_data.csv"

# Ensure Problems folder exists
os.makedirs(PROBLEMS_FOLDER, exist_ok=True)

# Create CSV file with header if it does not exist
if not os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["File", "Data", "Hora", "Sexo", "Data de Nascimento", "Laudo"])

# Function to extract information from a PDF
def extract_information(pdf_path):
    doc = fitz.open(pdf_path)

    # Check if PDF has at least two pages
    if len(doc) < 2:
        print(f"Moving {pdf_path} to Problems folder (only {len(doc)} page(s))")
        shutil.move(pdf_path, os.path.join(PROBLEMS_FOLDER, os.path.basename(pdf_path)))
        return None

    text = doc[0].get_text()  # Extract text from the first page

    # Extract fields using regex
    data_match = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", text)
    hora_match = re.search(r"Hora:\s*(\d{2}:\d{2})", text)
    sexo_match = re.search(r"Sexo:\s*(\w+)", text)
    nascimento_match = re.search(r"Data de Nascimento:\s*(\d{2}/\d{2}/\d{4})", text)

    # Extracting the "Laudo" section
    laudo_match = re.search(r"Laudo(.*?)Eletrocardiográficos - 2022", text, re.DOTALL)

    extracted_data = [
        os.path.basename(pdf_path),
        data_match.group(1) if data_match else None,
        hora_match.group(1) if hora_match else None,
        sexo_match.group(1) if sexo_match else None,
        nascimento_match.group(1) if nascimento_match else None,
        laudo_match.group(1).strip() if laudo_match else None,
    ]

    return extracted_data

# Process each PDF file in the Exams folder
for pdf_file in os.listdir(EXAMS_FOLDER):
    if pdf_file.endswith(".pdf"):
        pdf_path = os.path.join(EXAMS_FOLDER, pdf_file)
        print(f"Processing: {pdf_file}")

        extracted_data = extract_information(pdf_path)

        if extracted_data:
            # Append data to CSV immediately
            with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(extracted_data)

            # Delete the processed PDF file
            os.remove(pdf_path)
            print(f"Deleted {pdf_file} after processing.")

print(f"Extraction complete. Data saved to {OUTPUT_CSV}")