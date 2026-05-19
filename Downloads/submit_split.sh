#!/bin/bash
#SBATCH --job-name=nd2_split
#SBATCH --partition=scicore
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=logs/split_%j.out
#SBATCH --error=logs/split_%j.err
#SBATCH --qos=6hours

# The arguments passed via sbatch go here:
INPUT_FILE=$1
CHANNEL=$2

# Construct the command
if [ -n "$CHANNEL" ]; then
    pixi run python Python_Split.py -channel "$CHANNEL" "$INPUT_FILE" "$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/TIFF/{name}/Channel_%c/{name}_s%s_c%c.tiff"
else
    pixi run python Python_Split.py "$INPUT_FILE" "$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/TIFF/{name}/Channel_%c/{name}_s%s_c%c.tiff"
fi