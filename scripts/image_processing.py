import cv2
import numpy as np
import glob
import os

# Input and output directories
input_folder = "ECG"
output_folder = "Processed Images"

# Create the output folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Get all PNG files in the input folder
image_paths = glob.glob(os.path.join(input_folder, "*.png"))

for img_path in image_paths:
    # Read the image
    image = cv2.imread(img_path)
    if image is None:
        continue  # skip if the image can't be read

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold the image
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Detect horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 1))
    detected_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=5)

    # Detect vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 30))
    detected_vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=5)

    # Combine horizontal and vertical lines
    grid_mask = cv2.add(detected_lines, detected_vertical_lines)

    # Inpaint the image to remove grid
    inpainted_image = cv2.inpaint(image, grid_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

    # Construct output file path
    filename = os.path.basename(img_path)  # e.g., "carlosfelix_copy2_ecg.png"
    base_name, ext = os.path.splitext(filename)  # Split into base name and extension

    # Remove "_ecg" if it exists and append "_processed"
    base_name = base_name.replace("_ecg", "")  # Remove "_ecg" from the base name
    processed_filename = f"{base_name}_processed{ext}"  # Add "_processed" before extension
    output_path = os.path.join(output_folder, processed_filename)

    # Save the processed image
    cv2.imwrite(output_path, inpainted_image)

    print(f"Processed and saved: {output_path}")