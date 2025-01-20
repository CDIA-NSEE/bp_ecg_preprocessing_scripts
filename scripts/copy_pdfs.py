import os
import shutil
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("copy_log.log", mode='a')]
)
logger = logging.getLogger(__name__)

# Paths to folders
source_folder = Path("Exams")
destination_folder = Path("Exams_Copies")

# Number of copies per PDF
num_copies = 50

# Ensure the destination folder exists
destination_folder.mkdir(parents=True, exist_ok=True)

# Function to copy a file multiple times
def copy_file(file_path, num_copies):
    try:
        for i in range(1, num_copies + 1):
            # Generate a new filename
            new_filename = f"{file_path.stem}_copy{i}{file_path.suffix}"
            destination_path = destination_folder / new_filename
            # Copy the file to the destination folder
            shutil.copy2(file_path, destination_path)
            logger.info(f"Copied {file_path} to {destination_path}")
    except Exception as e:
        logger.error(f"Failed to copy {file_path}: {e}")

# Function to process PDFs in parallel
def process_pdfs():
    # Gather all the PDF files
    pdf_files = [file for file in source_folder.iterdir() if file.suffix.lower() == ".pdf"]

    # Use ThreadPoolExecutor for parallel copying
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(copy_file, pdf_file, num_copies): pdf_file for pdf_file in pdf_files}
        for future in as_completed(futures):
            future.result()  # Ensure any exceptions are raised

if __name__ == "__main__":
    logger.info("Starting PDF copy process...")
    process_pdfs()
    logger.info("All copies have been created.")
