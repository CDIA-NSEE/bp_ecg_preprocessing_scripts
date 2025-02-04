import os
import hashlib
import pandas as pd

# Define the folder containing PDFs
pdf_folder = "Exams"
output_folder = "Exams_anonymized"
mapping_file = os.path.join(pdf_folder, "file_mapping.csv")  # Save mapping inside Exams folder

# Create a folder for anonymized PDFs
os.makedirs(output_folder, exist_ok=True)

# Store the mapping
mapping = []

# Iterate through PDFs
for filename in os.listdir(pdf_folder):
    if filename.endswith(".pdf"):
        original_path = os.path.join(pdf_folder, filename)
        
        # Create a hash-based anonymous name
        hash_name = hashlib.sha256(filename.encode()).hexdigest()[:10] + ".pdf"
        anonymized_path = os.path.join(output_folder, hash_name)
        
        # Copy the file instead of renaming
        with open(original_path, 'rb') as src_file:
            with open(anonymized_path, 'wb') as dest_file:
                dest_file.write(src_file.read())
        
        # Store mapping
        mapping.append([filename, hash_name])

# Save the mapping to a CSV file inside Exams folder
df = pd.DataFrame(mapping, columns=["Original Filename", "Anonymized Filename"])
df.to_csv(mapping_file, index=False)

print(f"Renaming complete. Mapping saved to {mapping_file}")

# Inform the user that deletion of original files is optional
print("Original files have been preserved. Delete them manually after verification if necessary.")
