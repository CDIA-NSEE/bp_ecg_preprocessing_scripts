from utils import resize_images_in_folder

# Arguments
input_folder = "Processed Images"
output_folder = "Reduced Images"
new_height = 512

resize_images_in_folder(input_folder, output_folder, new_height)
