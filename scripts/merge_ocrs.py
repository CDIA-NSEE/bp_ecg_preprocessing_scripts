import os
import pandas as pd
from pathlib import Path

# Define the OCRs folder
OCR_FOLDER = "OCRs"

# Get a list of all CSV files in the OCRs folder
csv_files = list(Path(OCR_FOLDER).glob("*.csv"))

# Ensure there are CSV files to merge
if not csv_files:
    print("No CSV files found in the OCRs folder.")
    exit()

# Print the number of rows in each file before merging
print("Number of rows in each CSV file:")
for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    print(f"{csv_file.name}: {df.shape[0]} rows")

# Initialize merged DataFrame
merged_df = None

# Iterate over each CSV file and merge based on "file_name"
for csv_file in csv_files:
    df = pd.read_csv(csv_file)  # Read file without changing column names
    
    if merged_df is None:
        merged_df = df  # First file initializes the DataFrame
    else:
        merged_df = pd.merge(merged_df, df, on="file_name", how="outer")

# Save the merged DataFrame in the main folder
merged_csv_path = "merged_ocr.csv"
merged_df.to_csv(merged_csv_path, index=False)

print(f"\nAll OCR results have been merged into {merged_csv_path}.")
