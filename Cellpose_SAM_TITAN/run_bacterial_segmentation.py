import os
import argparse
import numpy as np
import cupy as cp
from cupyx.scipy import ndimage as cu_ndimage
from skimage.measure import label
from skimage.filters import threshold_triangle
import tifffile

# Set up arguments
parser = argparse.ArgumentParser()
parser.add_argument("--image_path", type=str, required=True, help="Path to the single 3D TIFF image")
parser.add_argument("--output_dir", type=str, required=True, help="Folder to save the output label file")
args = parser.parse_args()

# Check if the input file actually exists
if not os.path.exists(args.image_path):
    raise FileNotFoundError(f"Input file not found at: {args.image_path}")

# Create the output directory if it doesn't exist
if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)
    print(f"Created output directory: {args.output_dir}")

print(f"Processing isolated bacterial stack: {os.path.basename(args.image_path)}")

# Read the 3D image stack
stack = tifffile.imread(args.image_path)

# GPU Processing (Median filter)
stack_gpu = cp.asarray(stack.astype(np.float32))
filtered_gpu = cu_ndimage.median_filter(stack_gpu, size=2)

# Pull back to CPU for Thresholding & Connected Components (Labeling)
filtered = cp.asnumpy(filtered_gpu)
threshold_value = threshold_triangle(filtered)
binary = filtered > threshold_value
label_image = label(binary, connectivity=1)

# Size filter thresholds (in voxels)
min_size = 900
max_size = 5000

sizes = np.bincount(label_image.ravel())
remove_mask = (sizes < min_size) | (sizes > max_size)
label_image[remove_mask[label_image]] = 0

# FIX 1: Convert to uint16 so Fiji can display it properly. 
# (Throws a warning if you somehow have more than 65,535 bacteria)
max_label = label_image.max()
if max_label > 65535:
    print(f"WARNING: Too many labels ({max_label}). Consider using a float32 type for Fiji.")
label_image = label_image.astype(np.uint16)



# Extract metadata from original TIFF
with tifffile.TiffFile(args.image_path) as tif:
    ome_metadata = tif.ome_metadata
    # description = tif.pages[0].description # Usually redundant if pulling ome_metadata

# Construct New Save Path
file_name = os.path.splitext(os.path.basename(args.image_path))[0] + "_labels.tif"
output_path = os.path.join(args.output_dir, file_name)

# FIX 2: Write with imagej=True and explicit ZYX axes.
tifffile.imwrite(
    output_path,
    label_image,
    imagej=True,                 # Forces Fiji/ImageJ compatibility
    metadata={'axes': 'ZYX'},    # Explicitly defines it as a Z-stack
    description=ome_metadata,    # OME XML string goes in description, not metadata!
    compression="zlib",
)

print(f"Saved labels to: {output_path}")