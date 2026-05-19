#!/bin/bash

# ==============================================================================
# PATH CONFIGURATION (Matches your master script)
# ==============================================================================
TARGET_IMAGE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/TIFF/20251212_transwell_sATA1946_sATA2044_16hPI_60xOIL_rep2_006/Channel_3/20251212_transwell_sATA1946_sATA2044_16hPI_60xOIL_rep2_006_s1_c3.tiff"

OUT_BASE_CP3="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Output/Parameter_Sweep/Cellpose_3"
OUT_BASE_SAM="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Output/Parameter_Sweep/Cellpose_SAM"

CP3_SCRIPT="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_3_TITAN/Sweep_cellpose_3_Bact.sh"
SAM_SCRIPT="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_SAM_TITAN/Sweep_cellpose_SAM_Bact.sh"

# Extract script directories to check if they exist for logs
CP3_DIR=$(dirname "$CP3_SCRIPT")
SAM_DIR=$(dirname "$SAM_SCRIPT")

# ==============================================================================
# VALIDATION LOGIC
# ==============================================================================
ERRORS=0

echo "========================================="
echo "   RUNNING PATH VALIDATION FOR SWEEP     "
echo "========================================="

# 1. Test Input Image
echo -n "Checking Input Image... "
if [ -f "$TARGET_IMAGE" ]; then
    echo "✅ FOUND"
else
    echo "❌ NOT FOUND!"
    echo "   Path: $TARGET_IMAGE"
    ((ERRORS++))
fi

# 2. Test SBATCH Scripts
echo -n "Checking Cellpose 3 Script... "
if [ -f "$CP3_SCRIPT" ]; then
    echo "✅ FOUND"
else
    echo "❌ NOT FOUND!"
    echo "   Path: $CP3_SCRIPT"
    ((ERRORS++))
fi

echo -n "Checking Cellpose SAM Script... "
if [ -f "$SAM_SCRIPT" ]; then
    echo "✅ FOUND"
else
    echo "❌ NOT FOUND!"
    echo "   Path: $SAM_SCRIPT"
    ((ERRORS++))
fi

# 3. Test/Warn Output Base Directories (they will be created via mkdir -p, but good to check permissions)
echo -n "Checking Parent of CP3 Output... "
if [ -d "$(dirname "$OUT_BASE_CP3")" ]; then
    echo "✅ WRITABLE (Parent directory exists)"
else
    echo "⚠️  WARNING: Parent folder structure doesn't exist yet (mkdir -p will attempt to create it)"
fi

echo -n "Checking Parent of SAM Output... "
if [ -d "$(dirname "$OUT_BASE_SAM")" ]; then
    echo "✅ WRITABLE (Parent directory exists)"
else
    echo "⚠️  WARNING: Parent folder structure doesn't exist yet (mkdir -p will attempt to create it)"
fi

# 4. Check Slurm Log Directories (Crucial Fix)
echo -n "Checking CP3 Slurm logs directory... "
if [ -d "$CP3_DIR/logs" ]; then
    echo "✅ EXISTS"
else
    echo "❌ MISSING! Slurm will crash instantly."
    echo "   Required directory: $CP3_DIR/logs"
    ((ERRORS++))
fi

echo -n "Checking SAM Slurm logs directory... "
if [ -d "$SAM_DIR/logs" ]; then
    echo "✅ EXISTS"
else
    echo "❌ MISSING! Slurm will crash instantly."
    echo "   Required directory: $SAM_DIR/logs"
    ((ERRORS++))
fi

# ==============================================================================
# CONCLUSION
# ==============================================================================
echo "========================================="
if [ $ERRORS -eq 0 ]; then
    echo "🎉 SUCCESS: All vital paths are perfectly aligned! You are safe to submit."
    exit 0
else
    echo "🛑 FAILURE: found $ERRORS path error(s). Fix them before running the master script."
    exit 1
fi