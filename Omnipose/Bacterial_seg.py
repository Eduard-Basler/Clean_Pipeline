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
os.makedirs(OUTPUT_DIR, exist_ok=True) # Direct output directory creation

BACT_CH_IDX = 2

# ==========================================
# 2. INITIALIZE MODEL
# ==========================================
use_GPU = core.use_gpu()
print("Loading Bacteria Model (bact_fluor_omni)...")
model_bact = models.CellposeModel(
    gpu=use_GPU,
    model_type='bact_fluor_omni',
    dim=2,
    nclasses=3, # Kept at 3 to match working original script
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
    if img_4d.ndim == 4 and img_4d.shape[1] > BACT_CH_IDX:
        # Pull channel 2 as a solid 3D numpy array, exactly like script 1
        img_bact = img_4d[:, BACT_CH_IDX, :, :].astype(np.float32)
    else:
        # Fallback to keep it pure if it's already a 3D image stack
        img_bact = img_4d.astype(np.float32)

    # --- Global Normalization (Kept exactly identical) ---
    print("   -> Performing Global Normalization...")
    p1 = np.percentile(img_bact, 1)
    p99 = np.percentile(img_bact, 99)
    img_bact = np.clip((img_bact - p1) / (p99 - p1 + 1e-8), 0, 1)

    # --- B. Segment Bacteria (2D Stitching Mode - Kept identical) ---
    print("   -> Segmenting Bacteria (2D Stitching)...")

    masks_bact, flows_bact, _ = model_bact.eval(
        img_bact,            # Passed as a solid 3D numpy array
        channels=[0,0],

        do_3D=False,           # Turn OFF true 3D memory-hogging math
        stitch_threshold=0.90, # Using your updated stitching threshold

        omni=True,
        diameter=6.0,            
        cluster=True,          
        affinity_seg=True,     
        mask_threshold=-3.16,
        flow_threshold=0.4,
        niter=200,
        net_avg=False,  
        tile=True,
        tile_overlap=0.1,
        normalize=False       # Keep false because we normalize manually above
    )

    # Save output directly to OUTPUT_DIR
    base_name = filename.split('.')[0]
    bact_out_path = os.path.join(OUTPUT_DIR, f"{base_name}_masks.tif")
    imwrite(bact_out_path, masks_bact, compression='zlib')

    print(f"   ✅ Saved Masks: {len(np.unique(masks_bact)) - 1} cells found.")

    del masks_bact, flows_bact, img_4d, img_bact
    torch.cuda.empty_cache()

print("\n🎉 ALL PROCESSING COMPLETE!")