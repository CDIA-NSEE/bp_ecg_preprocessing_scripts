import os
import hashlib
import shutil
import logging
import argparse
import pandas as pd
import fitz  # PyMuPDF (for PDF compression)
from pathlib import Path
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_hashed_name(filename: str) -> str:
    """Generate a hashed filename based on SHA-256."""
    return hashlib.sha256(filename.encode()).hexdigest()[:10] + ".pdf"

def compress_pdf(input_path: Path, output_path: Path, quality: int):
    """Compresses a PDF file by converting images to lower quality."""
    try:
        doc = fitz.open(input_path)
        for page in doc:
            img_list = page.get_images(full=True)
            for img_index, img in enumerate(img_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                img_data = base_image["image"]
                img_ext = base_image["ext"]

                # Save image as JPEG (lower quality)
                compressed_img_path = input_path.with_suffix(f".{img_index}.jpg")
                with open(compressed_img_path, "wb") as img_file:
                    img_file.write(img_data)

                # Reinsert image with lower quality
                page.insert_image(page.rect, filename=str(compressed_img_path), quality=quality)

                # Remove temp image
                compressed_img_path.unlink()

        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        return True

    except Exception as e:
        logger.error(f"Error compressing {input_path.name}: {e}")
        return False

def process_single_pdf(args):
    """Processes a single PDF file, compresses it, and returns mapping."""
    original_path, output_folder, quality = args
    try:
        hashed_name = generate_hashed_name(original_path.name)
        anonymized_path = output_folder / hashed_name

        # Copy and compress the PDF
        shutil.copy2(original_path, anonymized_path)
        success = compress_pdf(anonymized_path, anonymized_path, quality)

        if success:
            return [original_path.name, hashed_name]
        else:
            return None

    except Exception as e:
        logger.error(f"Error processing {original_path.name}: {e}")
        return None

def anonymize_pdfs(pdf_folder: Path, output_folder: Path, mapping_file: Path, quality: int):
    """Anonymizes and compresses PDFs, tracks progress, and saves a mapping file."""
    if not pdf_folder.exists():
        logger.error(f"Source folder '{pdf_folder}' does not exist.")
        return

    output_folder.mkdir(parents=True, exist_ok=True)

    pdf_files = list(pdf_folder.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found for anonymization.")
        return

    mapping = []
    num_workers = min(cpu_count(), 8)  # Limit to 8 processes for efficiency

    with Pool(processes=num_workers) as pool:
        with tqdm(total=len(pdf_files), desc="Anonymizing & Compressing PDFs", unit="file") as pbar:
            for result in pool.imap_unordered(process_single_pdf, [(pdf, output_folder, quality) for pdf in pdf_files]):
                if result:
                    mapping.append(result)
                pbar.update(1)

    # Save mapping to CSV in batch
    save_mapping(mapping, mapping_file)
    logger.info(f"Anonymization & compression complete. Mapping saved to {mapping_file}")
    logger.info("Original files are preserved. Delete them manually after verification if necessary.")

def save_mapping(mapping: list, mapping_file: Path):
    """Saves the original-to-anonymized filename mapping to a CSV file."""
    try:
        df = pd.DataFrame(mapping, columns=["Original Filename", "Anonymized Filename"])
        df.to_csv(mapping_file, index=False)
    except Exception as e:
        logger.error(f"Failed to save mapping file {mapping_file}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Anonymize and compress PDFs.")
    parser.add_argument("--quality", type=int, default=70, help="Compression quality (1-100, default: 70)")
    
    args = parser.parse_args()

    pdf_folder = Path("Exams")
    output_folder = Path("Exams_anonymized")
    mapping_file = pdf_folder / "file_mapping.csv"

    anonymize_pdfs(pdf_folder, output_folder, mapping_file, args.quality)
