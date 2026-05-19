#!/bin/bash
#SBATCH --job-name=Batch_Calib_A100
#SBATCH --partition=a100-80g
#SBATCH --qos=a100-30min
#SBATCH --time=00:29:00
#SBATCH --gres=gpu:1
#SBATCH --mem=256G
#SBATCH --output=logs/calib_%j.out
#SBATCH --error=logs/calib_%j.err

# 1. Setup and Environment Check
cd "$SLURM_SUBMIT_DIR" || exit 1
mkdir -p logs

IMAGE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/TIFF/20251212_transwell_sATA1517_24hPI_60xOIL_rep3_/Channel_3/20251212_transwell_sATA1517_24hPI_60xOIL_rep3__s1_c3.tiff"
OUT_BASE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Output/Calibration"
mkdir -p "$OUT_BASE"

pixi run python -m cellpose \
 --image_path "$IMAGE" \
 --savedir "$OUT_PATH" \
 --use_gpu \
 --stitch_threshold 0.5 \
 --z_axis 0 \
 --batch_size 512 \
 --diameter 6 \
 --flow_threshold 0.4 \
 --save_tif \
 --no_npy \
 --verbose \

