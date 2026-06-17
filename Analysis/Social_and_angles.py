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

def calculate_bact_orientation_vector(bact_voxels):
    if len(bact_voxels) < 3: 
        return np.array([0.0, 0.0, 1.0])
    coords_um = bact_voxels * SCALE_ARR
    centered_coords = coords_um - np.mean(coords_um, axis=0)
    _, _, vh = np.linalg.svd(centered_coords, full_matrices=False)
    return vh[0]

def main():
    parser = argparse.ArgumentParser(description="Parallel Step D: Robust Exclusive Point Cloud Social Engine")
    parser.add_argument("--bact_mask", required=True)
    parser.add_argument("--out_dir", default=".")
    args = parser.parse_args()

    print("🚀 Extracting Bacterial Shell Point Clouds from Mask...")
    bact_mask = imread(args.bact_mask)
    
    # Extract coordinates for the outer shell boundaries of ALL bacteria objects
    bact_boundaries = find_boundaries(bact_mask, mode='inner')
    active_voxels = np.argwhere(bact_boundaries > 0)
    active_ids = bact_mask[bact_boundaries > 0]
    bact_pts_um = active_voxels * SCALE_ARR

    unique_bact_ids = np.unique(bact_mask)
    unique_bact_ids = unique_bact_ids[unique_bact_ids > 0]

    if len(unique_bact_ids) == 0:
        print("⚠️ No bacteria objects detected. Skipping execution.")
        return

    # Map point cloud coordinate segments into a dictionary by ID
    bact_clouds = {}
    for bid in unique_bact_ids:
        bact_clouds[bid] = bact_pts_um[active_ids == bid]

    # Calculate 3D orientation vectors via SVD/PCA on whole volume masks
    print("📐 Profiling structural body axis orientation vectors...")
    all_voxels_raw = np.argwhere(bact_mask > 0)
    all_ids_raw = bact_mask[bact_mask > 0]
    
    body_vectors = {}
    for bid in unique_bact_ids:
        voxels_spec = all_voxels_raw[all_ids_raw == bid]
        v_bact = calculate_bact_orientation_vector(voxels_spec)
        body_vectors[bid] = f"{v_bact[0]};{v_bact[1]};{v_bact[2]}"

    print("🌲 Running Edge-to-Edge Social Distance Analysis via 'Exclude Yourself' Trees...")
    nearest_bact_ids = []
    min_border_dists = []
    crowding_densities = []

    # Build a clean base lookup to calculate crowding indices efficiently
    global_bact_tree = KDTree(bact_pts_um)

    for bid in unique_bact_ids:
        my_pts = bact_clouds[bid]
        if len(my_pts) == 0:
            nearest_bact_ids.append(0)
            min_border_dists.append(np.nan)
            crowding_densities.append(0)
            continue

        # 1. Crowding Index: Count unique neighbors inside a 10um radius sphere
        seen_neighbors = set()
        for pt in my_pts:
            indices_in_radius = global_bact_tree.query_ball_point(pt, r=10.0)
            for idx in indices_in_radius:
                neighbor_id = active_ids[idx]
                if neighbor_id != bid:
                    seen_neighbors.add(neighbor_id)
        crowding_densities.append(len(seen_neighbors))

        # 2. THE CRITICAL FIX: "Exclude Yourself" Strategy
        # Isolate coordinates belonging ONLY to other external bacteria objects
        other_pts_mask = (active_ids != bid)
        other_pts = bact_pts_um[other_pts_mask]
        other_labels = active_ids[other_pts_mask]

        if len(other_pts) == 0:
            # Handle lone survivor edge-cases safely
            min_border_dists.append(np.nan)
            nearest_bact_ids.append(0)
            continue

        # Build an exclusive tree that is 100% blind to this specific bacterium's own volume
        exclusive_neighbor_tree = KDTree(other_pts)

        # Query the closest single external point (k=1) for all of my shell coordinates
        # workers=-1 distributes the search query over all available processor cores
        dists, indices = exclusive_neighbor_tree.query(my_pts, k=1, workers=-1)

        # Extract the absolute minimum edge clearance found across the entire shell perimeter
        abs_min_voxel_idx = np.argmin(dists)
        true_border_dist = float(dists[abs_min_voxel_idx])
        
        # Resolve who owns that specific closest boundary point
        target_tree_idx = indices[abs_min_voxel_idx]
        true_closest_neighbor_id = int(other_labels[target_tree_idx])

        min_border_dists.append(true_border_dist)
        nearest_bact_ids.append(true_closest_neighbor_id)

    df_out = pd.DataFrame({
        'Bact_ID': unique_bact_ids,
        'Dist_to_Nearest_Bact_um': min_border_dists,
        'Nearest_Bact_ID': nearest_bact_ids,
        'Bact_Density_Radius_10um': crowding_densities,
        'Body_Vector_SVD': [body_vectors[bid] for bid in unique_bact_ids]
    })

    os.makedirs(args.out_dir, exist_ok=True)
    df_out.to_csv(os.path.join(args.out_dir, "stepD_isolated_output.csv"), index=False)
    print("🏁 Step D point-cloud proximity tracking execution complete!")

if __name__ == "__main__":
    main()