#!/bin/bash
#SBATCH --job-name=nd2_split
#SBATCH --partition=scicore          # Standard CPU partition on sciCORE
#SBATCH --cpus-per-task=2            # CPU cores allocated per task
#SBATCH --mem=32G                    # Memory allocation (32 GB for large ND2 files)
#SBATCH --time=01:00:00              # Walltime limit (HH:MM:SS)
#SBATCH --output=logs/split_%j.out   # Standard output log (%j becomes the Job ID)
#SBATCH --error=logs/split_%j.err    # Standard error log
#SBATCH --qos=6hours                 # Standard CPU QoS matching your time limit

# Grab arguments from the terminal loop
INPUT_FILE=$1
CHANNEL=$2

# Run command with the dynamic channel
pixi run python Python_Split.py -channel "$CHANNEL" \
  "$INPUT_FILE" \
  "$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/TIFF/Python/Position/{name}/Channel_%c/{name}_s%s_c%c.tiff"
