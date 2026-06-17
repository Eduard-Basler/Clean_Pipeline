#!/bin/bash
#SBATCH --job-name=N2V2_Predict
#SBATCH --partition=a100            
#SBATCH --qos=a100-30min           
#SBATCH --time=00:30:00             
#SBATCH --gres=gpu:1                
#SBATCH --mem=64G                   
#SBATCH --cpus-per-task=4   
#SBATCH --output=logs/denoise_%j.out
#SBATCH --error=logs/denoise_%j.err        

RAW_CH_DIR=$1
OUT_CH_DIR=$2
CKPT=$3

SCRIPT_DIR="/scicore/home/basler/basler0004/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/CAREamics"
cd "$SCRIPT_DIR"

mkdir -p "$OUT_CH_DIR"

# Loop through the TIFFs in this specific channel
for FILE in "$RAW_CH_DIR"/*.tif*; do
    [ -e "$FILE" ] || continue
    echo "Denoising $FILE..."
    
    pixi run python Denoise.py \
        --predict_source "$FILE" \
        --checkpoint "$CKPT" \
        --output_dir "$OUT_CH_DIR"
done