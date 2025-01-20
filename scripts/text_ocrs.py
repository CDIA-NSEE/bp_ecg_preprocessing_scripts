import os
import sys
import logging
from pathlib import Path
from PIL import Image
import pytesseract
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def perform_ocr(image_path: Path, lang: str) -> dict:
    """Performs OCR on a single image and returns the extracted text."""
    try:
        with Image.open(image_path) as image:
            # Convert to grayscale for faster OCR
            gray_image = image.convert("L")
            text = pytesseract.image_to_string(
                gray_image, 
                lang=lang,
                config="--psm 6"  # Assume a single uniform block of text
            )
            # Extract base file name without the last underscore-separated part
            original_name = image_path.stem
            base_name = "_".join(original_name.split("_")[:-1]) if "_" in original_name else original_name
            return {"file_name": base_name, "ocr_text": text}
    except Exception as e:
        logging.error(f"Error processing image {image_path}: {e}")
        return {"file_name": image_path.stem, "ocr_text": ""}

def save_results_to_csv(results: list, csv_path: str):
    """Saves OCR results to the CSV file."""
    pd.DataFrame(results).to_csv(csv_path, mode="a", header=not os.path.exists(csv_path), index=False)

def main(image_folder_path: str, batch_size: int):
    """Main function to process OCR on images and save results to a CSV."""
    # Define constants and paths
    lang = "por"  # Language code for Portuguese in Tesseract
    ocr_folder = "OCRs"
    csv_path = os.path.join(ocr_folder, f"{Path(image_folder_path).name}_ocr.csv")

    # Ensure the OCRs folder exists
    os.makedirs(ocr_folder, exist_ok=True)

    # Get the list of image paths
    image_paths = list(Path(image_folder_path).glob("*.png"))  # Adjust extension if necessary
    if not image_paths:
        logging.warning(f"No images found in folder: {image_folder_path}")
        return

    # Process images in parallel
    logging.info(f"Processing {len(image_paths)} images using {batch_size} threads...")

    results = []
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        for i, result in enumerate(executor.map(lambda p: perform_ocr(p, lang), image_paths), start=1):
            results.append(result)
            if i % batch_size == 0 or i == len(image_paths):
                save_results_to_csv(results, csv_path)
                results.clear()  # Clear buffer to save memory
                logging.info(f"Saved batch {i // batch_size} to CSV.")

    # Save any remaining results
    if results:
        save_results_to_csv(results, csv_path)

    logging.info(f"OCR results saved to {csv_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        logging.error("Usage: python script.py <image_folder_path> <batch_size>")
        sys.exit(1)

    image_folder = sys.argv[1]
    try:
        batch_size = int(sys.argv[2])
    except ValueError:
        logging.error("Batch size must be an integer.")
        sys.exit(1)

    main(image_folder, batch_size)
