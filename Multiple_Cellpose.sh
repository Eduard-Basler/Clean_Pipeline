#!/bin/bash

# ==============================================================================
# 1. CONFIGURATION (Edit these paths and variables)
# ==============================================================================

# Base Paths
INPUT_BASE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/TIFF"
OUTPUT_BASE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Output"

# Script Directories
SCRIPT_DIR_CP3="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_3_TITAN"
SCRIPT_DIR_SAM="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_SAM_TITAN"

# SBATCH Scripts per Model and Target
CP3_SCRIPT_NUC="$SCRIPT_DIR_CP3/Submit_cellpose_3_Nuclei.sh"
SAM_SCRIPT_NUC="$SCRIPT_DIR_SAM/Submit_cellpose_SAM_Nuc.sh"

CP3_SCRIPT_BACT="$SCRIPT_DIR_CP3/Submit_cellpose_3_Bact.sh"
SAM_SCRIPT_BACT="$SCRIPT_DIR_SAM/Submit_cellpose_SAM_Bact.sh"

CP3_SCRIPT_CYTO="$SCRIPT_DIR_CP3/Submit_cellpose_3_Cyto.sh"
SAM_SCRIPT_CYTO="$SCRIPT_DIR_SAM/Submit_cellpose_SAM_Cyto.sh"

# Hyperparameters format: "BATCH_SIZE DIAMETER FLOW CELLPROB STITCH"

# Channel 1 (Nuclei)
CP3_PARAMS_CH1="64 60 -3.742 0.759 0.456"
SAM_PARAMS_CH1="64 60 -3.742 0.759 0.456"

# Channel 2 (Bacteria 1)
CP3_PARAMS_CH2="128 6 0.4 -1.0 0.5"
SAM_PARAMS_CH2="32 6 0.4 -1.0 0.5"

# Channel 3 (Bacteria 2)
CP3_PARAMS_CH3="128 6 0.4 -1.0 0.5"
SAM_PARAMS_CH3="32 6 0.4 -1.0 0.5"

# Channel 4 (Cyto)
CP3_PARAMS_CH4="64 76.271 -3.742 0.759 0.456"
SAM_PARAMS_CH4="128 76.271 -3.742 0.759 0.456"

# ==============================================================================
# 2. MAIN LOOP
# ==============================================================================

for FOLDER_PATH in "$INPUT_BASE"/*; do
    
    if [ ! -d "$FOLDER_PATH" ]; then continue; fi
    FOLDER_NAME=$(basename "$FOLDER_PATH")
    SATA_COUNT=$(echo "$FOLDER_NAME" | grep -o "sATA" | wc -l)
    
    echo "Processing Folder: $FOLDER_NAME (sATA count: $SATA_COUNT)"

    for s in {1..5}; do
        
        # ---------------------------------------------------------
        # CHANNEL 1 (Nuclei)
        # ---------------------------------------------------------
        IN_C1="$FOLDER_PATH/Channel_1/${FOLDER_NAME}_s${s}_c1.tiff"
        OUT_CP3_C1="$OUTPUT_BASE/Cellpose_3_RAW/$FOLDER_NAME/Channel_1/"
        OUT_SAM_C1="$OUTPUT_BASE/Cellpose_SAM_RAW/$FOLDER_NAME/Channel_1/"
        
        mkdir -p "$OUT_CP3_C1" "$OUT_SAM_C1"
        sbatch "$CP3_SCRIPT_NUC" "$IN_C1" "$OUT_CP3_C1" $CP3_PARAMS_CH1
        sbatch "$SAM_SCRIPT_NUC" "$IN_C1" "$OUT_SAM_C1" $SAM_PARAMS_CH1

        # ---------------------------------------------------------
        # CHANNELS 2 & 3 (Bacteria)
        # ---------------------------------------------------------
        if [ "$SATA_COUNT" -ge 2 ]; then
            # Channel 2
            IN_C2="$FOLDER_PATH/Channel_2/${FOLDER_NAME}_s${s}_c2.tiff"
            OUT_CP3_C2="$OUTPUT_BASE/Cellpose_3_RAW/$FOLDER_NAME/Channel_2/"
            OUT_SAM_C2="$OUTPUT_BASE/Cellpose_SAM_RAW/$FOLDER_NAME/Channel_2/"
            
            mkdir -p "$OUT_CP3_C2" "$OUT_SAM_C2"
            sbatch "$CP3_SCRIPT_BACT" "$IN_C2" "$OUT_CP3_C2" $CP3_PARAMS_CH2
            sbatch "$SAM_SCRIPT_BACT" "$IN_C2" "$OUT_SAM_C2" $SAM_PARAMS_CH2

            # Channel 3
            IN_C3="$FOLDER_PATH/Channel_3/${FOLDER_NAME}_s${s}_c3.tiff"
            OUT_CP3_C3="$OUTPUT_BASE/Cellpose_3_RAW/$FOLDER_NAME/Channel_3/"
            OUT_SAM_C3="$OUTPUT_BASE/Cellpose_SAM_RAW/$FOLDER_NAME/Channel_3/"
            
            mkdir -p "$OUT_CP3_C3" "$OUT_SAM_C3"
            sbatch "$CP3_SCRIPT_BACT" "$IN_C3" "$OUT_CP3_C3" $CP3_PARAMS_CH3
            sbatch "$SAM_SCRIPT_BACT" "$IN_C3" "$OUT_SAM_C3" $SAM_PARAMS_CH3

        else
            # Skip Channel 2, segment ONLY Channel 3
            IN_C3="$FOLDER_PATH/Channel_3/${FOLDER_NAME}_s${s}_c3.tiff"
            OUT_CP3_C3="$OUTPUT_BASE/Cellpose_3_RAW/$FOLDER_NAME/Channel_3/"
            OUT_SAM_C3="$OUTPUT_BASE/Cellpose_SAM_RAW/$FOLDER_NAME/Channel_3/"
            
            mkdir -p "$OUT_CP3_C3" "$OUT_SAM_C3"
            sbatch "$CP3_SCRIPT_BACT" "$IN_C3" "$OUT_CP3_C3" $CP3_PARAMS_CH3
            sbatch "$SAM_SCRIPT_BACT" "$IN_C3" "$OUT_SAM_C3" $SAM_PARAMS_CH3
        fi

        # ---------------------------------------------------------
        # CHANNEL 4 (Cytoplasm)
        # ---------------------------------------------------------
        IN_C4="$FOLDER_PATH/Channel_4/${FOLDER_NAME}_s${s}_c4.tiff"
        OUT_CP3_C4="$OUTPUT_BASE/Cellpose_3_RAW/$FOLDER_NAME/Channel_4/"
        OUT_SAM_C4="$OUTPUT_BASE/Cellpose_SAM_RAW/$FOLDER_NAME/Channel_4/"
        
        mkdir -p "$OUT_CP3_C4" "$OUT_SAM_C4"
        sbatch "$CP3_SCRIPT_CYTO" "$IN_C4" "$OUT_CP3_C4" $CP3_PARAMS_CH4
        sbatch "$SAM_SCRIPT_CYTO" "$IN_C4" "$OUT_SAM_C4" $SAM_PARAMS_CH4

    done
done

echo "All jobs submitted!"