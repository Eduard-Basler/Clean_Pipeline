#!/bin/bash
#SBATCH --job-name=Batch_Calib_A100
#SBATCH --partition=a100-80g
#SBATCH --qos=a100-30min
#SBATCH --time=00:29:00
#SBATCH --gres=gpu:1
#SBATCH --mem=200G
#SBATCH --cpus-per-task=4 
#SBATCH --output=logs/calib_SAM_%j.out
#SBATCH --error=logs/calib_SAM_%j.err

# 1. Setup and Environment Check
cd "$SLURM_SUBMIT_DIR" || exit 1

IMAGE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/TIFF/20251212_transwell_sATA1517_24hPI_60xOIL_rep3_/Channel_1/20251212_transwell_sATA1517_24hPI_60xOIL_rep3__s1_c1.tiff"
OUT_PATH="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Output/Calibration"
mkdir -p "$OUT_BASE"

pixi run python -m cellpose \
 --image_path "$IMAGE" \
 --savedir "$OUT_PATH" \
	  --use_gpu \
	  --z_axis 0 \
	  --do_3D \
	  --batch_size 500 \
	  --diameter 76.271 \
	  --cellprob_threshold -5.404 \
	  --anisotropy 2.786 \
	  --flow3D_smooth 0.69 0.69 0.69 \
	  --save_tif \
      --no_npy \
      --verbose
