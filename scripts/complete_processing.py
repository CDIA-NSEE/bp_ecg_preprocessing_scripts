import os
import csv
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import process_pdf, extract_information

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Define folders and constants
EXAMS_FOLDER = "Exams"
PROBLEMS_FOLDER = "Problems"
OUTPUT_CSV = "extracted_data.csv"
ERROR_FOLDER = "Errors"

# Define bounding boxes for image extraction
BOXES = {
    "ecg": {"output_folder": "ECG_Images", "page_number": 1, "crop_box": (230, 680, 6790, 4432)},
    'speed': {'output_folder': 'Speed', 'page_number': 1, 'crop_box': (170, 563, 180, 570)},
    'amplitude': {'output_folder': 'Amplitude', 'page_number': 1, 'crop_box': (264, 563, 278, 570)}
}

# Ensure necessary folders exist
for folder in [PROBLEMS_FOLDER, ERROR_FOLDER] + [config['output_folder'] for config in BOXES.values()]:
    os.makedirs(folder, exist_ok=True)

# Create CSV file with header if it does not exist
if not os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["File", "Data", "Hora", "Sexo", "Data de Nascimento", "Laudo"])

# Function to process a single PDF file and extract relevant data
def process_single_pdf(pdf_file):
    pdf_path = os.path.join(EXAMS_FOLDER, pdf_file)
    logger.info(f"Processing: {pdf_file}")

    extracted_data = extract_information(pdf_path, PROBLEMS_FOLDER)
    if extracted_data:
        process_pdf(pdf_path, BOXES, ERROR_FOLDER)
        return extracted_data, pdf_path
    return None, pdf_path

# Process all PDFs concurrently
def process_pdfs_concurrently():
    pdf_files = [f for f in os.listdir(EXAMS_FOLDER) if f.endswith(".pdf")]

    rows_to_write = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_single_pdf, pdf_file): pdf_file for pdf_file in pdf_files}

        for future in as_completed(futures):
            extracted_data, pdf_path = future.result()

            if extracted_data:
                rows_to_write.append(extracted_data)

            # Remove the PDF file after processing
            try:
                os.remove(pdf_path)
                logger.info(f"Deleted {pdf_path} after processing.")
            except Exception as e:
                logger.error(f"Failed to delete {pdf_path}: {e}")

    # Write extracted data to CSV after all PDFs have been processed
    if rows_to_write:
        with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(rows_to_write)
        logger.info(f"Extraction complete. Data saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    process_pdfs_concurrently()
