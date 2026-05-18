import os
import numpy as np
import concurrent.futures
from skimage.io import imread, imsave
from skimage.measure import regionprops
from pathlib import Path
import warnings

# Suppress TIF metadata warnings
warnings.filterwarnings("ignore")

def sync_masks(cell_mask_path, nuc_mask_path, output_path):
    """
    Matches Raw Nucleus IDs to their parent Cell IDs.
    """
    print(f"  -> Syncing Raw: {cell_mask_path.name}")
    
    # Load masks
    cell_mask = imread(cell_mask_path).astype(np.uint32)
    nuc_mask = imread(nuc_mask_path).astype(np.uint32)
    new_nuc_mask = np.zeros_like(nuc_mask, dtype=np.uint16)
    
    # Analyze every nucleus
    nuc_regions = regionprops(nuc_mask)
    
    for nuc in nuc_regions:
        coords = nuc.coords
        
        # Extract cell mask values at the nucleus coordinates
        cell_values = cell_mask[tuple(coords.T)]
        
        # Filter background
        valid_cell_values = cell_values[cell_values > 0]
        
        if len(valid_cell_values) > 0:
            # Majority vote for Parent ID
            vals, counts = np.unique(valid_cell_values, return_counts=True)
            parent_id = vals[np.argmax(counts)]
            
            # Map Nuc to Cell ID
            new_nuc_mask[tuple(coords.T)] = parent_id

    imsave(output_path, new_nuc_mask, check_contrast=False)
    print(f"  ✅ Synced: {output_path.name}")

if __name__ == "__main__":
    # --- PATHS (Pointing to Raw Masks) ---
    DATA_ROOT = Path(r"C:\Users\edaba\OneDrive\Desktop\Master\Imaging_Project_Lapwin\Interactive_Napari\Data")
    MASK_IN = DATA_ROOT / "Masks"
    SYNCED_OUT = DATA_ROOT / "Synced_Masks"
    
    SYNCED_OUT.mkdir(parents=True, exist_ok=True)

    # Gather all raw cell masks
    cell_files = list(MASK_IN.glob("*_MASKS_Cells.tif"))
    
    tasks = []
    for c_path in cell_files:
        # Match "Name_MASKS_Cells.tif" to "Name_MASKS_Nuc.tif"
        n_path = MASK_IN / c_path.name.replace("_Cells.tif", "_Nuc.tif")
        
        if n_path.exists():
            out_name = c_path.name.replace("_Cells.tif", "_Nuc_SYNCED.tif")
            tasks.append((c_path, n_path, SYNCED_OUT / out_name))

    if not tasks:
        print(f"❌ Still no files found! Checked: {MASK_IN}")
        print("Double check that your files end exactly in '_MASKS_Cells.tif' and '_MASKS_Nuc.tif'")
    else:
        # Large 3D files can be memory intensive, using 4-6 workers is safest
        MAX_WORKERS = 6 
        
        print(f"🚀 Syncing {len(tasks)} Raw Mask sets...")
        with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(sync_masks, *t) for t in tasks]
            concurrent.futures.wait(futures)
            
        print(f"\n🎉 Sync complete! Files are in: {SYNCED_OUT}")