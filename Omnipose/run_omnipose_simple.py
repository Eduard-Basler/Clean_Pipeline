import sys
import os
import tifffile
import numpy as np
from cellpose_omni import models, core

def main():
    # 1. Inputs
    img_path = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    # 2. Load the 3D volume
    print(f"Loading image: {img_path}")
    img = tifffile.imread(img_path)  # Shape: [Z, Y, X]

    # 3. Setup GPU & Model
    use_gpu = core.use_gpu()
    model = models.CellposeModel(gpu=use_gpu, model_type='bact_fluor_omni')

    # 4. Unroll to list & let Omnipose natively handle the 3D stitching
    print("Running native Omnipose 3D-stitched segmentation...")
    
    # We pass it as a list of 2D images to avoid the 32-bit index math crash.
    # The 'stitch_threshold' parameter natively connects the masks together into 3D.
    masks, flows, styles = model.eval(
        x=[slice_2d for slice_2d in img],  
        channels=[0, 0],
        diameter=6.0,
        mask_threshold=-3.16,
        flow_threshold=0.4,
        omni=True,                 
        do_3D=False,               
        affinity_seg=True,         
        cluster=True,              
        batch_size=8,             # Keeps your memory perfectly stable
        stitch_threshold=0.90      # NATIVE OMNIPOSE 3D STITCHER
    )

    # Convert the resulting list back into a clean 3D NumPy block
    final_masks = np.stack(masks, axis=0).astype(np.int32)

    # 5. Simple, standard edge removal
    print("Removing edge-touching cells...")
    edge_ids = np.unique([
        final_masks[0,:,:], final_masks[-1,:,:],   # Top/Bottom Z planes
        final_masks[:,0,:], final_masks[:,-1,:],   # Border Y edges
        final_masks[:,:,0], final_masks[:,:,-1]    # Border X edges
    ])
    edge_ids = edge_ids[edge_ids > 0]  # Ignore background
    final_masks[np.isin(final_masks, edge_ids)] = 0

    # 6. Save the output
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    out_file = os.path.join(out_dir, f"{base_name}_masks.tif")
    
    tifffile.imwrite(out_file, final_masks)
    print(f"Saved completed 3D masks to: {out_file}")

if __name__ == "__main__":
    main()