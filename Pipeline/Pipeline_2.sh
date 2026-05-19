#!/bin/bash

FOLDER_PATH="$1"
FOLDER_PATH=$(realpath "$FOLDER_PATH")
INPUT_BASE=$(dirname "$FOLDER_PATH") # The parent container

OUTPUT_BASE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/Denoised"
MODEL_DIR="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Models"
DENOISE_SCRIPT="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/CAREamics/Submit_Denoise.sh"

FOLDER_NAME=$(basename "$FOLDER_PATH")

SATA_COUNT=$(echo "$FOLDER_NAME" | grep -o "sATA" | wc -l)
SATA_COUNT=${SATA_COUNT:-0}

echo "Processing Folder: $FOLDER_NAME (sATA count: $SATA_COUNT)"

for CH in 1 2 3 4; do
    if [ "$CH" -eq 2 ] && [ "$SATA_COUNT" -lt 2 ]; then continue; fi

    CH_DIR="$FOLDER_PATH/Channel_$CH"
    MODEL="$MODEL_DIR/N2V2_Channel_${CH}_last.ckpt"
    OUT_DIR="$OUTPUT_BASE/$FOLDER_NAME/Channel_$CH"
    
    # Check if the folder exists
    if [ -d "$CH_DIR" ]; then
        mkdir -p "$OUT_DIR"
        
        # SUB-LOOP: Find every .tiff file and submit a job for each
        for FILE in "$CH_DIR"/*.tif*; do
            [ -e "$FILE" ] || continue
            sbatch "$DENOISE_SCRIPT" "$FILE" "$MODEL" "$OUT_DIR"
        done
    fi
done

echo "All jobs for $FOLDER_NAME submitted!"