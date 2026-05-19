#!/bin/bash

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================

# Target Image
TARGET_IMAGE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/TIFF/20251212_transwell_sATA1517_24hPI_60xOIL_rep3_/Channel_3/20251212_transwell_sATA1517_24hPI_60xOIL_rep3__s1_c3.tiff"

# Base Output Directories
OUT_BASE_CP3="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Output/Parameter_Sweep/Cellpose_3"
OUT_BASE_SAM="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Output/Parameter_Sweep/Cellpose_SAM"

# Script Locations (Corrected Filenames)
CP3_SCRIPT="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_3_TITAN/Submit_cellpose_3_Bact.sh"

# Set independent batch sizes based on expected VRAM limits
BATCH_SIZE_CP3="128"
BATCH_SIZE_SAM="32"  # Lowered for SAM to prevent OOM errors

# Script Locations (Corrected Filenames)
CP3_SCRIPT="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_3_TITAN/Sweep_cellpose_3_Bact.sh"
SAM_SCRIPT="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_SAM_TITAN/Sweep_cellpose_SAM_Bact.sh"


# Define lists of values you want to test (separated by spaces)
DIAMETERS=(6 10)
FLOWS=(0.4 0.6 0.8 1.0)
CELLPROBS=(-2.0 -1.0 -0.5 0.0 1.0)
STITCHES=(0.5)

# ==============================================================================
# 3. AUTOMATED COMBINATORIAL SWEEP
# ==============================================================================
echo "Starting automated combinatorial sweep with distinct batch sizes..."

# Loop through every combination automatically
for diam in "${DIAMETERS[@]}"; do
    for flow in "${FLOWS[@]}"; do
        for prob in "${CELLPROBS[@]}"; do
            for stitch in "${STITCHES[@]}"; do
                
                # Reconstruct the exact string format, but separate them per model
                PARAM_STRING_CP3="$BATCH_SIZE_CP3 $diam $flow $prob $stitch"
                PARAM_STRING_SAM="$BATCH_SIZE_SAM $diam $flow $prob $stitch"
                
                echo "Submitting CP3: $PARAM_STRING_CP3 | SAM: $PARAM_STRING_SAM"
                
                # Fire off both models simultaneously using their specific parameters
                sbatch "$CP3_SCRIPT" "$TARGET_IMAGE" "$OUT_BASE_CP3" $PARAM_STRING_CP3
                sbatch "$SAM_SCRIPT" "$TARGET_IMAGE" "$OUT_BASE_SAM" $PARAM_STRING_SAM
                
            done
        done
    done
done

echo "All combinatorial jobs submitted!"