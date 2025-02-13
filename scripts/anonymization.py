import os
import hashlib
import shutil
import logging
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_hashed_name(filename: str) -> str:
    """Generate a hashed filename based on SHA-256."""
    return hashlib.sha256(filename.encode()).hexdigest()[:10] + ".pdf"

def process_single_pdf(original_path: Path, output_folder: Path):
    """Processes a single PDF file, copies it with an anonymized name, and returns mapping."""
    try:
        hashed_name = generate_hashed_name(original_path.name)
        anonymized_path = output_folder / hashed_name

        shutil.copy2(original_path, anonymized_path)
        logger.info(f"Anonymized: {original_path.name} -> {hashed_name}")
        return [original_path.name, hashed_name]
    
    except Exception as e:
        logger.error(f"Error processing {original_path.name}: {e}")
        return None

def anonymize_pdfs(pdf_folder: Path, output_folder: Path, mapping_file: Path):
    """Anonymizes PDF filenames and saves a mapping file."""
    if not pdf_folder.exists():
        logger.error(f"Source folder '{pdf_folder}' does not exist.")
        return

    output_folder.mkdir(parents=True, exist_ok=True)

    pdf_files = list(pdf_folder.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found for anonymization.")
        return

    mapping = []
    max_workers = min(8, os.cpu_count() or 2)  # Adjust thread count dynamically

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_pdf, pdf, output_folder): pdf for pdf in pdf_files}

        for future in as_completed(futures):
            result = future.result()
            if result:
                mapping.append(result)

    # Save mapping to CSV in batch
    save_mapping(mapping, mapping_file)
    logger.info(f"Anonymization complete. Mapping saved to {mapping_file}")
    logger.info("Original files are preserved. Delete them manually after verification if necessary.")

def save_mapping(mapping: list, mapping_file: Path):
    """Saves the original-to-anonymized filename mapping to a CSV file."""
    try:
        df = pd.DataFrame(mapping, columns=["Original Filename", "Anonymized Filename"])
        df.to_csv(mapping_file, index=False)
    except Exception as e:
        logger.error(f"Failed to save mapping file {mapping_file}: {e}")

if __name__ == "__main__":
    pdf_folder = Path("Exams")
    output_folder = Path("Exams_anonymized")
    mapping_file = pdf_folder / "file_mapping.csv"

    anonymize_pdfs(pdf_folder, output_folder, mapping_file)
