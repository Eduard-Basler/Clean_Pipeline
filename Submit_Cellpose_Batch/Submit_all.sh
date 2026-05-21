#!/bin/bash

# ==========================================
# 1. SET YOUR TARGETS HERE
# ==========================================
TARGET_SERIES="s1"
TARGET_STATE="Raw"

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
    
    echo "Processing Experiment: $EXPERIMENT | Series: $TARGET_SERIES | State: $TARGET_STATE"

    # ----------------------------------------
    # NUCLEUS (Channel 1)
    # ----------------------------------------
    NUC_FILE=$(eval echo "$INPUT_BASE/$EXPERIMENT/$TARGET_STATE/Channel_1/*_${TARGET_SERIES}_c1.tiff")
    NUC_OUT="$OUTPUT_BASE/$EXPERIMENT/$TARGET_STATE/Channel_1/Series_$NUM"
    
    mkdir -p "$NUC_OUT/CP3_3d" "$NUC_OUT/CP3_Stitch" "$NUC_OUT/CPSAM_3d" "$NUC_OUT/CPSAM_Stitch"
    # Launch pointing directly to their isolated folders
    sbatch Submit_CP3_Cell_3d.sh      "$NUC_FILE" "$NUC_OUT/CP3_3d"
    sbatch Submit_CP3_Cell_Stitch.sh  "$NUC_FILE" "$NUC_OUT/CP3_Stitch"
    sbatch Submit_CPSAM_Cell_3d.sh    "$NUC_FILE" "$NUC_OUT/CPSAM_3d"
    sbatch Submit_CPSAM_Cell_Stitch.sh "$NUC_FILE" "$NUC_OUT/CPSAM_Stitch"


    # ----------------------------------------
    # ACTIN (Channel 4)
    # ----------------------------------------
    ACTIN_FILE=$(eval echo "$INPUT_BASE/$EXPERIMENT/$TARGET_STATE/Channel_4/*_${TARGET_SERIES}_c4.tiff")
    ACTIN_OUT="$OUTPUT_BASE/$EXPERIMENT/$TARGET_STATE/Channel_4/Series_$NUM"
    
    mkdir -p "$ACTIN_OUT/CP3_3d" "$ACTIN_OUT/CP3_Stitch" "$ACTIN_OUT/CPSAM_3d" "$ACTIN_OUT/CPSAM_Stitch"
    # Launch pointing directly to their isolated folders
    sbatch Submit_CP3_Cell_3d.sh      "$ACTIN_FILE" "$ACTIN_OUT/CP3_3d"
    sbatch Submit_CP3_Cell_Stitch.sh   "$ACTIN_FILE" "$ACTIN_OUT/CP3_Stitch"
    sbatch Submit_CPSAM_Cell_3d.sh    "$ACTIN_FILE" "$ACTIN_OUT/CPSAM_3d"
    sbatch Submit_CPSAM_Cell_Stitch.sh "$ACTIN_FILE" "$ACTIN_OUT/CPSAM_Stitch"

done

echo "=== SUBMISSION COMPLETE ==="