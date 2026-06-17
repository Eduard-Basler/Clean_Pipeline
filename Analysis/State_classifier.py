import argparse
import os
import pandas as pd
import numpy as np
from tifffile import imread
import cupy as cp
from cupyx.scipy.ndimage import binary_dilation, binary_erosion

# Microscope Spatial Spacings
SPACING_Z, SPACING_Y, SPACING_X = 0.2, 0.111, 0.111

def main():
    parser = argparse.ArgumentParser(description="Parallel Step C: Whole-Mask GPU Morphological Boundary Classifier")
    parser.add_argument("--cell_mask", required=True)
    parser.add_argument("--bact_mask", required=True)
    parser.add_argument("--out_dir", default=".")
    args = parser.parse_args()

    print("🚀 Loading whole volumes into GPU memory space...")
    cell_mask_gpu = cp.asarray(imread(args.cell_mask))
    bact_mask_gpu = cp.asarray(imread(args.bact_mask))
    
    # Calculate anisotropic morphological spatial gates
    EXPANSION_XY_UM, EXPANSION_Z_UM = 1.0, 1.5
    rz = int(np.ceil(EXPANSION_Z_UM / SPACING_Z))
    ry = int(np.ceil(EXPANSION_XY_UM / SPACING_Y))
    rx = int(np.ceil(EXPANSION_XY_UM / SPACING_X))

    zg, yg, xg = np.ogrid[-rz:rz+1, -ry:ry+1, -rx:rx+1]
    struct_element = (zg**2 / rz**2 + yg**2 / ry**2 + xg**2 / rx**2) <= 1.0
    struct_gpu = cp.asarray(struct_element)

    print("⚡ Executing unified whole-image Morphological filters on GPU...")
    all_cells_binary = (cell_mask_gpu > 0)

    # Dilate and erode the entire volume space simultaneously
    global_eroded = binary_erosion(all_cells_binary, structure=struct_gpu)
    global_dilated = binary_dilation(all_cells_binary, structure=struct_gpu)

    # Extract target contact zones
    global_border_zone = global_dilated ^ global_eroded
    global_inner_border = all_cells_binary ^ global_eroded

    print("🔍 Profiling global boundary intersection matrices...")
    bact_in_boundaries = (bact_mask_gpu > 0) & global_border_zone
    bact_in_inner_border = (bact_mask_gpu > 0) & global_inner_border
    
    bact_ids = cp.unique(bact_mask_gpu)
    bact_ids = bact_ids[bact_ids > 0]
    
    total_bact_vols = cp.bincount(bact_mask_gpu.ravel())
    
    # CRASH PROTECTION ENGINE: Safely handle zero-size selections on GPU
    if bact_mask_gpu[bact_in_boundaries].size > 0:
        contested_vols = cp.bincount(bact_mask_gpu[bact_in_boundaries].ravel(), minlength=len(total_bact_vols))
    else:
        contested_vols = cp.zeros(len(total_bact_vols), dtype=cp.int32)

    if bact_mask_gpu[bact_in_inner_border].size > 0:
        inner_border_vols = cp.bincount(bact_mask_gpu[bact_in_inner_border].ravel(), minlength=len(total_bact_vols))
    else:
        inner_border_vols = cp.zeros(len(total_bact_vols), dtype=cp.int32)

    # Move data to CPU for dataframe grouping
    bact_ids_cpu = cp.asnumpy(bact_ids)
    total_bact_vols_cpu = cp.asnumpy(total_bact_vols)
    contested_vols_cpu = cp.asnumpy(contested_vols)
    inner_border_vols_cpu = cp.asnumpy(inner_border_vols)
    
    cell_mask_cpu = cp.asnumpy(cell_mask_gpu)
    bact_mask_cpu = cp.asnumpy(bact_mask_gpu)

    # Rapid extraction of overlapping identity mappings
    overlap_pairs = pd.DataFrame({
        'Bact_ID': bact_mask_cpu[bact_mask_cpu > 0],
        'Cell_ID': cell_mask_cpu[bact_mask_cpu > 0]
    }).drop_duplicates()
    
    inside_cells_map = overlap_pairs[overlap_pairs['Cell_ID'] > 0].groupby('Bact_ID')['Cell_ID'].apply(lambda x: ";".join(map(str, sorted(x)))).to_dict()

    results = []
    for bid in bact_ids_cpu:
        v_total = total_bact_vols_cpu[bid]
        v_contested = contested_vols_cpu[bid]
        v_inner = inner_border_vols_cpu[bid]
        
        # Flag as contested if >= 10% of the bacterium sits inside the shell
        is_contested = (v_contested / v_total) >= 0.10
        cells_involved = inside_cells_map.get(bid, "")
        total_cells = len(cells_involved.split(';')) if cells_involved else 0

        results.append({
            'Bact_ID': int(bid),
            'Not_contested': not is_contested,
            'Contested_in_Cells_Raw': cells_involved if (v_inner > 0) else "",
            'Contested_in_Total': total_cells if (v_inner > 0) else 0,
            'Contested_out_cells': cells_involved if is_contested else "",
            'Contested_out_Total': total_cells if is_contested else 0
        })

    df_out = pd.DataFrame(results)
    os.makedirs(args.out_dir, exist_ok=True)
    df_out.to_csv(os.path.join(args.out_dir, "stepC_isolated_output.csv"), index=False)
    print("🏁 Step C Whole-Mask Morphological boundary classification absolute complete!")

if __name__ == "__main__":
    main()