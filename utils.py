import os
import fitz  # PyMuPDF
from PIL import Image
import shutil
import re
import tempfile

def process_pdf(input_path, boxes, ERROR_FOLDER):
    """Processes a single PDF to extract text and crop images."""
    saved_files = []
    pdf = fitz.open(input_path)
    if len(pdf) != 2:
        print(f"Skipping {os.path.basename(input_path)}: does not have 2 pages.")
        shutil.move(input_path, os.path.join(ERROR_FOLDER, os.path.basename(input_path)))
        return []

    for cut_type, config in boxes.items():
        output_name = os.path.splitext(os.path.basename(input_path))[0] + '_' + cut_type + '.png'
        output_path = os.path.join(config['output_folder'], output_name)
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

            with Image.open(temp_filepath) as img:
                x1, y1, x2, y2 = crop_box
                cropped_img = img.crop((x1, y1, x2, y2))
                cropped_img.save(output_path)

            os.remove(temp_filepath)
            saved_files.append(output_path)
        else:
            scale_factor = 3
            matrix = fitz.Matrix(scale_factor, scale_factor)
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            x1, y1, x2, y2 = [int(i * scale_factor) for i in crop_box]
            cropped_img = img.crop((x1, y1, x2, y2))
            cropped_img.save(output_path)
            saved_files.append(output_path)

    pdf.close()
    return saved_files

def extract_pdf_slices_sequential(input_folder, boxes, error_folder):
    """
    Processes all PDFs in the input folder sequentially.
    Moves PDFs with an invalid number of pages to an error folder.
    """
    if not os.path.exists(input_folder):
        raise ValueError("Input folder does not exist.")

    for config in boxes.values():
        if not os.path.exists(config['output_folder']):
            os.makedirs(config['output_folder'])

    pdf_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith('.pdf')]

    print(f"Starting sequential processing for {len(pdf_files)} files...")

    for input_path in pdf_files:
        process_pdf(input_path, boxes, error_folder)

    print("Completed processing all files.")

# Function to extract information from a PDF
def extract_information(pdf_path, PROBLEMS_FOLDER):
    """Extract textual information from the first page of the PDF."""
    doc = fitz.open(pdf_path)
    if len(doc) < 2:
        print(f"Moving {pdf_path} to Problems folder (only {len(doc)} page(s))")
        shutil.move(pdf_path, os.path.join(PROBLEMS_FOLDER, os.path.basename(pdf_path)))
        return None

    text = doc[0].get_text()

    data_match = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", text)
    hora_match = re.search(r"Hora:\s*(\d{2}:\d{2})", text)
    sexo_match = re.search(r"Sexo:\s*(\w+)", text)
    nascimento_match = re.search(r"Data de Nascimento:\s*(\d{2}/\d{2}/\d{4})", text)
    laudo_match = re.search(r"Laudo(.*?)Eletrocardiográficos - 2022", text, re.DOTALL)

    extracted_data = [
        os.path.splitext(os.path.basename(pdf_path))[0],
        data_match.group(1) if data_match else None,
        hora_match.group(1) if hora_match else None,
        sexo_match.group(1) if sexo_match else None,
        nascimento_match.group(1) if nascimento_match else None,
        laudo_match.group(1).strip() if laudo_match else None,
    ]

    return extracted_data