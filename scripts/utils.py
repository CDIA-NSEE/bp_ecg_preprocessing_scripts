import os
import shutil
import logging
import re
import tempfile
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Precompile regex patterns for better performance
DATE_PATTERN = re.compile(r"Data:\s*(\d{2}/\d{2}/\d{4})")
TIME_PATTERN = re.compile(r"Hora:\s*(\d{2}:\d{2})")
SEX_PATTERN = re.compile(r"Sexo:\s*(\w+)")
BIRTH_PATTERN = re.compile(r"Data de Nascimento:\s*(\d{2}/\d{2}/\d{4})")
REPORT_PATTERN = re.compile(r"Laudo(.*?)Eletrocardiográficos - 2022", re.DOTALL)


def move_to_folder(file_path: Path, destination_folder: Path):
    """Moves a file to the specified folder, creating it if necessary."""
    try:
        destination_folder.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file_path), str(destination_folder / file_path.name))
        logger.warning(f"Moved {file_path.name} to {destination_folder}")
    except Exception as e:
        logger.error(f"Failed to move {file_path.name}: {e}")


def process_pdf(input_path: Path, boxes: dict, error_folder: Path) -> list:
    """Processes a single PDF to extract images based on bounding boxes."""
    saved_files = []
    logger.info(f"Processing PDF: {input_path.name}")

    try:
        pdf = fitz.open(input_path)
        if len(pdf) != 2:
            logger.warning(f"Skipping {input_path.name}: does not have 2 pages.")
            move_to_folder(input_path, error_folder)
            return []

        for cut_type, config in boxes.items():
            output_folder = Path(config["output_folder"])
            output_folder.mkdir(parents=True, exist_ok=True)

            output_name = f"{input_path.stem}_{cut_type}.png"
            output_path = output_folder / output_name
            page_number = config["page_number"]
            crop_box = config["crop_box"]

            page = pdf[page_number]
            image_list = page.get_images(full=True)

            if cut_type.lower() == "ecg" and image_list:
                # Extract and save the image
                xref = image_list[0][0]
                base_image = pdf.extract_image(xref)
                raw_image_bytes = base_image["image"]
                image_format = base_image["ext"]

                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{image_format}") as temp_file:
                    temp_filepath = Path(temp_file.name)
                    temp_file.write(raw_image_bytes)

                try:
                    with Image.open(temp_filepath) as img:
                        x1, y1, x2, y2 = crop_box
                        img.crop((x1, y1, x2, y2)).save(output_path)
                        saved_files.append(str(output_path))
                finally:
                    temp_filepath.unlink()

            else:
                # Scale up the image and crop
                scale_factor = 3
                matrix = fitz.Matrix(scale_factor, scale_factor)
                pix = page.get_pixmap(matrix=matrix)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                x1, y1, x2, y2 = [int(i * scale_factor) for i in crop_box]
                img.crop((x1, y1, x2, y2)).save(output_path)
                saved_files.append(str(output_path))

        pdf.close()
        logger.info(f"Successfully processed: {input_path.name}")
        return saved_files

    except Exception as e:
        logger.exception(f"Error processing {input_path.name}: {e}")
        move_to_folder(input_path, error_folder)
        return []


def extract_pdf_slices(input_folder: Path, boxes: dict, error_folder: Path):
    """Processes all PDFs in the input folder sequentially."""
    if not input_folder.exists():
        raise ValueError(f"Input folder '{input_folder}' does not exist.")

    pdf_files = list(input_folder.glob("*.pdf"))
    logger.info(f"Starting processing for {len(pdf_files)} files...")

    for input_path in pdf_files:
        process_pdf(input_path, boxes, error_folder)

    logger.info("Completed processing all files.")


def extract_information(pdf_path: Path, problems_folder: Path) -> list | None:
    """Extracts textual information from the first page of the PDF."""
    logger.info(f"Extracting text from: {pdf_path.name}")

    try:
        doc = fitz.open(pdf_path)
        if len(doc) < 2:
            logger.warning(f"{pdf_path.name} has only {len(doc)} page(s). Moving to problems folder.")
            move_to_folder(pdf_path, problems_folder)
            return None

        text = doc[0].get_text()

        extracted_data = [
            pdf_path.stem,
            DATE_PATTERN.search(text).group(1) if DATE_PATTERN.search(text) else None,
            TIME_PATTERN.search(text).group(1) if TIME_PATTERN.search(text) else None,
            SEX_PATTERN.search(text).group(1) if SEX_PATTERN.search(text) else None,
            BIRTH_PATTERN.search(text).group(1) if BIRTH_PATTERN.search(text) else None,
            REPORT_PATTERN.search(text).group(1).strip() if REPORT_PATTERN.search(text) else None,
        ]

        logger.info(f"Extracted data from {pdf_path.name}: {extracted_data}")
        return extracted_data

    except Exception as e:
        logger.exception(f"Error extracting data from {pdf_path.name}: {e}")
        move_to_folder(pdf_path, problems_folder)
        return None
