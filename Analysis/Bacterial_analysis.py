import argparse
import os
import pandas as pd
import numpy as np
from tifffile import imread
from skimage.measure import regionprops_table, regionprops
import cupy as cp

SPACING_Z, SPACING_Y, SPACING_X = 0.2, 0.111, 0.111
VOXEL_VOLUME = SPACING_Z * SPACING_Y * SPACING_X

def main():
    parser = argparse.ArgumentParser(description="Upgraded GPU Bacteria Factory")
    parser.add_argument("--bact_mask", required=True)
    parser.add_argument("--c1", required=True)
    parser.add_argument("--c2", required=True)
    parser.add_argument("--c3", required=True)
    parser.add_argument("--c4", required=True)
    parser.add_argument("--out_dir", default=".")
    args = parser.parse_args()

    print("🚀 Running Upgraded GPU Bacteria Factory...")
    bact_mask = imread(args.bact_mask)
    channels = {1: imread(args.c1), 2: imread(args.c2), 3: imread(args.c3), 4: imread(args.c4)}
    img_shape = bact_mask.shape

    # Fast basic CPU table pass
    df_bact = pd.DataFrame(regionprops_table(bact_mask, properties=['label', 'area', 'centroid', 'bbox']))
    df_bact.rename(columns={
        'label': 'Bact_ID', 'area': 'Bact_Volume_Voxels',
        'centroid-0': 'Bact_Center_Z_voxels', 'centroid-1': 'Bact_Center_Y_voxels', 'centroid-2': 'Bact_Center_X_voxels'
    }, inplace=True)

    df_bact['Bact_Volume_um3'] = df_bact['Bact_Volume_Voxels'] * VOXEL_VOLUME
    df_bact['Bact_Center_Z_um'] = df_bact['Bact_Center_Z_voxels'] * SPACING_Z
    df_bact['Bact_Center_Y_um'] = df_bact['Bact_Center_Y_voxels'] * SPACING_Y
    df_bact['Bact_Center_X_um'] = df_bact['Bact_Center_X_voxels'] * SPACING_X

    # Calculate standard intensities via fast regionprops
    for ch in [1, 2, 3, 4]:
        ch_table = pd.DataFrame(regionprops_table(bact_mask, channels[ch], properties=['label', 'intensity_mean', 'intensity_std']))
        df_bact[f'Bact_Mean_Intensity_Ch{ch}'] = df_bact['Bact_ID'].map(ch_table.set_index('label')['intensity_mean']).fillna(0.0)
        df_bact[f'Bact_Total_Intensity_Ch{ch}'] = df_bact[f'Bact_Mean_Intensity_Ch{ch}'] * df_bact['Bact_Volume_Voxels']
        df_bact[f'Bact_Std_Intensity_Ch{ch}'] = df_bact['Bact_ID'].map(ch_table.set_index('label')['intensity_std']).fillna(0.0)

    # Fast local background extraction loop using cropped boxes
    print("  -> Extracting localized background auras and corrected signals...")
    bg_means = {ch: {} for ch in [1, 2, 3, 4]}
    z_elongation_ratios = {}

    for prop in regionprops(bact_mask):
        bid = prop.label
        z_min, y_min, x_min, z_max, y_max, x_max = prop.bbox
        
        # Calculate Z Elongation Ratio
        z_span = (z_max - z_min) * SPACING_Z
        y_span = (max(1, y_max - y_min)) * SPACING_Y
        z_elongation_ratios[bid] = z_span / y_span

        # Create localized expansion box for background aura calculation (+3 pixels out)
        pad_z_min, pad_z_max = max(0, z_min - 2), min(img_shape[0], z_max + 2)
        pad_y_min, pad_y_max = max(0, y_min - 3), min(img_shape[1], y_max + 3)
        pad_x_min, pad_x_max = max(0, x_min - 3), min(img_shape[2], x_max + 3)

        local_mask = bact_mask[pad_z_min:pad_z_max, pad_y_min:pad_y_max, pad_x_min:pad_x_max]
        bg_zone_mask = (local_mask == 0) # Background is where no labels exist

        if np.any(bg_zone_mask):
            for ch in [1, 2, 3, 4]:
                ch_crop = channels[ch][pad_z_min:pad_z_max, pad_y_min:pad_y_max, pad_x_min:pad_x_max]
                bg_means[ch][bid] = float(np.mean(ch_crop[bg_zone_mask]))
        else:
            for ch in [1, 2, 3, 4]: bg_means[ch][bid] = 0.0

    df_bact['Bact_Z_Elongation_Ratio'] = df_bact['Bact_ID'].map(z_elongation_ratios)
    for ch in [1, 2, 3, 4]:
        df_bact[f'Local_Bg_Mean_Ch{ch}'] = df_bact['Bact_ID'].map(bg_means[ch]).fillna(0.0)
        df_bact[f'Bact_Corrected_Mean_Ch{ch}'] = np.maximum(0, df_bact[f'Bact_Mean_Intensity_Ch{ch}'] - df_bact[f'Local_Bg_Mean_Ch{ch}'])

    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, "clean_bacteria_stats.csv")
    df_bact.to_csv(out_path, index=False)
    print(f"🎉 Bacteria Factory Complete! Saved to: {out_path}")

if __name__ == "__main__":
    main()