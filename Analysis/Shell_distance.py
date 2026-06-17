import argparse
import os
import pandas as pd
import numpy as np
from tifffile import imread
from skimage.segmentation import find_boundaries
from scipy.spatial import KDTree

# Microscope Spatial Spacings
SPACING_Z, SPACING_Y, SPACING_X = 0.2, 0.111, 0.111
SCALE_ARR = np.array([SPACING_Z, SPACING_Y, SPACING_X])

def main():
    parser = argparse.ArgumentParser(description="Parallel Step B: CPU Coordinate Tree Distance Profile Engine")
    parser.add_argument("--cell_mask", required=True)
    parser.add_argument("--bact_mask", required=True)
    parser.add_argument("--out_dir", default=".")
    args = parser.parse_args()

    print("🚀 Extracting Surface Coordinates from Masks...")
    cell_mask = imread(args.cell_mask)
    bact_mask = imread(args.bact_mask)
    img_shape = cell_mask.shape

    # 1. Extract Cell Membrane Surface Points
    cell_boundaries = find_boundaries(cell_mask, mode='inner')
    memb_voxels = np.argwhere(cell_boundaries > 0)
    memb_labels = cell_mask[cell_boundaries > 0]
    memb_pts_um = memb_voxels * SCALE_ARR

    if len(memb_pts_um) == 0:
        print("⚠️ No cell membranes detected. Exiting early.")
        return

    # 2. Extract Bacteria Shell Points
    bact_boundaries = find_boundaries(bact_mask, mode='inner')
    bact_voxels = np.argwhere(bact_boundaries > 0)
    bact_labels = bact_mask[bact_boundaries > 0]
    bact_pts_um = bact_voxels * SCALE_ARR

    unique_bact_ids = np.unique(bact_mask)
    unique_bact_ids = unique_bact_ids[unique_bact_ids > 0]

    # Calculate raw centroid coordinates for Downward Ray Tracing
    bact_centers = np.argwhere(bact_mask > 0)
    bact_center_labels = bact_mask[bact_mask > 0]
    
    centers_dict = {}
    for bid in unique_bact_ids:
        coords = bact_centers[bact_center_labels == bid]
        if len(coords) > 0:
            centers_dict[bid] = coords.mean(axis=0).round().astype(int)

    print("🌲 Building High-Speed Cellular Membrane KDTree...")
    # workers=-1 utilizes all available CPU processing threads on your cluster node
    membrane_tree = KDTree(memb_pts_um)

    results = []
    print("🔍 Querying Geometric Shell Clearances via Spatial Indexing...")
    
    for bid in unique_bact_ids:
        # Isolate this specific bacterium's outer shell coordinates
        b_pts = bact_pts_um[bact_labels == bid]
        if len(b_pts) == 0:
            continue

        # Find the distance to the closest membrane point, and its index in the tree
        dists, indices = membrane_tree.query(b_pts, k=1, workers=-1)
        
        # Calculate summary metrics along the shell
        bact_min_dist = float(np.min(dists))
        bact_max_dist = float(np.max(dists))
        bact_mean_dist = float(np.mean(dists))
        
        # Determine the primary cell ownership assignment based on the absolute closest voxel point
        closest_voxel_idx = np.argmin(dists)
        assigned_closest_cell = int(memb_labels[indices[closest_voxel_idx]])

        # Execute Downward Ray Tracing for Substrate Profiling
        cell_below_id = 0
        if bid in centers_dict:
            z_curr, y_curr, x_curr = centers_dict[bid]
            for z_trace in range(z_curr, -1, -1):
                val = int(cell_mask[z_trace, y_curr, x_curr])
                if val > 0:
                    cell_below_id = val
                    break

        results.append({
            'Bact_ID': int(bid),
            'Closest_Cell_ID_via_Membrane': assigned_closest_cell,
            'Dist_to_Membrane_um': bact_min_dist,
            'Cell_Below_ID': cell_below_id,
            'Intracellular_Z_Ratio': np.nan,
            'Bact_Voxel_Min_Dist_to_Membrane_um': bact_min_dist,
            'Bact_Voxel_Max_Dist_to_Membrane_um': bact_max_dist,
            'Bact_Voxel_Mean_Dist_to_Membrane_um': bact_mean_dist
        })

    df_out = pd.DataFrame(results) if results else pd.DataFrame(columns=['Bact_ID'])
    os.makedirs(args.out_dir, exist_ok=True)
    df_out.to_csv(os.path.join(args.out_dir, "stepB_isolated_output.csv"), index=False)
    print("🏁 Step B Point-Cloud Geometry Engine complete!")

if __name__ == "__main__":
    main()