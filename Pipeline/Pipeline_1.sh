#!/bin/bash

# Usage: ./run_pipeline.sh <PASSWORD> <IMAGE_ID> [CHANNEL]

PASSWORD=$1
IMAGE_ID=$2
CHANNEL=$3
OUTPUT_DIR="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/ND2"
mkdir -p "$OUTPUT_DIR"

# 1. Download
echo "Downloading Image:$IMAGE_ID..."
cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Downloads
pixi run omero -s omero.biozentrum.unibas.ch -u basler0004 -w "$PASSWORD" download "Image:$IMAGE_ID" "$OUTPUT_DIR"

INPUT_FILE=$(find "$OUTPUT_DIR" -name "*.nd2" | head -n 1)

if [ -z "$INPUT_FILE" ]; then
    echo "Error: Download failed."
    exit 1
fi

# 2. Submit the existing sbatch file
# We pass the arguments to the script by listing them after the sbatch filename
echo "Submitting split job for $INPUT_FILE..."
sbatch submit_split.sh "$INPUT_FILE" "$CHANNEL"

echo "Job submitted."