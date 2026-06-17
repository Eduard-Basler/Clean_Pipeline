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

def downsample_point_cloud(points, labels, voxel_size=1.0):
    """
    Downsamples a dense 3D point cloud by keeping only one representative
    point per 3D grid voxel voxel_size (e.g., 1.0 micrometer grid resolution).
    """
    if len(points) == 0:
        return points, labels
        
    # Quantize coordinates by dividing by the target grid voxel size and flooring
    grid_coords = np.floor(points / voxel_size).astype(int)
    
    # Use pandas to quickly find unique 3D grid voxel bins and keep the first point in each bin
    df = pd.DataFrame(grid_coords, columns=['z', 'y', 'x'])
    df['orig_idx'] = np.arange(len(points))
    
    # Drop duplicates based on grid coordinate combinations
    unique_indices = df.drop_duplicates(subset=['z', 'y', 'x'])['orig_idx'].values
    
    return points[unique_indices], labels[unique_indices]

def main():
    parser = argparse.ArgumentParser(description="Parallel Step: Optimized Cell-to-Cell Border Point Cloud Engine")
    parser.add_argument("--cell_mask", required=True)
    parser.add_argument("--classifier_csv", required=True)
    parser.add_argument("--out_dir", default=".")
    args = parser.parse_args()

    print("🚀 Extracting Cell Membrane Point Clouds from Mask...")
    cell_mask = imread(args.cell_mask)
    
    # 1. Extract raw inner 3D boundaries
    cell_boundaries = find_boundaries(cell_mask, mode='inner')
    c_voxels = np.argwhere(cell_boundaries > 0)
    c_labels = cell_mask[cell_boundaries > 0]
    c_pts_um = c_voxels * SCALE_ARR

    unique_cell_ids = np.unique(cell_mask)
    unique_cell_ids = unique_cell_ids[unique_cell_ids > 0]

    if len(unique_cell_ids) == 0:
        print("⚠️ No cells detected. Exiting.")
        return

    # --- THE CRITICAL OPTIMIZATION STEP ---
    print("📉 Downsampling cellular point clouds to 1.0um resolution grid to accelerate tree searches...")
    c_pts_um, c_labels = downsample_point_cloud(c_pts_um, c_labels, voxel_size=1.0)

    # Map the thinned point clouds into a quick dictionary lookup
    cell_clouds = {cid: c_pts_um[c_labels == cid] for cid in unique_cell_ids}

    # 2. Identify infected cells from Step C output
    df_class = pd.read_csv(args.classifier_csv)
    infected_cells = set()
    if 'Contested_in_Cells_Raw' in df_class.columns:
        for val in df_class['Contested_in_Cells_Raw'].dropna().astype(str):
            if val.strip() and val != 'nan':
                for c in val.split(';'):
                    infected_cells.add(int(float(c)))

    print("🌲 Running Edge-to-Edge Transmission Analysis via Optimized 'Exclude Yourself' Trees...")
    dist_to_nearest_inf = []
    nearest_inf_id = []

    for cid in unique_cell_ids:
        my_cloud = cell_clouds.get(cid, np.array([]))
        other_inf_ids = [i for i in infected_cells if i != cid]

        if len(my_cloud) == 0 or len(other_inf_ids) == 0:
            dist_to_nearest_inf.append(np.nan)
            nearest_inf_id.append(np.nan)
            continue

        # Collect thin border points of all other infected cells combined
        target_pts = []
        target_labels = []
        for inf_cid in other_inf_ids:
            pts = cell_clouds.get(inf_cid, np.array([]))
            if len(pts) > 0:
                target_pts.extend(pts)
                target_labels.extend([inf_cid] * len(pts))

        if len(target_pts) == 0:
            dist_to_nearest_inf.append(np.nan)
            nearest_inf_id.append(np.nan)
            continue

        # Build tree out of the thinned target cloud
        exclusive_infected_tree = KDTree(np.array(target_pts))

        # Query distances using all available processor threads
        dists, indices = exclusive_infected_tree.query(my_cloud, k=1, workers=-1)

        # Log absolute shortest edge-to-edge distance
        abs_min_idx = np.argmin(dists)
        dist_to_nearest_inf.append(float(dists[abs_min_idx]))
        nearest_inf_id.append(int(target_labels[indices[abs_min_idx]]))

    df_out = pd.DataFrame({
        'Cell_ID': unique_cell_ids,
        'Dist_to_Nearest_Infected_Cell': dist_to_nearest_inf,
        'Nearest_Infected_Cell_ID': nearest_inf_id
    })

    os.makedirs(args.out_dir, exist_ok=True)
    df_out.to_csv(os.path.join(args.out_dir, "stepCell_isolated_output.csv"), index=False)
    print("🏁 Cell-to-Cell Point Cloud Proximity metrics complete!")

if __name__ == "__main__":
    main()