import argparse
import os
import pandas as pd
import numpy as np
from collections import defaultdict

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
    args = parser.parse_args()

    print("🚀 Merging isolated parallel metric tables...")
    df_bact = pd.read_csv(args.clean_bact)
    df_cells = pd.read_csv(args.clean_cell)
    
    # Left join all parallel features on unique IDs
    df_bact = df_bact.merge(pd.read_csv(args.overlap_csv), on='Bact_ID', how='left')
    df_bact = df_bact.merge(pd.read_csv(args.distance_csv), on='Bact_ID', how='left', suffixes=('', '_drop'))
    df_bact = df_bact.merge(pd.read_csv(args.classifier_csv), on='Bact_ID', how='left', suffixes=('', '_drop'))
    df_bact = df_bact.merge(pd.read_csv(args.social_csv), on='Bact_ID', how='left', suffixes=('', '_drop'))
    df_bact.drop(columns=[c for c in df_bact.columns if c.endswith('_drop')], inplace=True)

    df_cells = df_cells.merge(pd.read_csv(args.cell_to_cell_csv), on='Cell_ID', how='left')

    base_file_name = os.path.basename(args.clean_bact)
    series_id = base_file_name.split('_')[-1].replace('.csv', '') if '_' in base_file_name else "001"
    df_cells['Series_Position'] = series_id
    df_bact['Series_Position'] = series_id

    # Compute Structural Orientation Angles from SVD principal axes
    angles_deg, alignment_types = [], []
    for _, row in df_bact.iterrows():
        v_str = str(row.get('Body_Vector_SVD', '0;0;1')).split(';')
        v_bact_unit = np.array([float(x) for x in v_str])
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

    # Map relational loads between tables
    cell_in_bact_ids = defaultdict(list)
    cell_out_bact_ids = defaultdict(list)
    updated_not_contested = []
    host_cell_ids = df_bact['Host_Cell_ID'].fillna(0).astype(int).values

    for i, row in df_bact.iterrows():
        bid = int(row['Bact_ID'])
        is_nc_true = str(row['Not_contested']).strip().lower() in ['true', '1', '1.0']
        
        if is_nc_true:
            updated_not_contested.append(str(host_cell_ids[i]))
            if host_cell_ids[i] > 0:
                cell_in_bact_ids[host_cell_ids[i]].append(bid)
        else:
            updated_not_contested.append("FALSE")
            in_cells = str(row.get('Contested_in_Cells_Raw', ''))
            if in_cells and in_cells != 'nan':
                for c in in_cells.split(';'):
                    if c.strip(): cell_in_bact_ids[int(c)].append(bid)

        out_cells = str(row.get('Contested_out_cells', ''))
        if out_cells and out_cells != "nan":
            for c in out_cells.split(';'):
                if c.strip(): cell_out_bact_ids[int(c)].append(bid)

    df_bact['Not_contested'] = updated_not_contested
    df_bact['Contested_in_Cells'] = df_bact['Contested_in_Cells_Raw']

    df_cells['Contested_in_bact'] = df_cells['Cell_ID'].map(lambda x: ";".join(map(str, sorted(set(cell_in_bact_ids[x])))))
    df_cells['Contested_in_number'] = df_cells['Cell_ID'].map(lambda x: len(set(cell_in_bact_ids[x])))
    df_cells['Contested_out_bact'] = df_cells['Cell_ID'].map(lambda x: ";".join(map(str, sorted(set(cell_out_bact_ids[x])))))
    df_cells['Contested_out_number'] = df_cells['Cell_ID'].map(lambda x: len(set(cell_out_bact_ids[x])))

    bact_nc_dict = df_bact.set_index('Bact_ID')['Not_contested'].to_dict()
    df_cells['Intracellular_Bact_Load'] = df_cells['Cell_ID'].map(lambda x: len([b for b in cell_in_bact_ids[x] if bact_nc_dict.get(b, "FALSE") != "FALSE"]))
    df_cells['Adherent_Bact_Load'] = df_cells['Contested_out_number']
    df_cells['Is_Infected'] = df_cells['Intracellular_Bact_Load'] > 0
    df_cells['Is_Adherent'] = df_cells['Adherent_Bact_Load'] > 0

    df_bact.rename(columns={'Bact_Volume_um3': 'Bact_Volume', 'Bact_Center_Z_um': 'Bact_Z', 'Bact_Center_Y_um': 'Bact_Y', 'Bact_Center_X_um': 'Bact_X'}, errors='ignore', inplace=True)
    df_bact['Is_Intracellular'] = (df_bact['Not_contested'].astype(str) != "FALSE") & (df_bact['Host_Cell_ID'] > 0)

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
    df_cells = df_cells.reindex(columns=[c for c in final_cell_cols if c in df_cells.columns])

    final_bact_cols = [
        'Bact_ID', 'Series_Position', 'Bact_Volume', 'Bact_Z', 'Bact_Y', 'Bact_X',
        'Bact_Total_Intensity_Ch1', 'Bact_Total_Intensity_Ch2', 'Bact_Total_Intensity_Ch3', 'Bact_Total_Intensity_Ch4',
        'Bact_Z_Elongation_Ratio', 'Max_Overlap_Cell_ID', 'Max_Overlap_Pct', 'All_Overlaps', 'Host_Cell_ID',
        'Cell_Below_ID', 'Not_contested', 'Contested_in_Cells', 'Contested_in_Total', 'Contested_out_cells', 'Contested_out_Total',
        'Dist_to_Nearest_Bact_um', 'Nearest_Bact_ID', 'Bact_Density_Radius_10um',
        'Bact_Voxel_Min_Dist_to_Membrane_um', 'Bact_Voxel_Max_Dist_to_Membrane_um', 'Bact_Voxel_Mean_Dist_to_Membrane_um'
    ]
    df_bact = df_bact.reindex(columns=[c for c in final_bact_cols if c in df_bact.columns])

    os.makedirs(args.out_dir, exist_ok=True)
    df_bact.to_csv(os.path.join(args.out_dir, "final_bacteria_analysis.csv"), index=False)
    df_cells.to_csv(os.path.join(args.out_dir, "final_cell_analysis.csv"), index=False)
    print("🏁 Pristine Unified Point Cloud Master Datasets Generated!")

if __name__ == "__main__":
    main()