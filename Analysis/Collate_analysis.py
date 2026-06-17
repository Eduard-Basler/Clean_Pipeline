import argparse
import os
import pandas as pd
import numpy as np
from collections import defaultdict

def safe_read(csv_path, key):
    """Safely read CSVs, returning an empty DataFrame with the merge key if the file is empty/missing headers."""
    try:
        df = pd.read_csv(csv_path)
        if df.empty or key not in df.columns:
            return pd.DataFrame({key: pd.Series(dtype='int64')})
        return df
    except Exception:
        return pd.DataFrame({key: pd.Series(dtype='int64')})

def extract_ids(raw_val):
    """Bulletproof parser: Safely extracts integers and ignores 'nan', 'None', or blanks."""
    if pd.isna(raw_val):
        return []
    valid_ids = []
    # Replace commas just in case, then split by semicolon
    for val in str(raw_val).replace(',', ';').split(';'):
        val = val.strip().lower()
        if val and val not in ['nan', 'none', 'null', 'na']:
            try:
                valid_ids.append(int(float(val)))
            except (ValueError, TypeError):
                pass
    return valid_ids

def main():
    parser = argparse.ArgumentParser(description="Final Convergence Node: Relational Consolidation Merger")
    parser.add_argument("--clean_bact", required=True)
    parser.add_argument("--clean_cell", required=True)
    parser.add_argument("--overlap_csv", required=True)
    parser.add_argument("--distance_csv", required=True)
    parser.add_argument("--classifier_csv", required=True)
    parser.add_argument("--social_csv", required=True)
    parser.add_argument("--cell_to_cell_csv", required=True)
    parser.add_argument("--out_dir", default=".")
    parser.add_argument("--position_id", required=True, help="Position wildcard string (e.g. s1, s2)")
    args = parser.parse_args()

    print(f"🚀 Merging isolated parallel metric tables for position {args.position_id}...")
    df_bact = safe_read(args.clean_bact, 'Bact_ID')
    df_cells = safe_read(args.clean_cell, 'Cell_ID')
    
    # Left join all parallel features on unique IDs safely
    df_bact = df_bact.merge(safe_read(args.overlap_csv, 'Bact_ID'), on='Bact_ID', how='left')
    df_bact = df_bact.merge(safe_read(args.distance_csv, 'Bact_ID'), on='Bact_ID', how='left', suffixes=('', '_drop'))
    df_bact = df_bact.merge(safe_read(args.classifier_csv, 'Bact_ID'), on='Bact_ID', how='left', suffixes=('', '_drop'))
    df_bact = df_bact.merge(safe_read(args.social_csv, 'Bact_ID'), on='Bact_ID', how='left', suffixes=('', '_drop'))
    df_bact.drop(columns=[c for c in df_bact.columns if c.endswith('_drop')], inplace=True, errors='ignore')

    df_cells = df_cells.merge(safe_read(args.cell_to_cell_csv, 'Cell_ID'), on='Cell_ID', how='left')

    series_id = args.position_id
    
    # Initialize core columns if they don't exist
    if 'Cell_ID' not in df_cells.columns: df_cells['Cell_ID'] = []
    if 'Bact_ID' not in df_bact.columns: df_bact['Bact_ID'] = []
    
    df_cells['Series_Position'] = series_id
    df_bact['Series_Position'] = series_id

    # Compute Structural Orientation Angles from SVD principal axes
    angles_deg, alignment_types = [], []
    for _, row in df_bact.iterrows():
        v_str = str(row.get('Body_Vector_SVD', '0;0;1')).split(';')
        v_bact_unit = np.array([float(x) for x in v_str]) if len(v_str) == 3 else np.array([0.0, 0.0, 1.0])
        v_wall = np.array([row.get('Dist_to_Membrane_um', 0.0), 0.0, 0.0])
        norm_wall = np.linalg.norm(v_wall)
        
        if norm_wall > 0:
            v_wall_unit = v_wall / norm_wall
            dot_product = np.clip(np.abs(np.dot(v_bact_unit, v_wall_unit)), 0.0, 1.0)
            angle_deg = np.degrees(np.arccos(dot_product))
            angles_deg.append(angle_deg)
            alignment_types.append('Perpendicular' if angle_deg <= 30.0 else 'Parallel' if angle_deg >= 60.0 else 'Oblique')
        else:
            angles_deg.append(np.nan)
            alignment_types.append('Unknown')
            
    df_bact['Bact_to_Wall_Angle_Deg'] = angles_deg
    df_bact['Bact_Spatial_Orientation'] = alignment_types

    # Map relational loads safely
    cell_in_bact_ids = defaultdict(list)
    cell_out_bact_ids = defaultdict(list)
    updated_not_contested = []

    for i, row in df_bact.iterrows():
        try:
            bid = int(float(row['Bact_ID']))
        except ValueError:
            continue # Skip invalid bacterium IDs

        # Safely extract Host Cell ID
        host_val = row.get('Host_Cell_ID', 0)
        host_id = int(float(host_val)) if pd.notna(host_val) and str(host_val).strip().lower() not in ['nan', 'none', ''] else 0

        is_nc_true = str(row.get('Not_contested', 'FALSE')).strip().lower() in ['true', '1', '1.0']
        
        if is_nc_true:
            updated_not_contested.append(str(host_id))
            if host_id > 0:
                cell_in_bact_ids[host_id].append(bid)
        else:
            updated_not_contested.append("FALSE")
            # Uses the bulletproof parser
            for c in extract_ids(row.get('Contested_in_Cells_Raw', '')):
                cell_in_bact_ids[c].append(bid)

        # Uses the bulletproof parser
        for c in extract_ids(row.get('Contested_out_cells', '')):
            cell_out_bact_ids[c].append(bid)

    df_bact['Not_contested'] = updated_not_contested
    df_bact['Contested_in_Cells'] = df_bact.get('Contested_in_Cells_Raw', pd.Series(dtype='str'))

    df_cells['Contested_in_bact'] = df_cells['Cell_ID'].map(lambda x: ";".join(map(str, sorted(set(cell_in_bact_ids.get(x, []))))))
    df_cells['Contested_in_number'] = df_cells['Cell_ID'].map(lambda x: len(set(cell_in_bact_ids.get(x, []))))
    df_cells['Contested_out_bact'] = df_cells['Cell_ID'].map(lambda x: ";".join(map(str, sorted(set(cell_out_bact_ids.get(x, []))))))
    df_cells['Contested_out_number'] = df_cells['Cell_ID'].map(lambda x: len(set(cell_out_bact_ids.get(x, []))))

    bact_nc_dict = df_bact.set_index('Bact_ID')['Not_contested'].to_dict() if not df_bact.empty else {}
    
    def count_intracellular(cell_id):
        count = 0
        for b in cell_in_bact_ids.get(cell_id, []):
            if bact_nc_dict.get(b, "FALSE") != "FALSE":
                count += 1
        return count

    df_cells['Intracellular_Bact_Load'] = df_cells['Cell_ID'].map(count_intracellular)
    df_cells['Adherent_Bact_Load'] = df_cells['Contested_out_number']
    df_cells['Is_Infected'] = df_cells['Intracellular_Bact_Load'] > 0
    df_cells['Is_Adherent'] = df_cells['Adherent_Bact_Load'] > 0

    df_bact.rename(columns={'Bact_Volume_um3': 'Bact_Volume', 'Bact_Center_Z_um': 'Bact_Z', 'Bact_Center_Y_um': 'Bact_Y', 'Bact_Center_X_um': 'Bact_X'}, errors='ignore', inplace=True)
    
    if 'Host_Cell_ID' in df_bact.columns:
        df_bact['Is_Intracellular'] = (df_bact['Not_contested'].astype(str) != "FALSE") & (df_bact['Host_Cell_ID'] > 0)
    else:
        df_bact['Is_Intracellular'] = False

    # Reindex columns to target configured schema layouts
    final_cell_cols = [
        'Cell_ID', 'Series_Position', 'Cell_Volume', 'Cell_Z', 'Cell_Y', 'Cell_X',
        'Cell_Total_Intensity_Ch1', 'Cell_Total_Intensity_Ch2', 'Cell_Total_Intensity_Ch3', 'Cell_Total_Intensity_Ch4',
        'Cell_Solidity', 'Cell_Ch4_Top5_Sum', 'Cell_Ch4_Top5_Std', 'Cell_Touching_Border', 'Cell_Elongation', 'Cell_Flatness', 'Cell_3D_Symmetry_Index',
        'Cell_Mean_Distance_to_3_Neighbors', 'Cell_Density_Radius_30um', 'Cell_Circularity', 
        'Intracellular_Bact_Load', 'Adherent_Bact_Load', 'Is_Infected', 'Is_Adherent',
        'Contested_in_bact', 'Contested_in_number', 'Contested_out_bact', 'Contested_out_number',
        'Dist_to_Nearest_Infected_Cell', 'Nearest_Infected_Cell_ID', 'Nuc_Volume', 'Nuc_Z', 'Nuc_Y', 'Nuc_X', 'Nuc_Sum_Intensity'
    ]
    df_cells = df_cells.reindex(columns=final_cell_cols)

    final_bact_cols = [
        'Bact_ID', 'Series_Position', 'Bact_Volume', 'Bact_Z', 'Bact_Y', 'Bact_X',
        'Bact_Total_Intensity_Ch1', 'Bact_Total_Intensity_Ch2', 'Bact_Total_Intensity_Ch3', 'Bact_Total_Intensity_Ch4',
        'Bact_Z_Elongation_Ratio', 'Max_Overlap_Cell_ID', 'Max_Overlap_Pct', 'All_Overlaps', 'Host_Cell_ID',
        'Cell_Below_ID', 'Not_contested', 'Contested_in_Cells', 'Contested_in_Total', 'Contested_out_cells', 'Contested_out_Total',
        'Dist_to_Nearest_Bact_um', 'Nearest_Bact_ID', 'Bact_Density_Radius_10um',
        'Bact_Voxel_Min_Dist_to_Membrane_um', 'Bact_Voxel_Max_Dist_to_Membrane_um', 'Bact_Voxel_Mean_Dist_to_Membrane_um',
        'Bact_to_Wall_Angle_Deg', 'Bact_Spatial_Orientation', 'Is_Intracellular'
    ]
    df_bact = df_bact.reindex(columns=final_bact_cols)

    os.makedirs(args.out_dir, exist_ok=True)
    
    df_cells.to_csv(os.path.join(args.out_dir, f"final_{args.position_id}_cell_analysis.csv"), index=False)
    df_bact.to_csv(os.path.join(args.out_dir, f"final_{args.position_id}_bacteria_analysis.csv"), index=False)
    print(f"🏁 Pristine Unified Point Cloud Master Datasets Generated for Position {args.position_id}!")

if __name__ == "__main__":
    main()