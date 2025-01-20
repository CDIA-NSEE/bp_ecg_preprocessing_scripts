import os
from pathlib import Path
from PIL import Image
import asyncio
import logging

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Function to resize images
def resize_image(input_path, output_path, new_width, new_height):
    """Resize a single image and save it."""
    try:
        with Image.open(input_path) as img:
            img.thumbnail((new_width, new_height), Image.ANTIALIAS) # type: ignore
            img.save(output_path)
            logger.info(f"Resized and saved: {output_path}")
    except Exception as e:
        logger.error(f"Error processing {input_path}: {e}")

# Helper function to process a batch of images asynchronously
async def process_batch(batch, input_folder, output_folder, new_width, new_height):
    """Process a batch of images asynchronously."""
    tasks = []
    for image_file in batch:
        input_path = os.path.join(input_folder, image_file)

        # Construct the output filename
        base_name, ext = os.path.splitext(image_file)
        if "_processed" in base_name:
            base_name = base_name.replace("_processed", "")  # Remove "_processed"
        output_file_name = f"{base_name}_reduced{ext}"  # Add "_reduced"
        output_path = os.path.join(output_folder, output_file_name)

        # Add resize task to the asyncio event loop
        tasks.append(asyncio.to_thread(resize_image, input_path, output_path, new_width, new_height))

    # Wait for all tasks in this batch to finish
    await asyncio.gather(*tasks)

# Main function for resizing images
async def resize_images_in_folder(input_folder, output_folder, new_height):
    """Resize all images in the folder to a new height while preserving the aspect ratio."""
    os.makedirs(output_folder, exist_ok=True)

    image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if not image_files:
        logger.warning("No image files found in the input folder.")
        return

    # Use the first image to calculate proportions
    first_image_path = os.path.join(input_folder, image_files[0])
    with Image.open(first_image_path) as img:
        width, height = img.size
        prop = width / height

    # Calculate new width while preserving aspect ratio
    new_width = int(new_height * prop)

    logger.info(f"Original Width: {width} pixels")
    logger.info(f"Original Height: {height} pixels")
    logger.info(f"Aspect Ratio (Width/Height): {prop:.2f}")
    logger.info(f"New Dimensions: {new_width}x{new_height}")

    # Process images in batches using asyncio
    batch_size = 10  # You can tweak this depending on memory usage and performance needs
    batches = [image_files[i:i + batch_size] for i in range(0, len(image_files), batch_size)]

    # Process all batches concurrently
    tasks = [process_batch(batch, input_folder, output_folder, new_width, new_height) for batch in batches]
    await asyncio.gather(*tasks)

    logger.info("Image resizing completed.")

def main():
    """Main function to trigger image resizing."""
    input_folder = "Processed Images"
    output_folder = "Reduced Images"
    new_height = 512

    # Run the asynchronous image resizing process
    asyncio.run(resize_images_in_folder(input_folder, output_folder, new_height))

# Check if the script is executed directly
if __name__ == "__main__":
    main()
