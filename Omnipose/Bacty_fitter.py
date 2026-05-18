import os
import numpy as np
import tifffile as tiff
import scipy.ndimage as ndi
from skimage.morphology import skeletonize
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from joblib import Parallel, delayed
import sys

os.environ["OMP_NUM_THREADS"] = "1"

# =============================================================================
# 1. SETTINGS
# =============================================================================
RES_X, RES_Y, RES_Z = 0.11, 0.11, 0.20
MICRON_SCALE = np.array([RES_Z, RES_Y, RES_X])
VOXEL_VOL_UM3 = RES_X * RES_Y * RES_Z

BACT_CHANNEL = 2  

UNIT_VOLUME_UM3 = 1.2    
CAPSULE_R_UM = 0.4       

INPUT_MASKS_DIR = sys.argv[1]
INPUT_RAW_DIR   = sys.argv[2]
OUTPUT_DIR      = sys.argv[3]


# =============================================================================
# 2. THE POLISHED INSIDE-OUT WORKER
# =============================================================================

def process_supermask_worker(label_id, mask_crop, raw_crop):
    strict_mask = (mask_crop == label_id)
    indices = np.argwhere(strict_mask)
    
    vol_um3 = len(indices) * VOXEL_VOL_UM3
    if vol_um3 < (UNIT_VOLUME_UM3 * 0.2): return []

    n_cells = max(1, int(round(vol_um3 / UNIT_VOLUME_UM3)))
    local_cells = []

    # --- BULLETPROOF CLUMP SEVERING ---
    if n_cells > 1:
        smoothed = ndi.gaussian_filter(raw_crop.astype(float), sigma=[0.5, 1.5, 1.5])
        smoothed[~strict_mask] = 0
        
        peaks = peak_local_max(smoothed, min_distance=3, num_peaks=n_cells, labels=strict_mask)
        
        if len(peaks) > 0:
            markers = np.zeros_like(strict_mask, dtype=int)
            for idx, (z, y, x) in enumerate(peaks):
                markers[z, y, x] = idx + 1
                
            cell_labels = watershed(-smoothed, markers, mask=strict_mask)
            domains = [cell_labels == i for i in range(1, len(peaks) + 1)]
        else:
            domains = [strict_mask]
    else:
        domains = [strict_mask]

    # --- SKELETON, BALLOON, & EDGE SMOOTHING ---
    for domain in domains:
        if not np.any(domain): continue
        
        skel = skeletonize(domain)
        if not np.any(skel): skel = domain 

        dist = ndi.distance_transform_edt(~skel, sampling=[RES_Z, RES_Y, RES_X])
        balloon = dist <= CAPSULE_R_UM
        
        smoothed_balloon = ndi.gaussian_filter(balloon.astype(float), sigma=0.5) >= 0.5
        
        iron_cage = ndi.binary_dilation(domain, iterations=2)
        final_biological_cell = smoothed_balloon & iron_cage
        
        if np.any(final_biological_cell):
            local_cells.append(final_biological_cell)

    return local_cells

# =============================================================================
# 3. THE MASTER PIPELINE (MULTI-SERIES)
# =============================================================================

def run_pipeline():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

    for root, dirs, files in os.walk(INPUT_MASKS_DIR):
        for mask_name in files:
            if not mask_name.endswith("_mask.tif"): continue
            
            mask_path = os.path.join(root, mask_name)
            
            # --- UPDATED FILE MATCHER ---
            # Handles both "..._RAW_bact_mask.tif" and standard "..._mask.tif"
            if mask_name.endswith("_bact_mask.tif"):
                base_name = mask_name.replace("_bact_mask.tif", "")
            else:
                base_name = mask_name.replace("_mask.tif", "")
            
            raw_path = None
            for raw_root, _, raw_files in os.walk(INPUT_RAW_DIR):
                for r_file in raw_files:
                    # Look for the exact base name (e.g., "..._Series5_RAW")
                    if r_file.lower().startswith(base_name.lower()):
                        raw_path = os.path.join(raw_root, r_file)
                        break
                if raw_path: break
                
            if not raw_path:
                print(f"\n[!] Skipping {mask_name}: Could not find matching raw file in {INPUT_RAW_DIR}")
                continue

            print(f"\n--- Loading Series: {mask_name} ---")
            omnipose_mask = tiff.imread(mask_path).astype(np.int32)
            full_raw = tiff.imread(raw_path)
            
            # --- EXTRACTING CHANNEL 3 (Index 2) ---
            if full_raw.ndim == 4:
                raw_signal = full_raw[BACT_CHANNEL] if full_raw.shape[0] < 10 else full_raw[:, BACT_CHANNEL]
            else:
                raw_signal = full_raw
                
            pristine_mask = np.zeros_like(omnipose_mask, dtype=np.uint16)
            
            print("Fusing fragmented 2D Z-slices into 3D Super-Masks...")
            omni_bin = omnipose_mask > 0
            
            melt_struct = np.zeros((5, 3, 3), dtype=bool)
            melt_struct[:, 1, 1] = True 
            melt_struct[2, :, :] = True 
            
            fused_binary = ndi.binary_closing(omni_bin, structure=melt_struct)
            
            super_labels, num_features = ndi.label(fused_binary)
            print(f"Glued pancakes together. Discovered {num_features} contiguous 3D cellular islands.")
            
            slices = ndi.find_objects(super_labels) 
            
            tasks = []
            for i, slc in enumerate(slices):
                if slc is not None:
                    label_id = i + 1
                    
                    z_slc, y_slc, x_slc = slc
                    z1, z2 = max(0, z_slc.start - 4), min(super_labels.shape[0], z_slc.stop + 4)
                    y1, y2 = max(0, y_slc.start - 4), min(super_labels.shape[1], y_slc.stop + 4)
                    x1, x2 = max(0, x_slc.start - 4), min(super_labels.shape[2], x_slc.stop + 4)
                    
                    padded_slc = (slice(z1, z2), slice(y1, y2), slice(x1, x2))
                    
                    m_crop = super_labels[padded_slc]
                    r_crop = raw_signal[padded_slc]
                    tasks.append((label_id, padded_slc, m_crop, r_crop))
                    
            print(f"Dispatching {len(tasks)} islands to 64 Cores for Skeleton Inflation...")
            
            results = Parallel(n_jobs=-1, backend="loky")(
                delayed(process_supermask_worker)(t[0], t[2], t[3]) for t in tasks
            )
            
            new_cell_id = 1
            for task_info, worker_result in zip(tasks, results):
                if worker_result is None or len(worker_result) == 0:
                    continue
                    
                _, padded_slc, _, _ = task_info
                canvas_view = pristine_mask[padded_slc]
                
                for final_cell_mask in worker_result:
                    canvas_view[final_cell_mask] = new_cell_id
                    new_cell_id += 1

            rel_path = os.path.relpath(root, INPUT_MASKS_DIR)
            out_folder = os.path.join(OUTPUT_DIR, rel_path)
            if not os.path.exists(out_folder): 
                os.makedirs(out_folder)

            out_path = os.path.join(out_folder, mask_name.replace("_mask.tif", "_Pristine_Skeleton.tif"))
            tiff.imwrite(out_path, pristine_mask, compression='zlib')
            print(f"Saved: {out_path} | Total rigid cells perfectly fit: {new_cell_id - 1}")

if __name__ == "__main__":
    run_pipeline()
