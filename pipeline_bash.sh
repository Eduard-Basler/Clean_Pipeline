#!/bin/bash
# Stop executing immediately if any single command fails
set -e

IMAGE_ID=$1

# Final Storage and Output Folders
FINAL_ND2="$~/Pipeline_Final/Final_Storage/ND2"
FINAL_TIFF="$~/Pipeline_Final/Final_Storage/TIFF"
CELLPOSE_OUT="$~/Pipeline_Final/Output/Cellpose"
OMNIPOSE_OUT="$~/Pipeline_Final/Output/Omnipose"
ANALYSIS_OUT="$~/Pipeline_Final/Output/Analysis"

# Temporary Scratch Workspaces (Isolated by Image ID)
TMP_ND2="$~/Pipeline_Final/Input/ND2/tmp_${IMAGE_ID}"
TMP_TIFF_FULL="$~/Pipeline_Final/Input/TIFF/tmp_${IMAGE_ID}/Full"
TMP_TIFF_SPLIT="$~/Pipeline_Final/Input/TIFF/tmp_${IMAGE_ID}/Split"

mkdir -p "$FINAL_ND2" "$FINAL_TIFF" "$CELLPOSE_OUT" "$OMNIPOSE_OUT" "$ANALYSIS_OUT" "$TMP_ND2" "$TMP_TIFF_FULL" "$TMP_TIFF_SPLIT"

cd "$~/Pipeline_Final/Scripts/Download"
pixi run omero -s omero.biozentrum.unibas.ch -u basler0004 -w Eda30092001@UNI download Image:"$IMAGE_ID" "$TMP_ND2"

FNAME=$(basename "$TMP_ND2"/*.nd2 .nd2)

pixi run bfconvert -compression LZW -bigtiff "$TMP_ND2"/*.nd2 "${TMP_TIFF_FULL}/${FNAME}_Series%s.ome.tif"

pixi run bfconvert -compression LZW -bigtiff "$TMP_ND2"/*.nd2 "${TMP_TIFF_SPLIT}/${FNAME}_Series_%s_Channel_%c.ome.tif"

echo "Splitting done"

cd "$~/Pipeline_Final/Scripts/Cellpose"

for s in {0..4}; do
    # Define variables for exactly what bfconvert outputs
    TARGET_C0="${TMP_TIFF_SPLIT}/${FNAME}_Series_${s}_Channel_0.ome.tif"
    TARGET_C3="${TMP_TIFF_SPLIT}/${FNAME}_Series_${s}_Channel_3.ome.tif"
    
    # Cellpose runs directly on the split channel TIFFs
    pixi run python -m cellpose \
    --image_path "$TARGET_C3" \
    --savedir "$CELLPOSE_OUT" \
    --use_gpu \
    --z_axis 0 \
    --batch_size 64 \
    --diameter 76.271 \
    --flow_threshold -3.742 \
    --cellprob_threshold 0.759 \
    --min_size 23959 \
    --stitch_threshold 0.456 \
    --norm_percentile 1.82 98.53 \
    --save_tif \
    --no_npy \
    --verbose


    pixi run python -m cellpose \
    --image_path "$TARGET_C0" \
    --savedir "$CELLPOSE_OUT" \
    --use_gpu \
    --z_axis 0 \
    --batch_size 64 \
    --diameter 76.271 \
    --flow_threshold -3.742 \
    --cellprob_threshold 0.759 \
    --min_size 23959 \
    --stitch_threshold 0.456 \
    --norm_percentile 1.82 98.53 \
    --save_tif \
    --no_npy \
    --verbose
done

# Omnipose runs ONLY on the folder containing the full 4-channel images
cd "$~/Pipeline_Final/Scripts/Omnipose"
pixi run python Bacterial_seg.py "$TMP_TIFF_FULL" "$OMNIPOSE_OUT"

# Custom Analysis script runs on Omnipose output and the full raw images folder
cd "$~/Pipeline_Final/Scripts/Analysis"
pixi run python script.py "$OMNIPOSE_OUT" "$TMP_TIFF_FULL" "$ANALYSIS_OUT"



# Move everything out to final storage (leaving the scratch folders empty)
mv "$TMP_ND2"/*.nd2 "$FINAL_ND2/"
mv "$TMP_TIFF_FULL"/*.tif "$FINAL_TIFF/"
mv "$TMP_TIFF_SPLIT"/*.tif "$FINAL_TIFF/"

echo "Pipeline complete for Image ID: $IMAGE_ID (Temp directories left empty)"
