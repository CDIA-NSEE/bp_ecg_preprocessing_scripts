import os
import fitz
import uuid
from PIL import Image
import shutil
import re
import tempfile

import os
import shutil
import uuid
import fitz  # PyMuPDF
from PIL import Image
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

def resize_images_in_folder(input_folder, output_folder, new_height):
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Get a list of all files in the input folder
    image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not image_files:
        print("No image files found in the input folder.")
        return

    # Use the first image to calculate proportions
    first_image_path = os.path.join(input_folder, image_files[0])
    img = Image.open(first_image_path)
    width, height = img.size
    prop = width / height

    # Calculate new width while preserving aspect ratio
    new_width = int(new_height * prop)

    print(f"Original Width: {width} pixels")
    print(f"Original Height: {height} pixels")
    print(f"Aspect Ratio (Width/Height): {prop:.2f}")
    print(f"New Dimensions: {new_width}x{new_height}")

    # Process each image
    for image_file in image_files:
        input_path = os.path.join(input_folder, image_file)

        # Construct the output filename by replacing "processed" with "reduced"
        base_name, ext = os.path.splitext(image_file)
        if "_processed" in base_name:
            base_name = base_name.replace("_processed", "")  # Remove "_processed"
        output_file_name = f"{base_name}_reduced{ext}"  # Add "_reduced"
        output_path = os.path.join(output_folder, output_file_name)

        # Open the image
        img = Image.open(input_path)

        # Resize the image
        resized_img = img.resize((new_width, new_height))

        # Save the resized image to the output folder
        resized_img.save(output_path)
        print(f"Resized and saved: {output_path}")

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