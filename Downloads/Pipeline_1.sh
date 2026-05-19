#!/bin/bash

# --- Usage ---
# Run this: ./run_pipeline.sh <PASSWORD> <IMAGE_ID> [CHANNEL]
# Note: CHANNEL is now optional. Omit it to split ALL channels.

PASSWORD=$1
IMAGE_ID=$2
CHANNEL=$3
OUTPUT_DIR="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/ND2/"
mkdir -p "$OUTPUT_DIR"

# 1. Download from OMERO
echo "Downloading Image:$IMAGE_ID..."
pixi run omero -s omero.biozentrum.unibas.ch -u basler0004 -w "$PASSWORD" download "Image:$IMAGE_ID" "$OUTPUT_DIR"

# Identify the downloaded file (assuming .nd2 extension)
INPUT_FILE=$(find "$OUTPUT_DIR" -name "*.nd2" | head -n 1)

if [ -z "$INPUT_FILE" ]; then
    echo "Error: Download failed or file not found."
    exit 1
fi

# Define the output pattern
OUT_PATTERN="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/TIFF/Python/Position/{name}/Channel_%c/{name}_s%s_c%c.tiff"

# 2. Build the Python arguments array dynamically
PY_ARGS=()
if [ -n "$CHANNEL" ]; then
    PY_ARGS+=("-channel" "$CHANNEL")
fi
PY_ARGS+=("$INPUT_FILE" "$OUT_PATTERN")

# 3. Submit the Splitter to Slurm
echo "Submitting split job for $INPUT_FILE..."
sbatch <<EOT
#!/bin/bash
#SBATCH --job-name=nd2_split
#SBATCH --partition=scicore
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=logs/split_%j.out
#SBATCH --error=logs/split_%j.err
#SBATCH --qos=6hours

# Run Python with the exact arguments we built
pixi run python Python_Split.py "${PY_ARGS[@]}"
EOT

echo "Done. Check your 'logs/' folder for status."




