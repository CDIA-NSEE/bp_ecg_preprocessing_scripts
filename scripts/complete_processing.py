import os
import csv
from utils import process_pdf, extract_information

# Define folders
EXAMS_FOLDER = "Exams"
PROBLEMS_FOLDER = "Problems"
OUTPUT_CSV = "extracted_data.csv"
ERROR_FOLDER = "Errors"

# Define bounding boxes for image extraction
BOXES = {
    "ecg": {"output_folder": "ECG_Images", "page_number": 1, "crop_box": (230, 680, 6790, 4432)},
    'speed': {'output_folder': 'Speed', 'page_number': 1, 'crop_box': (170, 563, 180, 570)},
    'amplitude': {'output_folder': 'Amplitude', 'page_number': 1, 'crop_box': (264, 563, 278, 570)}
}

# Ensure necessary folders exist
os.makedirs(PROBLEMS_FOLDER, exist_ok=True)
os.makedirs(ERROR_FOLDER, exist_ok=True)
for config in BOXES.values():
    os.makedirs(config['output_folder'], exist_ok=True)

# Create CSV file with header if it does not exist
if not os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["File", "Data", "Hora", "Sexo", "Data de Nascimento", "Laudo"])


# Process all PDFs
for pdf_file in os.listdir(EXAMS_FOLDER):
    if pdf_file.endswith(".pdf"):
        pdf_path = os.path.join(EXAMS_FOLDER, pdf_file)
        print(f"Processing: {pdf_file}")

        extracted_data = extract_information(pdf_path, PROBLEMS_FOLDER)
        image_files = process_pdf(pdf_path, BOXES, ERROR_FOLDER)

        if extracted_data:
            with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(extracted_data)

        os.remove(pdf_path)

print(f"Extraction complete. Data saved to {OUTPUT_CSV}")