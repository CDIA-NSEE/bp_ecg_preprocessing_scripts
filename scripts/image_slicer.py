import os
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from utils import extract_pdf_slices_sequential
from pathlib import Path

# Configure logging for better monitoring
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Bounding box configurations
boxes = {
    'ecg': {'output_folder': 'ECG', 'page_number': 1, 'crop_box': (230, 680, 6790, 4432)},
    'report': {'output_folder': 'Report', 'page_number': 0, 'crop_box': (19, 350, 364, 600)},
    'birthday': {'output_folder': 'Birthday', 'page_number': 0, 'crop_box': (98, 196, 142, 204)},
    'gender': {'output_folder': 'Gender', 'page_number': 0, 'crop_box': (323, 196, 364, 204)},
    'date': {'output_folder': 'Date', 'page_number': 0, 'crop_box': (323, 243, 365, 251)},
    'hour': {'output_folder': 'Hour', 'page_number': 0, 'crop_box': (323, 255, 346, 263)},
    'speed': {'output_folder': 'Speed', 'page_number': 1, 'crop_box': (562, 662, 572, 671)},
    'amplitude': {'output_folder': 'Speed', 'page_number': 1, 'crop_box': (562, 565, 572, 576)}
}

# Input folder containing PDFs
input_folder = "Exams"

# Folder for PDFs with an invalid number of pages
error_folder = "ErrorFiles"

# Ensure that output folders exist
for config in boxes.values():
    os.makedirs(config["output_folder"], exist_ok=True)

# Function to process individual PDFs
def process_pdf(pdf_file):
    try:
        logging.info(f"Processing {os.path.basename(pdf_file)}...")
        extract_pdf_slices_sequential(pdf_file, boxes, error_folder)
        logging.info(f"Successfully processed {os.path.basename(pdf_file)}.")
    except Exception as e:
        logging.error(f"Error processing {os.path.basename(pdf_file)}: {e}")

# Function to process PDF files using multiprocessing
def process_pdfs_multiprocessing(input_folder):
    # Get list of all PDF files
    pdf_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith(".pdf")]
    if not pdf_files:
        logging.warning(f"No PDF files found in folder: {input_folder}")
        return

    # Use ProcessPoolExecutor for parallel processing (CPU-bound tasks)
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_pdf, pdf_file) for pdf_file in pdf_files]

        # Wait for all futures to complete and log results
        for future in as_completed(futures):
            try:
                future.result()  # Retrieve the result of the processed PDF
            except Exception as e:
                logging.error(f"Error during processing: {e}")

if __name__ == "__main__":
    # Start processing PDFs with multiprocessing
    process_pdfs_multiprocessing(input_folder)
    logging.info("All PDF processing completed.")
