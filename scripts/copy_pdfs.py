import os
import shutil

# Path to the folder containing original PDFs
source_folder = "Exams"
# Path to the destination folder
destination_folder = "Exams_Copies"

# Number of copies you want for each PDF
num_copies = 50

# Ensure the destination folder exists
os.makedirs(destination_folder, exist_ok=True)

# Iterate over each file in the source folder
for filename in os.listdir(source_folder):
    if filename.endswith(".PDF"):  # Only process PDF files
        source_path = os.path.join(source_folder, filename)
        # Create the specified number of copies
        for i in range(1, num_copies + 1):
            # Generate a new filename for each copy
            new_filename = f"{os.path.splitext(filename)[0]}_copy{i}.pdf"
            destination_path = os.path.join(destination_folder, new_filename)
            # Copy the file
            shutil.copy2(source_path, destination_path)
            print(f"Copied {source_path} to {destination_path}")

print("All copies have been created.")
