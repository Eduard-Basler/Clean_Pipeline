import os
import glob
import time
import numpy as np
import pandas as pd
from tifffile import imread
from skimage.measure import regionprops_table, regionprops
from skimage.segmentation import expand_labels
from scipy.spatial.distance import cdist
import warnings
import matplotlib.pyplot as plt
from skimage.filters import threshold_otsu
from scipy.ndimage import distance_transform_edt
from skimage.io import imsave

warnings.filterwarnings("ignore")

# ==========================================
# 1. DIRECTORY CONFIGURATION
# ==========================================
BASE_DIR = r"C:\Users\edaba\OneDrive\Desktop\Master\Imaging_Project_Lapwin\Interactive_Napari\Data"

RAW_DIR  = os.path.join(BASE_DIR, "Split")
CELL_DIR = os.path.join(BASE_DIR, r"Masks\Cells")
NUC_DIR  = os.path.join(BASE_DIR, r"Masks\Nuc_synched")
BACT_DIR = os.path.join(BASE_DIR, r"Masks\Bact")
OUT_DIR  = os.path.join(BASE_DIR, "Analysis_Results")

# Validation folders for Cilia classification
VAL_DIR = os.path.join(OUT_DIR, "Cilia_Validation")
PLOT_DIR = os.path.join(OUT_DIR, "Plots")
os.makedirs(os.path.join(VAL_DIR, "Ciliated"), exist_ok=True)
os.makedirs(os.path.join(VAL_DIR, "Non_Ciliated"), exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)

# 3D Calibration (Multiply Z-axis distance by your anisotropy if needed)
# If your Z-steps are 1.8x further apart than X/Y, we multiply Z by 1.8 for true physical distance.
Z_ANISOTROPY = 1.8 
VOXEL_SCALING = np.array([Z_ANISOTROPY, 1.0, 1.0])

# ==========================================
# 2. BATCH PROCESSING LOOP
# ==========================================
raw_files = sorted(glob.glob(os.path.join(RAW_DIR, "*_RAW.tif")))
print(f"Found {len(raw_files)} raw images to analyze.")

for raw_path in raw_files:
    filename = os.path.basename(raw_path)
    base_name = filename.replace("_RAW.tif", "") # e.g. "...rep2_006_Series1"
    
    print(f"\n🚀 Processing: {base_name}")
    start_time = time.time()
    
    # --- A. FILE MATCHING ---
    # We use glob to find the mask that contains the base_name
    try:
        cell_mask_path = glob.glob(os.path.join(CELL_DIR, f"*{base_name}*.tif"))[0]
        nuc_mask_path  = glob.glob(os.path.join(NUC_DIR, f"*{base_name}*.tif"))[0]
        bact_mask_path = glob.glob(os.path.join(BACT_DIR, f"*{base_name}*.tif"))[0]
    except IndexError:
        print(f"   ⚠️ Could not find all matching masks for {base_name}. Skipping.")
        continue

    # --- B. LOAD DATA ---
    print("   -> Loading large 3D arrays...")
    raw_stack = imread(raw_path)
    
    # Safely extract channels based on where the "Channel" dimension lives
    if raw_stack.ndim == 4:
        if raw_stack.shape[1] < 10:  # Format: (Z, C, Y, X)
            ch1_raw = raw_stack[:, 0, :, :]  # Ch 1 (Nuc)
            ch2_raw = raw_stack[:, 1, :, :]  # Ch 2 
            ch3_raw = raw_stack[:, 2, :, :]  # Ch 3 (Bact)
            ch4_raw = raw_stack[:, 3, :, :]  # Ch 4 (Cell)
            
            # ---> THIS IS THE MISSING LINE: Move channels to the very end for regionprops
            raw_multi = np.moveaxis(raw_stack, 1, -1) 
            
        else:                        # Format: (Z, Y, X, C)
            ch1_raw = raw_stack[..., 0]
            ch2_raw = raw_stack[..., 1]
            ch3_raw = raw_stack[..., 2]
            ch4_raw = raw_stack[..., 3]
            
            # ---> THIS IS THE MISSING LINE: Channels are already at the end, just assign it
            raw_multi = raw_stack 
            
        # ... [Your recent raw_multi and channel extraction code] ...
        nuc_raw  = ch1_raw
        bact_raw = ch3_raw
        cell_raw = ch4_raw
    else:
        print(f"   ⚠️ ERROR: Raw image is not 4D (Shape: {raw_stack.shape}). Skipping.")
        continue
    
    # ---> ADD THESE LINES BACK IN HERE <---
    cell_mask = imread(cell_mask_path)
    nuc_mask  = imread(nuc_mask_path)
    bact_mask = imread(bact_mask_path)
    
    # Failsafe check to ensure shapes actually match
    if nuc_mask.shape[:3] != nuc_raw.shape[:3]: 
        print(f"   ⚠️ ERROR: Shape mismatch! Mask is {nuc_mask.shape}, Raw is {nuc_raw.shape}. Skipping.")
        continue

    # ==========================================
    # 3. EXTRACT CORE METRICS
    # ==========================================
    print("   -> Extracting base signal and coordinates...")
    
    # --- Nucleus Data ---
    nuc_props = regionprops(nuc_mask, intensity_image=nuc_raw)
    nuc_data = []
    nuc_centroids = {} # Dict for fast distance lookups later
    for p in nuc_props:
        c = p.centroid
        nuc_centroids[p.label] = np.array(c) * VOXEL_SCALING
        nuc_data.append({
            'Cell_ID': p.label,
            'Nuc_Volume': p.area,
            'Nuc_Mean_Intensity': p.intensity_mean,
            'Nuc_Sum_Intensity': p.area * p.intensity_mean,
            'Nuc_Z': c[0], 'Nuc_Y': c[1], 'Nuc_X': c[2]
        })
    df_nuc = pd.DataFrame(nuc_data)

    # --- Cell Data ---
    cell_dict = regionprops_table(cell_mask, intensity_image=raw_multi, 
                                  properties=('label', 'area', 'centroid', 'intensity_mean'))
    df_cell = pd.DataFrame(cell_dict)
    
    df_cell.rename(columns={
        'label': 'Cell_ID', 'area': 'Cell_Volume',
        'centroid-0': 'Cell_Z', 'centroid-1': 'Cell_Y', 'centroid-2': 'Cell_X',
        'intensity_mean-0': 'Cell_Mean_Intensity_Ch1', 'intensity_mean-1': 'Cell_Mean_Intensity_Ch2',
        'intensity_mean-2': 'Cell_Mean_Intensity_Ch3', 'intensity_mean-3': 'Cell_Mean_Intensity_Ch4'
    }, inplace=True)
    
    df_cell['Cell_Total_Intensity_Ch1'] = df_cell['Cell_Volume'] * df_cell['Cell_Mean_Intensity_Ch1']
    df_cell['Cell_Total_Intensity_Ch2'] = df_cell['Cell_Volume'] * df_cell['Cell_Mean_Intensity_Ch2']
    df_cell['Cell_Total_Intensity_Ch3'] = df_cell['Cell_Volume'] * df_cell['Cell_Mean_Intensity_Ch3']
    df_cell['Cell_Total_Intensity_Ch4'] = df_cell['Cell_Volume'] * df_cell['Cell_Mean_Intensity_Ch4']
    
    # Preserve these variables for the spatial math section
    cell_ids_arr = df_cell['Cell_ID'].tolist()
    cell_centroids_arr = list(df_cell[['Cell_Z', 'Cell_Y', 'Cell_X']].values * VOXEL_SCALING)

    # --- Bacteria Data & Host Mapping (Who is inside who?) ---
    bact_dict = regionprops_table(bact_mask, intensity_image=raw_multi, 
                                  properties=('label', 'area', 'centroid', 'intensity_mean'))
    df_bact = pd.DataFrame(bact_dict)
    
    df_bact.rename(columns={
        'label': 'Bact_ID', 'area': 'Bact_Volume',
        'centroid-0': 'Bact_Z', 'centroid-1': 'Bact_Y', 'centroid-2': 'Bact_X',
        'intensity_mean-0': 'Bact_Mean_Intensity_Ch1', 'intensity_mean-1': 'Bact_Mean_Intensity_Ch2',
        'intensity_mean-2': 'Bact_Mean_Intensity_Ch3', 'intensity_mean-3': 'Bact_Mean_Intensity_Ch4'
    }, inplace=True)
    
    if not df_bact.empty:
        df_bact['Bact_Total_Intensity_Ch1'] = df_bact['Bact_Volume'] * df_bact['Bact_Mean_Intensity_Ch1']
        df_bact['Bact_Total_Intensity_Ch2'] = df_bact['Bact_Volume'] * df_bact['Bact_Mean_Intensity_Ch2']
        df_bact['Bact_Total_Intensity_Ch3'] = df_bact['Bact_Volume'] * df_bact['Bact_Mean_Intensity_Ch3']
        df_bact['Bact_Total_Intensity_Ch4'] = df_bact['Bact_Volume'] * df_bact['Bact_Mean_Intensity_Ch4']
        
    bact_centroids_arr = list(df_bact[['Bact_Z', 'Bact_Y', 'Bact_X']].values * VOXEL_SCALING) if not df_bact.empty else []

    if not df_bact.empty:
        # Fast vectorized host mapping using exact center pixel
        z_idx = df_bact['Bact_Z'].round().astype(int).clip(0, cell_mask.shape[0]-1)
        y_idx = df_bact['Bact_Y'].round().astype(int).clip(0, cell_mask.shape[1]-1)
        x_idx = df_bact['Bact_X'].round().astype(int).clip(0, cell_mask.shape[2]-1)
        
        df_bact['Host_Cell_ID'] = cell_mask[z_idx, y_idx, x_idx]
        df_bact['Is_Intracellular'] = df_bact['Host_Cell_ID'] > 0
    else:
        df_bact['Host_Cell_ID'] = pd.Series(dtype=int)
        df_bact['Is_Intracellular'] = pd.Series(dtype=bool)

    # ==========================================
    # 4. INFECTION & SPATIAL MATH (The Cool Stuff)
    # ==========================================
    print("   -> Calculating Spatial Distances...")
    # Generate 3D Map: Distance to nearest cell boundary (for extracellular bacteria)
    binary_cells = (cell_mask > 0)
    dist_to_cell_map = distance_transform_edt(~binary_cells, sampling=VOXEL_SCALING)
    
    # Check if there are actually bacteria in the image
    if len(df_bact) > 0:
        bact_coords = np.array(bact_centroids_arr)
        
        # A. Bact to Closest Nuc (Overall)
        all_nuc_coords = np.array(list(nuc_centroids.values()))
        if len(all_nuc_coords) > 0:
            dist_to_all_nucs = cdist(bact_coords, all_nuc_coords)
            df_bact['Dist_to_Closest_Nuc'] = dist_to_all_nucs.min(axis=1)
        else:
            df_bact['Dist_to_Closest_Nuc'] = np.nan
            
        # B. Bact to ITS OWN Host Nuc
        host_nuc_dists = []
        for _, row in df_bact.iterrows():
            hid = row['Host_Cell_ID']
            if hid > 0 and hid in nuc_centroids:
                # Distance between this bact and its specific host nuc
                dist = np.linalg.norm(np.array([row['Bact_Z'], row['Bact_Y'], row['Bact_X']]) * VOXEL_SCALING - nuc_centroids[hid])
                host_nuc_dists.append(dist)
            else:
                host_nuc_dists.append(np.nan)
        df_bact['Dist_to_Host_Nuc'] = host_nuc_dists

        # C. Bact to Nearest Other Bacterium
        if len(bact_coords) > 1:
            bact_to_bact = cdist(bact_coords, bact_coords)
            np.fill_diagonal(bact_to_bact, np.inf) # Ignore distance to itself (0)
            df_bact['Dist_to_Nearest_Bact'] = bact_to_bact.min(axis=1)
        else:
            df_bact['Dist_to_Nearest_Bact'] = np.nan

        # D. Calculate Bacterial Load (MOI) per Cell
        moi_counts = df_bact[df_bact['Is_Intracellular']].groupby('Host_Cell_ID').size().reset_index(name='Bacterial_Load')
        df_cell = df_cell.merge(moi_counts, left_on='Cell_ID', right_on='Host_Cell_ID', how='left').drop(columns=['Host_Cell_ID'])
        df_cell['Bacterial_Load'] = df_cell['Bacterial_Load'].fillna(0).astype(int)
        df_cell['Is_Infected'] = df_cell['Bacterial_Load'] > 0

        # E. Distance to nearest INFECTED cell
        infected_cells = df_cell[df_cell['Is_Infected']]
        if len(infected_cells) > 0 and len(cell_centroids_arr) > 0:
            infected_coords = np.array([cell_centroids_arr[i] for i, cid in enumerate(cell_ids_arr) if cid in infected_cells['Cell_ID'].values])
            all_cell_coords = np.array(cell_centroids_arr)
            
            cell_to_infected = cdist(all_cell_coords, infected_coords)
            
            # If the cell itself is infected, its distance to an infected cell is 0. 
            # We want distance to the *other* nearest infected cell.
            for i, is_inf in enumerate(df_cell['Is_Infected']):
                if is_inf:
                    # Sort distances, take the second one (index 1), because index 0 is itself
                    dists = np.sort(cell_to_infected[i])
                    df_cell.loc[i, 'Dist_to_Other_Infected_Cell'] = dists[1] if len(dists) > 1 else np.nan
                else:
                    df_cell.loc[i, 'Dist_to_Other_Infected_Cell'] = np.min(cell_to_infected[i])
        else:
             df_cell['Dist_to_Other_Infected_Cell'] = np.nan
        # F. Distance to Nearest Cell & Bacterial Z-Ratio
        dist_to_cell_list = []
        z_ratio_list = []
        
        # Grab bounding boxes to find the absolute top/bottom of each cell
        cell_bboxes = {p.label: p.bbox for p in regionprops(cell_mask)}

        for _, row in df_bact.iterrows():
            # 1. Distance to nearest cell
            bz, by, bx = int(row['Bact_Z']), int(row['Bact_Y']), int(row['Bact_X'])
            dist = dist_to_cell_map[bz, by, bx]
            dist_to_cell_list.append(dist)
            
            # 2. Z-Ratio (Intracellular Polarity)
            hid = row['Host_Cell_ID']
            if hid > 0 and hid in cell_bboxes:
                z_min, _, _, z_max, _, _ = cell_bboxes[hid]
                # Ratio: 0.0 is absolute bottom, 1.0 is absolute top.
                ratio = (row['Bact_Z'] - z_min) / (z_max - z_min) if (z_max - z_min) > 0 else 0.5
                z_ratio_list.append(ratio)
            else:
                z_ratio_list.append(np.nan)
                
        df_bact['Dist_to_Nearest_Cell'] = dist_to_cell_list
        df_bact['Intracellular_Z_Ratio'] = z_ratio_list

    else:
        # Failsafe if image has zero bacteria
        df_cell['Bacterial_Load'] = 0
        df_cell['Is_Infected'] = False
        df_cell['Dist_to_Other_Infected_Cell'] = np.nan

    # Merge Nuc Data into Cell Data
    df_cell_master = df_cell.merge(df_nuc, on='Cell_ID', how='left')

    # ==========================================
    # 5. CILIA CLASSIFICATION & VALIDATION
    # ==========================================
    print("   -> Classifying Cilia (Actin Puncta Logic)...")
    actin_raw = ch4_raw
    cilia_data = []
    
    cell_props = regionprops(cell_mask)
    for p in cell_props:
        cid = p.label
        z_min, y_min, x_min, z_max, y_max, x_max = p.bbox
        
        # Define "Top": Max projection of the top 3 slices of the cell to avoid empty tips
        top_z_start = max(z_min, z_max - 3)
        apical_mask = (cell_mask[top_z_start:z_max, y_min:y_max, x_min:x_max] == cid)
        apical_actin = actin_raw[top_z_start:z_max, y_min:y_max, x_min:x_max]
        
        actin_vals = apical_actin[apical_mask]
        
        # Calculate CV (Coefficient of Variation) = Puncta Score
        if len(actin_vals) > 5: 
            mean_int = np.mean(actin_vals)
            std_int = np.std(actin_vals)
            puncta_score = std_int / mean_int if mean_int > 0 else 0
        else:
            puncta_score = 0
            
        cilia_data.append({
            'Cell_ID': cid,
            'Apical_Actin_Score': puncta_score,
            'bbox': p.bbox,
            'top_z_start': top_z_start,
            'z_max': z_max
        })
        
    df_cilia = pd.DataFrame(cilia_data)
    
    # Run Otsu Thresholding to split populations automatically
    scores = df_cilia['Apical_Actin_Score'].fillna(0).values
    if len(scores) > 1 and np.max(scores) > 0:
        otsu_thresh = threshold_otsu(scores)
    else:
        otsu_thresh = 0.0
        
    df_cilia['Is_Ciliated'] = df_cilia['Apical_Actin_Score'] >= otsu_thresh
    
    # Plot & Save Histogram
    plt.figure(figsize=(8, 5))
    plt.hist(scores, bins=30, color='skyblue', edgecolor='black')
    plt.axvline(otsu_thresh, color='red', linestyle='dashed', linewidth=2, label=f'Threshold: {otsu_thresh:.2f}')
    plt.title(f'Cilia Classification (Actin CV) - {base_name}')
    plt.xlabel('Puncta Score (Coefficient of Variation)')
    plt.ylabel('Cell Count')
    plt.legend()
    plt.savefig(os.path.join(PLOT_DIR, f"{base_name}_Cilia_Histogram.png"), bbox_inches='tight')
    plt.close()

    # Export Cropped TIFs to Validation Folders
    for _, row in df_cilia.iterrows():
        cid = row['Cell_ID']
        z_min, y_min, x_min, z_max, y_max, x_max = row['bbox']
        
        # Max-project the top slices for a clear 2D validation image
        crop = np.max(actin_raw[row['top_z_start']:row['z_max'], y_min:y_max, x_min:x_max], axis=0)
        
        folder = "Ciliated" if row['Is_Ciliated'] else "Non_Ciliated"
        save_path = os.path.join(VAL_DIR, folder, f"{base_name}_Cell_{int(cid)}_score_{row['Apical_Actin_Score']:.2f}.tif")
        
        imsave(save_path, crop.astype(np.uint16), check_contrast=False)

    # Merge final Cilia data into the main cell dataframe
    df_cell_master = df_cell_master.merge(df_cilia[['Cell_ID', 'Apical_Actin_Score', 'Is_Ciliated']], on='Cell_ID', how='left')
    
    # ==========================================
    # 6. SAVE OUTPUTS
    # ==========================================
    cell_out = os.path.join(OUT_DIR, f"{base_name}_Cell_Stats.csv")
    bact_out = os.path.join(OUT_DIR, f"{base_name}_Bacteria_Stats.csv")
    
    df_cell_master.to_csv(cell_out, index=False)
    if len(df_bact) > 0:
        df_bact.to_csv(bact_out, index=False)
        
    elapsed = time.time() - start_time
    print(f"   ✅ Done in {elapsed:.1f}s. Saved Cell and Bacteria Data!")

print("\n🎉 ALL BATCH PROCESSING COMPLETE!")