import argparse
import os
import pandas as pd
import numpy as np
from tifffile import imread
from skimage.measure import regionprops_table

def main():
    parser = argparse.ArgumentParser(description="Independent Step A: Pixel Overlap Linker")
    parser.add_argument("--bact_mask", required=True)
    parser.add_argument("--cell_mask", required=True)
    parser.add_argument("--out_dir", default=".")
    args = parser.parse_args()

    cell_mask = imread(args.cell_mask)
    bact_mask = imread(args.bact_mask)

    # Re-generate base Bact_ID list independently from scratch
    props = regionprops_table(bact_mask, properties=['label'])
    df_bact = pd.DataFrame(props).rename(columns={'label': 'Bact_ID'})

    flat_cell = cell_mask.ravel()
    flat_bact = bact_mask.ravel()

    overlap_mask = (flat_bact > 0) & (flat_cell > 0)
    overlap_bact = flat_bact[overlap_mask]
    overlap_cell = flat_cell[overlap_mask]

    bact_counts = np.bincount(flat_bact)

    max_overlap_ids = {}
    max_overlap_pcts = {}
    all_overlaps_strings = {}
    is_shared_border_conflict = {}

    if len(overlap_bact) > 0:
        df_counts = pd.DataFrame({'Bact_ID': overlap_bact, 'Cell_ID': overlap_cell})
        df_grouped = df_counts.groupby(['Bact_ID', 'Cell_ID']).size().reset_index(name='Overlap_Voxels')
        
        for bid, group in df_grouped.groupby('Bact_ID'):
            total_bact_voxels = bact_counts[int(bid)]
            sorted_group = group.sort_values('Overlap_Voxels', ascending=False)
            top_match = sorted_group.iloc[0]
            
            max_overlap_ids[bid] = int(top_match['Cell_ID'])
            max_overlap_pcts[bid] = float((top_match['Overlap_Voxels'] / total_bact_voxels) * 100.0)
            all_overlaps_strings[bid] = ";".join([f"{int(r['Cell_ID'])}:{((r['Overlap_Voxels']/total_bact_voxels)*100.0).round(1)}" for _, r in sorted_group.iterrows()])
            is_shared_border_conflict[bid] = len(sorted_group) >= 2

    df_bact['Max_Overlap_Cell_ID'] = df_bact['Bact_ID'].map(max_overlap_ids).fillna(0).astype(int)
    df_bact['Max_Overlap_Pct'] = df_bact['Bact_ID'].map(max_overlap_pcts).fillna(0.0)
    df_bact['All_Overlaps'] = df_bact['Bact_ID'].map(all_overlaps_strings).fillna("")
    df_bact['Is_Shared_Border_Conflict'] = df_bact['Bact_ID'].map(is_shared_border_conflict).fillna(False).astype(bool)
    df_bact['Pct_Background'] = 100.0 - df_bact['Max_Overlap_Pct']
    df_bact['Host_Cell_ID'] = df_bact['Max_Overlap_Cell_ID']

    os.makedirs(args.out_dir, exist_ok=True)
    df_bact.to_csv(os.path.join(args.out_dir, "stepA_isolated_output.csv"), index=False)

if __name__ == "__main__":
    main()