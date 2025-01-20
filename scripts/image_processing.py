import cv2
import numpy as np
import glob
import os
from pathlib import Path
import logging
from concurrent.futures import ProcessPoolExecutor

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Input and output directories
input_folder = "ECG"
output_folder = "Processed Images"

# Create the output folder if it doesn't exist
Path(output_folder).mkdir(parents=True, exist_ok=True)

# Get all PNG files in the input folder
image_paths = glob.glob(os.path.join(input_folder, "*.png"))

def process_image(img_path):
    """Process a single image and remove the grid."""
    try:
        # Read the image
        image = cv2.imread(img_path)
        if image is None:
            logger.warning(f"Could not read image: {img_path}")
            return

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Threshold the image
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Detect horizontal and vertical lines in one combined step
        kernel_size = 30
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_size))
        
        # Apply morphological operations in parallel (two lines can be detected concurrently)
        detected_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=3)
        detected_vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=3)

        # Combine horizontal and vertical lines
        grid_mask = cv2.add(detected_lines, detected_vertical_lines)

        # Inpaint the image to remove grid
        inpainted_image = cv2.inpaint(image, grid_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

        # Construct output file path
        filename = Path(img_path).name  # Get the filename with extension
        base_name, ext = filename.rsplit('.', 1)  # Split into base name and extension

        # Remove "_ecg" if it exists and append "_processed"
        base_name = base_name.replace("_ecg", "")
        processed_filename = f"{base_name}_processed.{ext}"

        output_path = Path(output_folder) / processed_filename

        # Save the processed image
        cv2.imwrite(str(output_path), inpainted_image)
        logger.info(f"Processed and saved: {output_path}")

    except Exception as e:
        logger.error(f"Error processing {img_path}: {e}")

def process_images_concurrently(image_paths, batch_size=10):
    """Process images in batches concurrently using ProcessPoolExecutor."""
    with ProcessPoolExecutor(max_workers=batch_size) as executor:
        executor.map(process_image, image_paths)

if __name__ == "__main__":
    if not image_paths:
        logger.warning("No images found in the input folder.")
    else:
        logger.info(f"Processing {len(image_paths)} images...")
        process_images_concurrently(image_paths)
