import os
import hashlib
import pandas as pd

# Define the folder containing PDFs
pdf_folder = "Exams"
output_folder = "Exams_anonymized"
mapping_file = "file_mapping.csv"

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
        
        # Rename and move the file
        os.rename(original_path, anonymized_path)
        
        # Store mapping
        mapping.append([filename, hash_name])

# Save the mapping to a CSV file
df = pd.DataFrame(mapping, columns=["Original Filename", "Anonymized Filename"])
df.to_csv(mapping_file, index=False)

print(f"Renaming complete. Mapping saved to {mapping_file}")
