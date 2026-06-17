import os
os.environ["XLA_FLAGS"] = "--xla_gpu_cuda_data_dir=/home/basler0004/Pipeline_Final/Stardist/.pixi/envs/default"

import numpy as np
import tifffile
from merge_stardist_masks.model_3d import StarDist3D

# Import StarDist's official robust normalizer
from csbdeep.utils import normalize 

def run_author_3d_pipeline(image_path):
    print(f"--- Loading 3D Volume: {image_path} ---")
    img_3d = tifffile.imread(image_path)
    print(f"Loaded volume shape: {img_3d.shape} (Z, Y, X)")
    
    print("--- Normalizing 3D Volume (Percentile) ---")
    # This scales the contrast based on the 1st and 99.8th percentiles, 
    # completely ignoring extreme sensor noise and bringing the bacteria to light.
    img_normalized = normalize(img_3d, 1, 99.8, axis=(0,1,2))

    print("\n--- Initializing the Wrapped 3D Model ---")
    model = StarDist3D(None, name='stardist-opp-12', basedir='.')

    print("\n--- Running Optimized 3D Prediction ---")
    fused_labels, details = model.predict_instances(
        img_normalized, 
        n_tiles=(2, 4, 4),
        prob_thresh=0.15,   # LOWERED: Tells the model to accept fainter cells
        nms_thresh=0.5      # RAISED: Allows tight clusters to touch without deleting them
    )
    
    num_cells = np.max(fused_labels)
    print(f"3D Segmentation complete! Found {num_cells} distinct objects.")

    print("\n--- Saving 3D Results ---")
    output_filename = "fused_3d_masks.tif"
    tifffile.imwrite(output_filename, fused_labels)
    print(f"Saved optimized 3D masks to '{output_filename}'.")

if __name__ == "__main__":
    test_3d_image_path = "CLEAN_20251212_transwell_sATA1946_sATA2044_16hPI_60xOIL_rep2_006_s1_c3-1.tif" 
    run_author_3d_pipeline(test_3d_image_path)