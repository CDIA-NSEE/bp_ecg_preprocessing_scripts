from utils import extract_pdf_slices_sequential

# Bounding box configurations
boxes = {
        'ecg': {'output_folder': 'ECG', 'page_number': 1, 'crop_box': (230, 680, 6790, 4432)},
        'report': {'output_folder': 'Report', 'page_number': 0, 'crop_box': (19, 350, 364, 600)},
        'birthday': {'output_folder': 'Birthday', 'page_number': 0, 'crop_box': (98, 196, 142, 204)},
        'gender': {'output_folder': 'Gender', 'page_number': 0, 'crop_box': (323, 196, 364, 204)},
        'date': {'output_folder': 'Date', 'page_number': 0, 'crop_box': (323, 243, 365, 251)},
        'hour': {'output_folder': 'Hour', 'page_number': 0, 'crop_box': (323, 255, 346, 263)},
        'speed': {'output_folder': 'Speed', 'page_number': 1, 'crop_box': (562, 662, 572, 671)},
        'amplitude': {'output_folder': 'Speed', 'page_number': 1, 'crop_box': (562, 565, 572, 576)}
}

# Input folder containing PDFs
input_folder = "Exams"

# Folder for PDFs with an invalid number of pages
error_folder = "ErrorFiles"

# Start processing
extract_pdf_slices_sequential(input_folder, boxes, error_folder)