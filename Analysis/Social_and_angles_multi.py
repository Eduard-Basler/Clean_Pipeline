import argparse
import os
import pandas as pd
import numpy as np
from tifffile import imread
from skimage.segmentation import find_boundaries
from scipy.spatial import KDTree
from multiprocessing import Pool, cpu_count

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

# --- GLOBAL VARIABLES FOR HPC MEMORY SHARING (FORK) ---
bact_clouds = {}
global_bact_tree = None
active_ids = None
bact_pts_um = None

def process_single_bacterium(bid):
    """
    This contains your EXACT original loop logic. 
    It runs independently on its own CPU core.
    """
    my_pts = bact_clouds[bid]
    if len(my_pts) == 0:
        return bid, 0, np.nan, 0

    # 1. Crowding Index: Count unique neighbors inside a 10um radius sphere
    seen_neighbors = set()
    for pt in my_pts:
        indices_in_radius = global_bact_tree.query_ball_point(pt, r=10.0)
        for idx in indices_in_radius:
            neighbor_id = active_ids[idx]
            if neighbor_id != bid:
                seen_neighbors.add(neighbor_id)
    crowding_density = len(seen_neighbors)

    # 2. THE CRITICAL FIX: "Exclude Yourself" Strategy
    other_pts_mask = (active_ids != bid)
    other_pts = bact_pts_um[other_pts_mask]
    other_labels = active_ids[other_pts_mask]

    if len(other_pts) == 0:
        return bid, 0, np.nan, crowding_density

    # Build exclusive tree
    exclusive_neighbor_tree = KDTree(other_pts)

    # NOTE: workers=1 here because the outer loop is already using all CPU cores
    dists, indices = exclusive_neighbor_tree.query(my_pts, k=1, workers=1)

    abs_min_voxel_idx = np.argmin(dists)
    true_border_dist = float(dists[abs_min_voxel_idx])
    
    target_tree_idx = indices[abs_min_voxel_idx]
    true_closest_neighbor_id = int(other_labels[target_tree_idx])

    return bid, true_closest_neighbor_id, true_border_dist, crowding_density

def main():
    global bact_clouds, global_bact_tree, active_ids, bact_pts_um

    parser = argparse.ArgumentParser(description="Parallel Step D: HPC Multi-Core Social Engine")
    parser.add_argument("--bact_mask", required=True)
    parser.add_argument("--out_dir", default=".")
    parser.add_argument("--cores", type=int, default=0, help="Number of cores to use. 0 uses all allocated.")
    args = parser.parse_args()

    # Determine core count based on HPC allocation
    num_cores = args.cores if args.cores > 0 else cpu_count()
    print(f"I am running on an HPC... i can request more cores and more ram that is no problem lets go for that")
    print(f"🔥 Initializing Multi-Core Engine across {num_cores} CPU cores...")

    print("🚀 Extracting Bacterial Shell Point Clouds from Mask...")
    bact_mask = imread(args.bact_mask)
    
    bact_boundaries = find_boundaries(bact_mask, mode='inner')
    active_voxels = np.argwhere(bact_boundaries > 0)
    active_ids = bact_mask[bact_boundaries > 0]
    bact_pts_um = active_voxels * SCALE_ARR

    unique_bact_ids = np.unique(bact_mask)
    unique_bact_ids = unique_bact_ids[unique_bact_ids > 0]

    if len(unique_bact_ids) == 0:
        print("⚠️ No bacteria objects detected. Creating empty placeholder file.")
        df_out = pd.DataFrame(columns=[
            'Bact_ID', 'Dist_to_Nearest_Bact_um', 'Nearest_Bact_ID', 
            'Bact_Density_Radius_10um', 'Body_Vector_SVD'
        ])
        os.makedirs(args.out_dir, exist_ok=True)
        df_out.to_csv(os.path.join(args.out_dir, "stepD_isolated_output.csv"), index=False)
        return

    for bid in unique_bact_ids:
        bact_clouds[bid] = bact_pts_um[active_ids == bid]

    print("📐 Profiling structural body axis orientation vectors...")
    all_voxels_raw = np.argwhere(bact_mask > 0)
    all_ids_raw = bact_mask[bact_mask > 0]
    
    body_vectors = {}
    for bid in unique_bact_ids:
        voxels_spec = all_voxels_raw[all_ids_raw == bid]
        v_bact = calculate_bact_orientation_vector(voxels_spec)
        body_vectors[bid] = f"{v_bact[0]};{v_bact[1]};{v_bact[2]}"

    print("🌲 Indexing Global Base Tree...")
    global_bact_tree = KDTree(bact_pts_um)

    print("⚡ Mapping Edge-to-Edge Analysis across Node Processing Cores...")
    # Fire up the parallel worker pool
    with Pool(processes=num_cores) as pool:
        results = pool.map(process_single_bacterium, unique_bact_ids)

    # Reassemble parallel outputs back into order
    results_lookup = {res[0]: (res[1], res[2], res[3]) for res in results}
    
    nearest_bact_ids = [results_lookup[bid][0] for bid in unique_bact_ids]
    min_border_dists = [results_lookup[bid][1] for bid in unique_bact_ids]
    crowding_densities = [results_lookup[bid][2] for bid in unique_bact_ids]

    df_out = pd.DataFrame({
        'Bact_ID': unique_bact_ids,
        'Dist_to_Nearest_Bact_um': min_border_dists,
        'Nearest_Bact_ID': nearest_bact_ids,
        'Bact_Density_Radius_10um': crowding_densities,
        'Body_Vector_SVD': [body_vectors[bid] for bid in unique_bact_ids]
    })

    os.makedirs(args.out_dir, exist_ok=True)
    df_out.to_csv(os.path.join(args.out_dir, "stepD_isolated_output.csv"), index=False)
    print("🏁 Step D parallel execution complete!")

if __name__ == "__main__":
    main()