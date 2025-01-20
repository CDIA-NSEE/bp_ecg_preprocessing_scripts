import re
import os
import shutil
import csv
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import PyPDF2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Define folders
EXAMS_FOLDER = "Exams"
PROBLEMS_FOLDER = "Problems"
OUTPUT_CSV = "extracted_data.csv"

# Ensure Problems folder exists
Path(PROBLEMS_FOLDER).mkdir(parents=True, exist_ok=True)

# Create CSV file with header if it does not exist
def create_csv_header():
    if not Path(OUTPUT_CSV).exists():
        with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["File", "Data", "Hora", "Sexo", "Data de Nascimento", "Laudo"])

# Function to extract information from a PDF
def extract_information(pdf_path):
    try:
        # Open the PDF
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)

            # Check if PDF has at least two pages
            if len(reader.pages) < 2:
                logger.info(f"Moving {pdf_path} to Problems folder (only {len(reader.pages)} page(s))")
                shutil.move(pdf_path, Path(PROBLEMS_FOLDER) / Path(pdf_path).name)
                return None

            # Extract text from the first page
            page = reader.pages[0]
            text = page.extract_text()

            if text is None:
                logger.warning(f"No text extracted from {pdf_path}")
                return None

            # Extract fields using regex
            data_match = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", text)
            hora_match = re.search(r"Hora:\s*(\d{2}:\d{2})", text)
            sexo_match = re.search(r"Sexo:\s*(\w+)", text)
            nascimento_match = re.search(r"Data de Nascimento:\s*(\d{2}/\d{2}/\d{4})", text)

            # Extracting the "Laudo" section
            laudo_match = re.search(r"Laudo(.*?)Eletrocardiográficos - 2022", text, re.DOTALL)

            return [
                Path(pdf_path).name,
                data_match.group(1) if data_match else None,
                hora_match.group(1) if hora_match else None,
                sexo_match.group(1) if sexo_match else None,
                nascimento_match.group(1) if nascimento_match else None,
                laudo_match.group(1).strip() if laudo_match else None,
            ]
    except Exception as e:
        logger.error(f"Error processing {pdf_path}: {e}")
        return None

# Function to process PDFs and return extracted data
def process_pdf(pdf_file):
    pdf_path = Path(EXAMS_FOLDER) / pdf_file
    logger.info(f"Processing: {pdf_file}")

    return extract_information(pdf_path)

# Function to save data in bulk to CSV
def save_data_to_csv(data):
    with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(data)
    logger.info(f"Batch data saved to {OUTPUT_CSV}")

# Function to process PDFs using parallel processing
def process_pdfs():
    extracted_data = []

    # Use ThreadPoolExecutor for parallel processing of PDF files
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_pdf, pdf_file): pdf_file for pdf_file in os.listdir(EXAMS_FOLDER) if pdf_file.endswith(".pdf")}

        for future in as_completed(futures):
            data = future.result()
            if data:
                extracted_data.append(data)
            else:
                # If there's an issue with processing, move file to Problems folder
                pdf_file = futures[future]
                shutil.move(Path(EXAMS_FOLDER) / pdf_file, Path(PROBLEMS_FOLDER) / pdf_file)
                logger.info(f"Moved problematic PDF: {pdf_file}")

    # Save all the extracted data to CSV after processing
    if extracted_data:
        save_data_to_csv(extracted_data)
    else:
        logger.warning("No data extracted.")

if __name__ == "__main__":
    create_csv_header()  # Create the CSV file if it doesn't exist
    process_pdfs()  # Process the PDFs and extract data
