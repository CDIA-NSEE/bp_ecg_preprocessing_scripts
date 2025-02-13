import os
import csv
import logging
import argparse
import fitz  # PyMuPDF (for PDF compression)
from pathlib import Path
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from utils import process_pdf, extract_information

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Define folders
EXAMS_FOLDER = Path("Exams")
PROCESSED_FOLDER = Path("Processed")
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
    for folder in [PROCESSED_FOLDER, PROBLEMS_FOLDER, ERROR_FOLDER] + [Path(config["output_folder"]) for config in BOXES.values()]:
        folder.mkdir(parents=True, exist_ok=True)

    # Create CSV file with header if it does not exist
    if not OUTPUT_CSV.exists():
        with OUTPUT_CSV.open(mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["File", "Data", "Hora", "Sexo", "Data de Nascimento", "Laudo"])

def compress_pdf(input_path: Path, output_path: Path, quality: int):
    """Compresses a PDF file by converting images to lower quality."""
    try:
        doc = fitz.open(input_path)
        for page in doc:
            img_list = page.get_images(full=True)
            for img in img_list:
                xref = img[0]
                base_image = doc.extract_image(xref)
                img_data = base_image["image"]

                # Save image as lower-quality JPEG
                compressed_img_path = input_path.with_suffix(".jpg")
                with open(compressed_img_path, "wb") as img_file:
                    img_file.write(img_data)

                # Reinsert image with lower quality
                page.insert_image(page.rect, filename=str(compressed_img_path), quality=quality)

                # Remove temporary image file
                compressed_img_path.unlink()

        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        return True

    except Exception as e:
        logger.error(f"Error compressing {input_path.name}: {e}")
        return False

def process_single_pdf(args):
    """Processes a single PDF file, extracts information, compresses it, and returns the extracted data."""
    pdf_path, quality = args
    try:
        extracted_data = extract_information(pdf_path, PROBLEMS_FOLDER)
        process_pdf(pdf_path, BOXES, ERROR_FOLDER)

        # Compress the processed PDF with user-defined quality
        compressed_pdf_path = PROCESSED_FOLDER / pdf_path.name  # Move to Processed folder
        compress_pdf(pdf_path, compressed_pdf_path, quality)

        if extracted_data:
            return extracted_data, pdf_path
        return None, pdf_path

    except Exception as e:
        logger.exception(f"Error processing {pdf_path.name}: {e}")
        pdf_path.rename(ERROR_FOLDER / pdf_path.name)  # Move problematic PDF to error folder
        return None, None

def process_pdfs_concurrently(quality: int):
    """Processes all PDFs in the Exams folder concurrently using multiprocessing."""
    if not EXAMS_FOLDER.exists():
        logger.error(f"Exams folder '{EXAMS_FOLDER}' does not exist!")
        return

    pdf_files = list(EXAMS_FOLDER.glob("*.pdf"))

    if not pdf_files:
        logger.info("No PDF files found. Exiting.")
        return

    rows_to_write = []
    num_workers = min(cpu_count(), 8)  # Limit to 8 processes for efficiency

    with Pool(processes=num_workers) as pool:
        with tqdm(total=len(pdf_files), desc="Processing & Compressing PDFs", unit="file") as pbar:
            for result in pool.imap_unordered(process_single_pdf, [(pdf, quality) for pdf in pdf_files]):
                extracted_data, pdf_path = result

                if extracted_data:
                    rows_to_write.append(extracted_data)

                if pdf_path and pdf_path.exists():
                    try:
                        processed_path = PROCESSED_FOLDER / pdf_path.name
                        pdf_path.rename(processed_path)  # Move processed PDF instead of deleting
                        logger.info(f"Moved {pdf_path} to {processed_path}")
                    except Exception as e:
                        logger.error(f"Failed to move {pdf_path}: {e}")

                pbar.update(1)

    # Write extracted data to CSV in batch
    if rows_to_write:
        with OUTPUT_CSV.open(mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(rows_to_write)
        logger.info(f"Extraction complete. Data saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process and compress PDFs while keeping original files.")
    parser.add_argument("--quality", type=int, default=70, help="Compression quality (1-100, default: 70)")

    args = parser.parse_args()

    setup_folders()
    process_pdfs_concurrently(args.quality)
