#!/bin/bash

# Define absolute paths
BASE_INPUT="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input"
BASE_OUTPUT="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Output"
SCRIPT_DIR="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Submit_Cellpose_Batch"

# Move into the script directory so logs save to the right place
cd "$SCRIPT_DIR" || exit 1
mkdir -p logs

# Loop through both variants (TIFF and Denoised)
for variant in TIFF Denoised; do
    INPUT_DIR="${BASE_INPUT}/${variant}"
    
    if [ -d "$INPUT_DIR" ]; then
        echo "Processing folder variant: $variant..."
        
        # 1. Loop through EVERY individual experiment folder
        for EXP_FOLDER in "$INPUT_DIR"/*; do
            [ ! -d "$EXP_FOLDER" ] && continue # Skip files, only process directories
            
            # 2. Grab exactly ONE image from Channel_1 and ONE from Channel_4, strictly stripping newlines
            img_path_c1=$(find "$EXP_FOLDER/Channel_1" -type f -name "*.tif*" 2>/dev/null | head -n 1 | tr -d '\r\n')
            img_path_c4=$(find "$EXP_FOLDER/Channel_4" -type f -name "*.tif*" 2>/dev/null | head -n 1 | tr -d '\r\n')
            
            # 3. Feed these two selected images into your segmentation loop
            for img_path in "$img_path_c1" "$img_path_c4"; do
                [ -z "$img_path" ] && continue # Skip if a channel was missing/empty
                [ ! -f "$img_path" ] && continue # Defensive double-check that the file physically exists
                
                # Extract parent channel folder name
                CHANNEL_DIR=$(basename "$(dirname "$img_path")")
                
                # Map Channel_1 to Nuclei and Channel_4 to Cells
                if [ "$CHANNEL_DIR" = "Channel_1" ]; then
                    TARGET="NUC"
                elif [ "$CHANNEL_DIR" = "Channel_4" ]; then
                    TARGET="Cell"
                else
                    continue # Skip other channels
                fi
                
                # Extract just the folder structure after the variant
                RELATIVE_PATH="${img_path#$INPUT_DIR/}"
                SUB_DIR_STRUCTURE="$(dirname "$RELATIVE_PATH")"
                
                # Loop through both models and methods
                for model_type in CP3 CPSAM; do
                    for method in 3d Stitch; do
                        
                        SLURM_SCRIPT="${SCRIPT_DIR}/Submit_${model_type}_${TARGET}_${method}.sh"
                        
                        if [ -f "$SLURM_SCRIPT" ]; then
                            
                            # Build output path to prevent overwriting
                            OUT_DIR="${BASE_OUTPUT}/${model_type}_${method}/${variant}/${SUB_DIR_STRUCTURE}"
                            
                            # Create the directory synchronously here to prevent race conditions
                            mkdir -p "$OUT_DIR"
                            
                            echo "Submitting: $variant | $(basename "$EXP_FOLDER") | $CHANNEL_DIR | ${model_type}_${method}"
                            
                            # Launch sbatch and pass args as $1 and $2
                            sbatch "$SLURM_SCRIPT" "$img_path" "$OUT_DIR"
                            
                            # Throttle submissions to protect the SLURM controller
                            sleep 0.2
                            
                        else
                            echo "Warning: Script not found -> $SLURM_SCRIPT"
                        fi
                        
                    done
                done
            done
        done
    fi
done

echo "All representative test jobs successfully submitted!"