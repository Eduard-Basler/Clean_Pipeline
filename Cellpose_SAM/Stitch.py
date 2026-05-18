import os
import glob
import numpy as np
import tifffile
from cellpose.utils import stitch_3d

# 1. Path setup
mask_folder = "/home/basler0004/Pipeline_Final/Temp_Prediction_Cellpose/Debug"
output_path = "/home/basler0004/Pipeline_Final/Temp_Prediction_Cellpose/Debug/Result/stitched_volume.tif"

# 2. Load and sort mask files (ensuring correct Z-order)
mask_files = sorted(glob.glob(os.path.join(mask_folder, "*.png")))  # Change extension if needed
if not mask_files:
    raise FileNotFoundError("No mask files found in the specified directory.")

print(f"Found {len(mask_files)} mask planes. Stacking...")
masks_2d = [tifffile.imread(f) if f.endswith(('.tif', '.tiff')) else np.array(tifffile.Image.open(f)) for f in mask_files]

# Stack into an [N_planes x Y x X] numpy array
masks_3d = np.stack(masks_2d, axis=0)

# 3. Apply Cellpose stitching logic
# stitch_threshold: IoU threshold (0.5 is a standard starting point)
stitch_thresh = 0.5 
print(f"Stitching masks with a threshold of {stitch_thresh}...")
stitched_masks = stitch_3d(masks_3d, stitch_threshold=stitch_thresh)

# 4. Save the stitched 3D volume
tifffile.imwrite(output_path, stitched_masks.astype(np.int32))
print(f"Successfully saved stitched 3D masks to: {output_path}")
