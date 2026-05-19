#!/bin/bash

CHANNEL=$1
INPUT_BASE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/TIFF"

mkdir -p logs

for FILEPATH in "${INPUT_BASE}"/*; do
    if [ -d "$FILEPATH" ]; then
        IMAGE_NAME=$(basename "$FILEPATH")
        
        echo "Submitting job for: ${IMAGE_NAME} -> ${CHANNEL}"
        sbatch Submit_cellpose_SAM.sh "$IMAGE_NAME" "$CHANNEL"
    fi
done