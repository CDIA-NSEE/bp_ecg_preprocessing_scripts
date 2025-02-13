import os
import csv
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import process_pdf, extract_information

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Define folders
EXAMS_FOLDER = Path("Exams")
PROBLEMS_FOLDER = Path("Problems")
OUTPUT_CSV = Path("extracted_data.csv")
ERROR_FOLDER = Path("Errors")

# Define bounding boxes for image extraction
BOXES = {
    "ecg": {"output_folder": "ECG_Images", "page_number": 1, "crop_box": (230, 680, 6790, 4432)},
    "speed": {"output_folder": "Speed", "page_number": 1, "crop_box": (170, 563, 180, 570)},
    "amplitude": {"output_folder": "Amplitude", "page_number": 1, "crop_box": (264, 563, 278, 570)},
}

def setup_folders():
    """Ensure necessary folders exist."""
    for folder in [PROBLEMS_FOLDER, ERROR_FOLDER] + [Path(config["output_folder"]) for config in BOXES.values()]:
        folder.mkdir(parents=True, exist_ok=True)

    # Create CSV file with header if it does not exist
    if not OUTPUT_CSV.exists():
        with OUTPUT_CSV.open(mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["File", "Data", "Hora", "Sexo", "Data de Nascimento", "Laudo"])

def process_single_pdf(pdf_path: Path):
    """Processes a single PDF file, extracts information, and returns the extracted data."""
    try:
        extracted_data = extract_information(pdf_path, PROBLEMS_FOLDER)
        process_pdf(pdf_path, BOXES, ERROR_FOLDER)

        if extracted_data:
            return extracted_data, pdf_path
        return None, pdf_path

    except Exception as e:
        logger.exception(f"Error processing {pdf_path.name}: {e}")
        pdf_path.rename(ERROR_FOLDER / pdf_path.name)  # Move problematic PDF to error folder
        return None, None

def process_pdfs_concurrently():
    """Processes all PDFs in the Exams folder concurrently using a ThreadPoolExecutor."""
    if not EXAMS_FOLDER.exists():
        logger.error(f"Exams folder '{EXAMS_FOLDER}' does not exist!")
        return

    pdf_files = list(EXAMS_FOLDER.glob("*.pdf"))

    if not pdf_files:
        logger.info("No PDF files found. Exiting.")
        return

    rows_to_write = []
    max_workers = min(8, os.cpu_count() or 2)  # Adjust thread count dynamically

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_pdf, pdf): pdf for pdf in pdf_files}

        for future in as_completed(futures):
            extracted_data, pdf_path = future.result()

            if extracted_data:
                rows_to_write.append(extracted_data)

            if pdf_path and pdf_path.exists():
                try:
                    pdf_path.unlink()  # Delete processed PDF
                    logger.info(f"Deleted {pdf_path} after processing.")
                except Exception as e:
                    logger.error(f"Failed to delete {pdf_path}: {e}")

    # Write extracted data to CSV in batch
    if rows_to_write:
        with OUTPUT_CSV.open(mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(rows_to_write)
        logger.info(f"Extraction complete. Data saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    setup_folders()
    process_pdfs_concurrently()
