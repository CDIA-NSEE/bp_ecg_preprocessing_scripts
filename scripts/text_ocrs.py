import os
import sys
from PIL import Image
from surya.ocr import run_ocr
from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
from surya.model.recognition.model import load_model as load_rec_model
from surya.model.recognition.processor import load_processor as load_rec_processor
from pathlib import Path
import pandas as pd

# Parse command-line arguments
IMAGE_FOLDER_PATH = sys.argv[1]  # This is the folder name, e.g., "Birthday"
BATCH_SIZE = int(sys.argv[2])

# Define the languages
langs = ["pt"]

# Load models and processors
det_processor, det_model = load_det_processor(), load_det_model()
rec_model, rec_processor = load_rec_model(), load_rec_processor()

# Get the list of images from the folder
image_paths = list(Path(IMAGE_FOLDER_PATH).glob("*.png"))  # Adjust extension if necessary

# Ensure the OCRs folder exists
OCR_FOLDER = "OCRs"
os.makedirs(OCR_FOLDER, exist_ok=True)

# Path to the CSV file inside the OCRs folder
csv_path = os.path.join(OCR_FOLDER, f"{IMAGE_FOLDER_PATH}_ocr.csv")

# Create the CSV file and write the header (only for the first time)
if not os.path.exists(csv_path):
    pd.DataFrame(columns=["file_name", IMAGE_FOLDER_PATH]).to_csv(csv_path, index=False)

# Process images in batches
for i in range(0, len(image_paths), BATCH_SIZE):
    batch_paths = image_paths[i:i + BATCH_SIZE]
    images = [Image.open(image_path) for image_path in batch_paths]

    # Run OCR for the current batch
    predictions = run_ocr(images, [langs] * len(images), det_model, det_processor, rec_model, rec_processor)

    # Prepare batch results
    rows = []
    for idx, page_predictions in enumerate(predictions):
        text = " ".join(line.text for line in page_predictions.text_lines)  # Concatenate all text lines

        # Get the base file name without extension
        original_name = batch_paths[idx].stem  # Example: "carlosfelix_copy24_hour"

        # Remove the last underscore-separated part (e.g., "carlosfelix_copy24_hour" → "carlosfelix_copy24")
        base_name = "_".join(original_name.split("_")[:-1]) if "_" in original_name else original_name

        rows.append({"file_name": base_name, IMAGE_FOLDER_PATH: text})

    # Append the batch results to the CSV
    pd.DataFrame(rows).to_csv(csv_path, mode='a', header=False, index=False)

    print(f"Processed batch {i // BATCH_SIZE + 1}/{(len(image_paths) + BATCH_SIZE - 1) // BATCH_SIZE}")

print(f"OCR results have been saved to {csv_path}.")
