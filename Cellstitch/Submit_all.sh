#!/bin/bash

# ==========================================
# 1. SET YOUR TARGETS HERE
# ==========================================
TARGET_SERIES="$1"  #s1
TARGET_STATE="$2"   #"Raw" or "Denoised"

# Set to a specific folder name to test, or "*" to run every single folder
TARGET_EXP="$3"


# ==========================================
# 2. DEFINING TRACKING PATHS
# ==========================================
NUM="${TARGET_SERIES#s}"
INPUT_BASE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Batch_Input"
OUTPUT_BASE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Batch_Output"


# ==========================================
# 3. THE ACTUAL ENGINE
# ==========================================
echo "=== RUNNING SIMPLIFIED LIVE LAUNCH ==="

# Simple loop: expands TARGET_EXP using absolute paths directly
for EXP_PATH in "$INPUT_BASE"/$TARGET_EXP; do
    
    # Extract just the folder name from the absolute path
    EXPERIMENT=$(basename "$EXP_PATH")
    
    echo "Processing Experiment: $EXPERIMENT | Series: $TARGET_SERIES | State: $TARGET_STATE"

    # ----------------------------------------
    # NUCLEUS (Channel 1)
    # ----------------------------------------
    nuc_files=("$INPUT_BASE/$EXPERIMENT/$TARGET_STATE/Channel_1/"*_"${TARGET_SERIES}"_c1.tiff)

    # 2. Assign the first match to your variable (if files exist)
    if [ -e "${nuc_files[0]}" ]; then
        NUC_FILE="${nuc_files[0]}"
    else
        echo "Error: No file found for $TARGET_SERIES in Channel 1"
        exit 1
    fi
    
    NUC_OUT="$OUTPUT_BASE/$EXPERIMENT/$TARGET_STATE/Channel_1/Series_$NUM"

    mkdir -p "$NUC_OUT/cellstitch_CP3" "$NUC_OUT/cellstitch_CPSAM"
    # Launch pointing directly to their isolated folders
    sbatch Submit_cellstitch_CP3_Nuc.sh      "$NUC_FILE" "$NUC_OUT/cellstitch_CP3"
    sbatch Submit_cellstitch_CPSAM_Nuc.sh    "$NUC_FILE" "$NUC_OUT/cellstitch_CPSAM"


    # ----------------------------------------
    # CELL (Channel 4)
    # ----------------------------------------
    cell_files=("$INPUT_BASE/$EXPERIMENT/$TARGET_STATE/Channel_4/"*_"${TARGET_SERIES}"_c4.tiff)

    # 2. Assign the first match to your variable (if files exist)
    if [ -e "${cell_files[0]}" ]; then
        CELL_FILE="${cell_files[0]}"
    else
        echo "Error: No file found for $TARGET_SERIES in Channel 4"
        exit 1
    fi

    CELL_OUT="$OUTPUT_BASE/$EXPERIMENT/$TARGET_STATE/Channel_4/Series_$NUM"
    
    mkdir -p "$CELL_OUT/cellstitch_CP3" "$CELL_OUT/cellstitch_CPSAM"
    # Launch pointing directly to their isolated folders
    sbatch Submit_cellstitch_CP3_Cell.sh      "$CELL_FILE" "$CELL_OUT/cellstitch_CP3"
    sbatch Submit_cellstitch_CPSAM_Cell.sh    "$CELL_FILE" "$CELL_OUT/cellstitch_CPSAM"
    
done

echo "=== SUBMISSION COMPLETE ==="