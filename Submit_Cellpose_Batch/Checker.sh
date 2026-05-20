#!/bin/bash

BASE_INPUT="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input"
BASE_OUTPUT="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Output"
SCRIPT_DIR="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Submit_Cellpose_Batch"

# Define the file where we will save our commands
OUTPUT_CMD_FILE="${SCRIPT_DIR}/manual_run_list.sh"

# Clear out any old versions and insert a standard bash header
echo "#!/bin/bash" > "$OUTPUT_CMD_FILE"
echo "# Generated on: $(date)" >> "$OUTPUT_CMD_FILE"
echo "# Run individual lines manually to test, or execute the whole file." >> "$OUTPUT_CMD_FILE"
echo "" >> "$OUTPUT_CMD_FILE"

echo "Scanning folders and writing commands to manual_run_list.sh..."

for channel_path in "$BASE_INPUT"/{TIFF,Denoised}/*/Channel_[14]; do
    [ ! -d "$channel_path" ] && continue

    # Native Bash array ensures we only ever evaluate one file at a time
    shopt -s nullglob
    tif_files=("$channel_path"/*.tif*)
    shopt -u nullglob

    [ ${#tif_files[@]} -eq 0 ] && continue
    img_path="${tif_files[0]}"

    CHANNEL_DIR=$(basename "$channel_path")
    EXP_FOLDER=$(basename "$(dirname "$channel_path")")
    VARIANT_DIR=$(basename "$(dirname "$(dirname "$channel_path")")")

    [ "$CHANNEL_DIR" = "Channel_1" ] && TARGET="NUC" || TARGET="Cell"

    for model_type in CP3 CPSAM; do
        for method in 3d Stitch; do
            SLURM_SCRIPT="${SCRIPT_DIR}/Submit_${model_type}_${TARGET}_${method}.sh"
            [ ! -f "$SLURM_SCRIPT" ] && continue
            
            OUT_DIR="${BASE_OUTPUT}/${model_type}_${method}/${VARIANT_DIR}/${EXP_FOLDER}/${CHANNEL_DIR}"
            
            # Print a status note followed by the exact unrolled command string
            echo "echo \"Testing: ${model_type}_${method} on ${EXP_FOLDER} (${CHANNEL_DIR})\"" >> "$OUTPUT_CMD_FILE"
            echo "sbatch \"$SLURM_SCRIPT\" \"$img_path\" \"$OUT_DIR\"" >> "$OUTPUT_CMD_FILE"
            echo "sleep 0.2" >> "$OUTPUT_CMD_FILE"
            echo "" >> "$OUTPUT_CMD_FILE"
        done
    done
done

# Grant execution rights to the file so it's ready to use
chmod +x "$OUTPUT_CMD_FILE"

echo "Done! You can now look at or test individual paths inside manual_run_list.sh"