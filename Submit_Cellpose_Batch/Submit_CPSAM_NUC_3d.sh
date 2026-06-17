#!/bin/bash
#SBATCH --job-name=cp_SAM_C3
#SBATCH --partition=a100-80g
#SBATCH --qos=a100-30min
#SBATCH --time=00:30:00
#SBATCH --gres=gpu:1
#SBATCH --mem=120G
#SBATCH --cpus-per-task=4 
#SBATCH --output=logs/cp_SAM_N3/%j.out
#SBATCH --error=logs/cp_SAM_N3/%j.err

# 1. Setup and Environment Check
cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_SAM

echo "CPSAM NUC 3D"

IMAGE=$1
OUT_PATH=$2


pixi run python -m cellpose \
	--image_path "$IMAGE" \
	--savedir "$OUT_PATH" \
	--use_gpu \
	--do_3D \
	--diameter 50 \
	--flow_threshold -3.742 \
	--cellprob_threshold -3.16 \
	--anisotropy 2.43 \
	--flow3D_smooth 1.74 \
	--save_tif \
	--batch_size 350 \
	--no_npy \
	--verbose
