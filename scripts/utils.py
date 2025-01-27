from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import shutil
import re
import tempfile
import os

def process_pdf(input_path, boxes, error_folder):
    """Processes a single PDF to extract text and crop images."""
    saved_files = []
    input_path = Path(input_path)
    error_folder = Path(error_folder)

    pdf = fitz.open(input_path)
    if len(pdf) != 2:
        print(f"Skipping {input_path.name}: does not have 2 pages.")
        error_folder.mkdir(parents=True, exist_ok=True)
        shutil.move(str(input_path), str(error_folder / input_path.name))
        return []

    for cut_type, config in boxes.items():
        output_folder = Path(config['output_folder'])
        output_folder.mkdir(parents=True, exist_ok=True)

        output_name = f"{input_path.stem}_{cut_type}.png"
        output_path = output_folder / output_name
        page_number = config['page_number']
        crop_box = config['crop_box']

        page = pdf[page_number]
        image_list = page.get_images(full=True)

        if cut_type.lower() == 'ecg' and image_list:
            xref = image_list[0][0]
            base_image = pdf.extract_image(xref)
            raw_image_bytes = base_image["image"]
            image_format = base_image["ext"]

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{image_format}") as temp_file:
                temp_filepath = temp_file.name
                temp_file.write(raw_image_bytes)

            try:
                with Image.open(temp_filepath) as img:
                    x1, y1, x2, y2 = crop_box
                    cropped_img = img.crop((x1, y1, x2, y2))
                    cropped_img.save(output_path)

                saved_files.append(str(output_path))
            finally:
                os.remove(temp_filepath)

        else:
            scale_factor = 3
            matrix = fitz.Matrix(scale_factor, scale_factor)
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            x1, y1, x2, y2 = [int(i * scale_factor) for i in crop_box]
            cropped_img = img.crop((x1, y1, x2, y2))
            cropped_img.save(output_path)
            saved_files.append(str(output_path))

    pdf.close()
    return saved_files


def extract_pdf_slices_sequential(input_folder, boxes, error_folder):
    """
    Processes all PDFs in the input folder sequentially.
    Moves PDFs with an invalid number of pages to an error folder.
    """
    input_folder = Path(input_folder)
    error_folder = Path(error_folder)

    if not input_folder.exists():
        raise ValueError("Input folder does not exist.")

    pdf_files = list(input_folder.glob("*.pdf"))
    print(f"Starting sequential processing for {len(pdf_files)} files...")

    for input_path in pdf_files:
        process_pdf(input_path, boxes, error_folder)

    print("Completed processing all files.")

# Function to extract information from a PDF
def extract_information(pdf_path, problems_folder):
    """Extract textual information from the first page of the PDF."""
    pdf_path = Path(pdf_path)
    problems_folder = Path(problems_folder)

    doc = fitz.open(pdf_path)
    if len(doc) < 2:
        print(f"Moving {pdf_path.name} to Problems folder (only {len(doc)} page(s))")
        
        problems_folder.mkdir(parents=True, exist_ok=True)
        shutil.move(str(pdf_path), str(problems_folder / pdf_path.name))
        return None

    text = doc[0].get_text()

    data_match = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", text)
    hora_match = re.search(r"Hora:\s*(\d{2}:\d{2})", text)
    sexo_match = re.search(r"Sexo:\s*(\w+)", text)
    nascimento_match = re.search(r"Data de Nascimento:\s*(\d{2}/\d{2}/\d{4})", text)
    laudo_match = re.search(r"Laudo(.*?)Eletrocardiográficos - 2022", text, re.DOTALL)

    extracted_data = [
        pdf_path.stem,
        data_match.group(1) if data_match else None,
        hora_match.group(1) if hora_match else None,
        sexo_match.group(1) if sexo_match else None,
        nascimento_match.group(1) if nascimento_match else None,
        laudo_match.group(1).strip() if laudo_match else None,
    ]

    return extracted_data
