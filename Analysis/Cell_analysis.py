import argparse
import os
import pandas as pd
import numpy as np
from tifffile import imread
from skimage.measure import regionprops_table, regionprops
from scipy.spatial import KDTree, ConvexHull
from scipy.ndimage import binary_erosion

# Microscope Scaling Constants (Physical micrometer step size per voxel)
SPACING_Z, SPACING_Y, SPACING_X = 0.2, 0.111, 0.111
VOXEL_VOLUME = SPACING_Z * SPACING_Y * SPACING_X

def filter_small_cells_cpu(cell_mask_cpu, min_voxels=5000):
    print(f"  [CPU] Sifting cell segments smaller than {min_voxels} voxels...")
    counts = np.bincount(cell_mask_cpu.ravel())
    bad_ids = np.where((counts < min_voxels) & (counts > 0))[0]
    
    if len(bad_ids) > 0:
        lookup = np.arange(int(cell_mask_cpu.max()) + 1, dtype=cell_mask_cpu.dtype)
        lookup[bad_ids] = 0
        cell_mask_cpu = lookup[cell_mask_cpu]
        counts = np.bincount(cell_mask_cpu.ravel())
    return cell_mask_cpu, counts

def main():
    parser = argparse.ArgumentParser(description="Memory-Safe True 3D Cell Factory (CPU Only)")
    parser.add_argument("--cell_mask", required=True)
    parser.add_argument("--nuc_mask", required=True)
    parser.add_argument("--c1", required=True)
    parser.add_argument("--c2", required=True)
    parser.add_argument("--c3", required=True)
    parser.add_argument("--c4", required=True)
    parser.add_argument("--out_dir", default=".")
    args = parser.parse_args()

    print("🚀 Initializing Optimized High-Speed Cell Factory...")
    raw_cell_mask = imread(args.cell_mask)
    nuc_mask = imread(args.nuc_mask)
    channels_cpu = {1: imread(args.c1), 2: imread(args.c2), 3: imread(args.c3), 4: imread(args.c4)}
    img_shape = raw_cell_mask.shape

    # 1. Clean small fragments using CPU bincount
    cell_mask_cpu, counts_cpu = filter_small_cells_cpu(raw_cell_mask, min_voxels=5000)

    # 2 & 4. Integrated Bounding Box Processing Loop
    print("  [CPU] Extracting Bounding Box Morphologies & 3D Spatial Tensors...")
    
    elong_map = {}
    flat_map = {}
    sym_map = {}
    cell_solidity = {}
    cell_circularity = {}
    cell_avg_top_z = {}
    top10pct_ch4_sums = {}
    top5_ch4_sums = {}
    top5_ch4_stds = {}

    for prop in regionprops(cell_mask_cpu):
        cid = prop.label
        z_min, y_min, x_min, z_max, y_max, x_max = prop.bbox
        sub_mask = prop.image 
        
        # --- PRECISE 3D SPATIAL TENSOR COMPUTATION VIA LOCAL BOUNDING BOX ---
        local_z, local_y, local_x = np.where(sub_mask)
        
        # Convert local voxel coordinates to global micrometer coordinates
        z_um = (local_z + z_min) * SPACING_Z
        y_um = (local_y + y_min) * SPACING_Y
        x_um = (local_x + x_min) * SPACING_X
        
        # Calculate cell center of mass
        m_z = np.mean(z_um)
        m_y = np.mean(y_um)
        m_x = np.mean(x_um)
        
        # Calculate precise centered distances
        zc = z_um - m_z
        yc = y_um - m_y
        xc = x_um - m_x
        
        # Build Covariance Matrix
        cov = np.array([
            [np.mean(zc*zc), np.mean(zc*yc), np.mean(zc*xc)],
            [np.mean(zc*yc), np.mean(yc*yc), np.mean(yc*xc)],
            [np.mean(zc*xc), np.mean(yc*xc), np.mean(xc*xc)]
        ])
        
        # Solve Eigenvalues
        eigvals = np.linalg.eigvalsh(cov)
        e0, e1, e2 = eigvals[2], eigvals[1], eigvals[0]
        elong_map[cid] = e1 / e0 if e0 > 0 else 1.0
        flat_map[cid] = e2 / e1 if e1 > 0 else 1.0
        
        if e0 > 0 or e1 > 0 or e2 > 0:
            me = (e0 + e1 + e2) / 3.0
            fa = np.sqrt(1.5) * np.sqrt((e0-me)**2 + (e1-me)**2 + (e2-me)**2) / np.sqrt(e0**2 + e1**2 + e2**2)
            sym_map[cid] = 1.0 - np.clip(fa, 0.0, 1.0)
        else:
            sym_map[cid] = 1.0

        # --- EXTRACT SURFACE CRUST & INTENSITIES ---
        footprint = np.any(sub_mask, axis=0)
        if np.any(footprint):
            dZ = sub_mask.shape[0]
            max_z_local = dZ - 1 - np.argmax(sub_mask[::-1], axis=0)
            avg_top_z = float(np.mean(max_z_local[footprint]) + z_min)
        else:
            avg_top_z = np.nan
        cell_avg_top_z[cid] = avg_top_z

        if not np.isnan(avg_top_z):
            avg_top_z_int = int(np.round(avg_top_z))
            top_z_start = max(z_min, avg_top_z_int - 5)
            top_z_end = min(z_max, avg_top_z_int)
            
            local_top_z_start = top_z_start - z_min
            local_top_z_end = top_z_end - z_min
            top5_mask = sub_mask[local_top_z_start:local_top_z_end]
            
            if np.any(top5_mask):
                ch4_crop = channels_cpu[4][top_z_start:top_z_end, y_min:y_max, x_min:x_max]
                top5_ch4_sums[cid] = float(np.sum(ch4_crop[top5_mask]))
                top5_ch4_stds[cid] = float(np.std(ch4_crop[top5_mask]))
            else:
                top5_ch4_sums[cid] = 0.0
                top5_ch4_stds[cid] = 0.0
        else:
            top5_ch4_sums[cid] = 0.0
            top5_ch4_stds[cid] = 0.0

        z_length = z_max - z_min
        slice_count_10pct = max(1, int(np.round(0.1 * z_length)))
        top_10pct_z_start = max(z_min, z_max - slice_count_10pct)
        local_10pct_z_start = top_10pct_z_start - z_min
        top10pct_mask = sub_mask[local_10pct_z_start:]
        
        if np.any(top10pct_mask):
            ch4_crop = channels_cpu[4][top_10pct_z_start:z_max, y_min:y_max, x_min:x_max]
            top10pct_ch4_sums[cid] = float(np.sum(ch4_crop[top10pct_mask]))
        else:
            top10pct_ch4_sums[cid] = 0.0

        # Precise Solidity via Local Convex Hull
        if sub_mask.sum() >= 4:
            eroded_mask = binary_erosion(sub_mask)
            surface_mask = sub_mask ^ eroded_mask
            pts = np.argwhere(surface_mask)
            try:
                hull = ConvexHull(pts * [SPACING_Z, SPACING_Y, SPACING_X])
                cell_solidity[cid] = min(1.0, (prop.area * VOXEL_VOLUME) / hull.volume) if hull.volume > 0 else 1.0
            except:
                cell_solidity[cid] = 1.0
        else:
            cell_solidity[cid] = 1.0

        # 2D Projected Circularity
        proj_2d = np.max(sub_mask, axis=0)
        from skimage.measure import label as l2d, regionprops as r2d
        p2d_list = r2d(l2d(proj_2d.astype(np.uint8)))
        if p2d_list:
            circ = (4 * np.pi * p2d_list[0].area) / (p2d_list[0].perimeter ** 2) if p2d_list[0].perimeter > 0 else 1.0
            cell_circularity[cid] = min(1.0, circ)
        else:
            cell_circularity[cid] = 1.0

    # 3. Fast CPU Table Building
    print("  [CPU] Generating tabular summaries...")
    df_cell = pd.DataFrame(regionprops_table(cell_mask_cpu, properties=['label', 'centroid', 'bbox']))
    df_cell.rename(columns={
        'label': 'Cell_ID',
        'centroid-0': 'Cell_Z_raw', 'centroid-1': 'Cell_Y_raw', 'centroid-2': 'Cell_X_raw'
    }, inplace=True)
    
    df_cell['Cell_Volume'] = df_cell['Cell_ID'].map(lambda x: counts_cpu[x] * VOXEL_VOLUME)
    df_cell['Cell_Volume_um3'] = df_cell['Cell_Volume'] 
    
    df_cell['Cell_Z'] = df_cell['Cell_Z_raw'] * SPACING_Z
    df_cell['Cell_Y'] = df_cell['Cell_Y_raw'] * SPACING_Y
    df_cell['Cell_X'] = df_cell['Cell_X_raw'] * SPACING_X

    # Mapping shapes back to main dataframe
    df_cell['Cell_Elongation'] = df_cell['Cell_ID'].map(elong_map).fillna(1.0)
    df_cell['Cell_Flatness'] = df_cell['Cell_ID'].map(flat_map).fillna(1.0)
    df_cell['Cell_3D_Symmetry_Index'] = df_cell['Cell_ID'].map(sym_map).fillna(1.0)
    df_cell['Cell_Solidity'] = df_cell['Cell_ID'].map(cell_solidity).fillna(1.0)
    df_cell['Cell_Circularity'] = df_cell['Cell_ID'].map(cell_circularity).fillna(1.0)
    df_cell['Cell_Ch4_Top_10Percent_Sum'] = df_cell['Cell_ID'].map(top10pct_ch4_sums).fillna(0.0)
    df_cell['Cell_Avg_Top_Z_um'] = df_cell['Cell_ID'].map(cell_avg_top_z).fillna(np.nan) * SPACING_Z
    df_cell['Cell_Ch4_Top5_Sum'] = df_cell['Cell_ID'].map(top5_ch4_sums).fillna(0.0)
    df_cell['Cell_Ch4_Top5_Std'] = df_cell['Cell_ID'].map(top5_ch4_stds).fillna(0.0)

    # Output intensities
    for ch in [1, 2, 3, 4]:
        ch_table = pd.DataFrame(regionprops_table(cell_mask_cpu, channels_cpu[ch], properties=['label', 'intensity_mean']))
        mean_dict = ch_table.set_index('label')['intensity_mean'].to_dict()
        df_cell[f'Cell_Total_Intensity_Ch{ch}'] = df_cell['Cell_ID'].map(mean_dict).fillna(0.0) * df_cell['Cell_ID'].map(lambda x: counts_cpu[x])

    # Frame border checks (XY only)
    df_cell['Cell_Touching_Border'] = (
        (df_cell['bbox-1'] == 0) | (df_cell['bbox-4'] == img_shape[1]) |
        (df_cell['bbox-2'] == 0) | (df_cell['bbox-5'] == img_shape[2])
    )
    df_cell.drop(columns=[c for c in df_cell.columns if 'bbox-' in c or '_raw' in c], inplace=True)

    # Neighborhood densities
    centers = df_cell[['Cell_Z', 'Cell_Y', 'Cell_X']].values
    if len(centers) > 1:
        tree = KDTree(centers)
        df_cell['Cell_Density_Radius_30um'] = [len(tree.query_ball_point(c, r=30.0)) - 1 for c in centers]
        dists, _ = tree.query(centers, k=min(4, len(centers)))
        df_cell['Cell_Mean_Distance_to_3_Neighbors'] = np.mean(dists[:, 1:4], axis=1) if dists.shape[1] >= 4 else np.nan
    else:
        df_cell['Cell_Density_Radius_30um'] = 0
        df_cell['Cell_Mean_Distance_to_3_Neighbors'] = np.nan

    # Clean Nuclear summaries 
    df_nuc = pd.DataFrame(regionprops_table(nuc_mask, properties=['label', 'area', 'centroid']))
    df_nuc.rename(columns={'label': 'Cell_ID', 'area': 'NVox', 'centroid-0': 'NZ', 'centroid-1': 'NY', 'centroid-2': 'NX'}, inplace=True)
    df_nuc['Nuc_Volume'] = df_nuc['NVox'] * VOXEL_VOLUME
    df_nuc['Nuc_Z'] = df_nuc['NZ'] * SPACING_Z
    df_nuc['Nuc_Y'] = df_nuc['NY'] * SPACING_Y
    df_nuc['Nuc_X'] = df_nuc['NX'] * SPACING_X
    
    nuc_means = regionprops_table(nuc_mask, intensity_image=channels_cpu[1], properties=['label', 'intensity_mean'])
    df_nm = pd.DataFrame(nuc_means)
    mean_nuc_dict = df_nm.set_index('label')['intensity_mean'].to_dict()
    df_nuc['Nuc_Sum_Intensity'] = df_nuc['Cell_ID'].map(mean_nuc_dict).fillna(0.0) * df_nuc['NVox']
    df_nuc.drop(columns=['NVox', 'NZ', 'NY', 'NX'], inplace=True)

    df_final = pd.merge(df_cell, df_nuc, on='Cell_ID', how='left').sort_values(by='Cell_ID')
    
    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, "clean_cell_stats.csv")
    df_final.to_csv(out_path, index=False)
    print(f"🎉 Fully Restored 3D CPU-Only Cell Factory Complete! Saved to: {out_path}")

if __name__ == "__main__":
    main()