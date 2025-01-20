import os
import sys
import logging
import pandas as pd
import dask.dataframe as dd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def merge_csv_files(input_folder: str, output_file: str):
    """Merges all CSV files in the input folder into a single CSV file."""
    input_path = Path(input_folder)

    # Get list of all CSV files
    csv_files = list(input_path.glob("*.csv"))
    if not csv_files:
        logging.warning(f"No CSV files found in folder: {input_folder}")
        return

    logging.info(f"Found {len(csv_files)} CSV files in {input_folder}.")
    for csv_file in csv_files:
        logging.info(f"  - {csv_file.name}")

    # Use Dask for parallel processing
    merged_df = None
    for csv_file in csv_files:
        try:
            # Load the CSV file as a Dask DataFrame
            dask_df = dd.read_csv(csv_file)

            # Ensure "file_name" column exists
            if "file_name" not in dask_df.columns:
                logging.error(f"Missing 'file_name' column in {csv_file.name}. Skipping this file.")
                continue

            # Perform merge operation on 'file_name' column
            if merged_df is None:
                merged_df = dask_df
            else:
                merged_df = dd.merge(merged_df, dask_df, on="file_name", how="outer")

            logging.info(f"Merged {csv_file.name}.")
        except Exception as e:
            logging.error(f"Error reading {csv_file.name}: {e}")

    if merged_df is None:
        logging.warning("No valid CSV files were merged.")
        return

    # Convert Dask DataFrame to Pandas and save
    merged_df = merged_df.compute()  # Triggers computation and converts to Pandas DataFrame
    merged_df.to_csv(output_file, index=False)
    logging.info(f"Merged CSV saved to {output_file} ({merged_df.shape[0]} rows).")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logging.error("Usage: python merge_ocrs.py <input_folder> [output_file]")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "merged_ocr.csv"

    if not os.path.exists(input_folder):
        logging.error(f"Input folder does not exist: {input_folder}")
        sys.exit(1)

    merge_csv_files(input_folder, output_file)
