import os
import glob
import torch
import numpy as np
from tifffile import imread, imwrite
from cellpose_omni import models, core
import sys

# ==========================================
# 1. CONFIGURATION
# ==========================================
INPUT_DIR = sys.argv[1]
OUTPUT_DIR = sys.argv[2]
os.makedirs(os.path.join(OUTPUT_DIR, "bacteria_masks"), exist_ok=True)

BACT_CH_IDX = 2 
Z_ANISOTROPY = 1.8


# ==========================================
# 2. INITIALIZE MODEL
# ==========================================
use_GPU = core.use_gpu()
print("Loading Bacteria Model (bact_fluor_omni)...")
model_bact = models.CellposeModel(
    gpu=use_GPU, 
    model_type='bact_fluor_omni', 
    dim=2, 
    nclasses=3, 
    nchan=2
)

# ==========================================
# 3. PROCESSING LOOP
# ==========================================
files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.tif*")))

for filepath in files:
    filename = os.path.basename(filepath)
    print(f"\n🚀 Processing: {filename}")
    
    img_4d = imread(filepath)
    if img_4d.ndim == 4 and img_4d.shape[1] < 10:  
        # Ensure it's a float for division during normalization
        img_bact = img_4d[:, BACT_CH_IDX, :, :].astype(np.float32)
    else:
        continue

    # --- CRITICAL: Global Normalization ---
    # Since normalize=False in eval(), we must scale the data to 0-1 here.
    print("   -> Performing Global Normalization...")
    p1 = np.percentile(img_bact, 1)
    p99 = np.percentile(img_bact, 99)
    # Add a tiny epsilon (1e-8) to prevent division by zero
    img_bact = np.clip((img_bact - p1) / (p99 - p1 + 1e-8), 0, 1)

    # --- B. Segment Bacteria (2D Stitching Mode) ---
    print("   -> Segmenting Bacteria (2D Stitching)...")
    
    masks_bact, flows_bact, _ = model_bact.eval(
        img_bact,
        channels=[0,0],       
        
        # --- THE MAGIC SWITCH ---
        do_3D=False,           # Turn OFF true 3D memory-hogging math
        stitch_threshold=0.2,  # Turn ON 2D stitching. (0.5 means 50% overlap required to stitch)
        
        omni=True,
        diameter=10,            
        cluster=True,         
        mask_threshold=1.2,
        net_avg=False,        
        verbose=False,
	niter=200,
        
        # We can turn tile back to False to speed up 2D processing!
        # A single 2720x2720 2D slice easily fits in 12GB VRAM.
        tile=True,
	tile_overlap=0.1,
        normalize=False       # (Keep your global normalization step from earlier)
    )
    
    # Save output
    bact_out_path = os.path.join(OUTPUT_DIR, "bacteria_masks", f"{filename.split('.')[0]}_bact_mask.tif")
    imwrite(bact_out_path, masks_bact, compression='zlib')
    
    print(f"   ✅ Saved Masks: {len(np.unique(masks_bact)) - 1} cells found.")
    
    del masks_bact, flows_bact, img_4d, img_bact
    torch.cuda.empty_cache()

print("\n🎉 ALL PROCESSING COMPLETE!")
