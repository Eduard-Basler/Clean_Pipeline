'''
This script is a lightweight utility that performs a spatial and volumetric crop on a 3D TIFF file.
It reads a 3D TIFF file using the tifffile library and determines its dimensions ($Z, Y, X$).
Volumetric Cropping ($Z$): It extracts exactly 50 slices, specifically from index 50 to 99 (the "middle-top" portion of the stack).
Spatial Cropping ($Y, X$): It identifies the center of the image and extracts a 50% window from both the width and height, maintaining the central focus of the frame.
Output: It saves the resulting cropped data as a new TIFF file into a specified output directory, preserving the original filename with a "cropped_" prefix.
Execution: It is designed to be run from the command line, accepting the input file path and the target output folder as arguments.

'''


import tifffile
import argparse
import os

def crop_tiff(input_path, output_folder):
    data = tifffile.imread(input_path)
    z, y, x = data.shape

    # Dimensions for Y and X (50% size)
    new_y, new_x = y // 2, x // 2

    # Calculate center for Y and X
    start_y = (y - new_y) // 2
    start_x = (x - new_x) // 2

    # Perform the crop: Slices 50-100, centered Y and X
    cropped_data = data[50:100, 
                        start_y:start_y + new_y, 
                        start_x:start_x + new_x]

    # Save
    output_path = os.path.join(output_folder, f"cropped_{os.path.basename(input_path)}")
    tifffile.imwrite(output_path, cropped_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    
    crop_tiff(args.input, args.output)