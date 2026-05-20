#!/bin/bash

# ==========================================
# 1. SET YOUR TARGETS HERE
# ==========================================
TARGET_SERIES="s1"
TARGET_STATE="Denoised"

# Set to a specific folder name to test, or "*" to run every single folder
TARGET_EXP="20251212_transwell_sATA1946_sATA2044_16hPI_60xOIL_rep2_006"


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
    
    echo "Processing Experiment: $EXPERIMENT"

    # ----------------------------------------
    # NUCLEUS (Channel 1)
    # ----------------------------------------
    NUC_FILE=$(eval echo "$INPUT_BASE/$EXPERIMENT/$TARGET_STATE/Channel_1/*_${TARGET_SERIES}_c1.tiff")
    NUC_OUT="$OUTPUT_BASE/$EXPERIMENT/$TARGET_STATE/Channel_1/Series_$NUM"
    
    mkdir -p "$NUC_OUT"
    sbatch Submit_CP3_Cell_3d.sh "$NUC_FILE" "$NUC_OUT"
    sbatch Submit_CP3_Cell_Stitch.sh "$NUC_FILE" "$NUC_OUT"
    sbatch Submit_CPSAM_Cell_3d.sh "$NUC_FILE" "$NUC_OUT"
    sbatch Submit_CPSAM_Cell_Stitch.sh "$NUC_FILE" "$NUC_OUT"


    # ----------------------------------------
    # ACTIN (Channel 4)
    # ----------------------------------------
    ACTIN_FILE=$(eval echo "$INPUT_BASE/$EXPERIMENT/$TARGET_STATE/Channel_4/*_${TARGET_SERIES}_c4.tiff")
    ACTIN_OUT="$OUTPUT_BASE/$EXPERIMENT/$TARGET_STATE/Channel_4/Series_$NUM"
    
    mkdir -p "$ACTIN_OUT"
    sbatch Submit_CP3_Cell_3d.sh "$ACTIN_FILE" "$ACTIN_OUT"
    sbatch Submit_CP3_Cell_Stitch.sh "$ACTIN_FILE" "$ACTIN_OUT"
    sbatch Submit_CPSAM_Cell_3d.sh   "$ACTIN_FILE" "$ACTIN_OUT"
    sbatch Submit_CPSAM_Cell_Stitch.sh   "$ACTIN_FILE" "$ACTIN_OUT"

done

echo "=== SUBMISSION COMPLETE ==="