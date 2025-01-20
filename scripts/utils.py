import os
import shutil
from PyPDF2 import PdfReader
from PIL import Image
from pdf2image import convert_from_path
import re
from typing import List, Dict, Any, Optional
from multiprocessing import Pool, cpu_count
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Precompile regex patterns for better performance
DATE_PATTERN = re.compile(r"Data:\s*(\d{2}/\d{2}/\d{4})")
TIME_PATTERN = re.compile(r"Hora:\s*(\d{2}:\d{2})")
SEX_PATTERN = re.compile(r"Sexo:\s*(\w+)")
BIRTH_PATTERN = re.compile(r"Data de Nascimento:\s*(\d{2}/\d{2}/\d{4})")
REPORT_PATTERN = re.compile(r"Laudo(.*?)Eletrocardiográficos - 2022", re.DOTALL)

def process_pdf(input_path: str, boxes: Dict[str, Dict[str, Any]], error_folder: str) -> List[str]:
    """Processes a single PDF to extract text and crop images."""
    saved_files = []
    try:
        reader = PdfReader(input_path)
        if len(reader.pages) != 2:
            raise ValueError(f"Invalid page count: {len(reader.pages)}")
    except Exception as e:
        logging.error(f"Error opening PDF {input_path}: {e}")
        shutil.move(input_path, os.path.join(error_folder, os.path.basename(input_path)))
        return []

    for cut_type, config in boxes.items():
        output_name = f"{os.path.splitext(os.path.basename(input_path))[0]}_{cut_type}.png"
        output_path = os.path.join(config["output_folder"], output_name)
        page_number = config["page_number"]
        crop_box = config["crop_box"]

        try:
            images = convert_from_path(
                input_path, first_page=page_number + 1, last_page=page_number + 1, dpi=150
            )
            if images:
                img = images[0]
                x1, y1, x2, y2 = crop_box
                img.crop((x1, y1, x2, y2)).save(output_path)
                saved_files.append(output_path)
        except Exception as e:
            logging.error(f"Error processing {cut_type} in {input_path}: {e}")

    return saved_files


def extract_pdf_slices_sequential(input_folder: str, boxes: Dict[str, Dict[str, Any]], error_folder: str):
    """Processes all PDFs in the input folder in parallel."""
    if not os.path.exists(input_folder):
        raise ValueError("Input folder does not exist.")

    for config in boxes.values():
        os.makedirs(config["output_folder"], exist_ok=True)

    pdf_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith(".pdf")]
    logging.info(f"Starting processing for {len(pdf_files)} files...")

    # Use multiprocessing to handle multiple PDFs in parallel
    with Pool(processes=min(cpu_count(), len(pdf_files))) as pool:
        pool.starmap(process_pdf, [(pdf, boxes, error_folder) for pdf in pdf_files])

    logging.info("Completed processing all files.")


def extract_information(pdf_path: str, problems_folder: str) -> Optional[List[str]]:
    """Extracts textual information from the first page of the PDF."""
    try:
        reader = PdfReader(pdf_path)
        if len(reader.pages) < 2:
            raise ValueError("PDF has fewer than 2 pages")
    except Exception as e:
        logging.error(f"Error opening PDF {pdf_path}: {e}")
        shutil.move(pdf_path, os.path.join(problems_folder, os.path.basename(pdf_path)))
        return None

    text = reader.pages[0].extract_text()

    # Perform regex searches with proper checks
    date_match = DATE_PATTERN.search(text)
    time_match = TIME_PATTERN.search(text)
    sex_match = SEX_PATTERN.search(text)
    birth_match = BIRTH_PATTERN.search(text)
    report_match = REPORT_PATTERN.search(text)

    extracted_data = [
        os.path.splitext(os.path.basename(pdf_path))[0],
        date_match.group(1) if date_match else None,
        time_match.group(1) if time_match else None,
        sex_match.group(1) if sex_match else None,
        birth_match.group(1) if birth_match else None,
        report_match.group(1).strip() if report_match else None,
    ]

    return extracted_data
