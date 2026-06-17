#!/bin/bash
#SBATCH --job-name=nd2_split
#SBATCH --partition=scicore
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=logs/split_%j.out
#SBATCH --error=logs/split_%j.err
#SBATCH --qos=6hours

INPUT_FILE=$1
OUTPUT_PATTERN=$2

SCRIPT_DIR="/scicore/home/basler/basler0004/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Downloads"

cd $SCRIPT_DIR

# Pass the input file and output pattern directly to the Python script
pixi run python $SCRIPT_DIR/Python_Split.py "$INPUT_FILE" "$OUTPUT_PATTERN"