#!/bin/bash
#SBATCH --job-name=Batch_Calib_A100
#SBATCH --partition=a100-80g
#SBATCH --qos=a100-30min
#SBATCH --time=00:30:00
#SBATCH --gres=gpu:1
#SBATCH --mem=60G
#SBATCH --cpus-per-task=4 
#SBATCH --output=logs/cp_SAM_C3_%j.out
#SBATCH --error=logs/cp_SAM_C3_%j.err

# 1. Setup and Environment Check
cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_SAM

echo "CPSAM Cell 3D"

IMAGE=$1
OUT_PATH=$2


pixi run python -m cellpose \
	--image_path "$IMAGE" \
	--savedir "$OUT_PATH" \
	--use_gpu \
	--do_3D \
	--diameter 76.271 \
	--flow_threshold -3.404 \
	--cellprob_threshold -3.16 \
	--anisotropy 2.786 \
	--flow3D_smooth 0.69 \
	--save_tif \
	--batch_size 500 \
	--no_npy \
	--verbose
