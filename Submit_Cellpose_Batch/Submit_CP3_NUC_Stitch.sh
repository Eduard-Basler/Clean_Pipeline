#!/bin/bash
#SBATCH --job-name=Batch_Calib_A100
#SBATCH --partition=a100-80g
#SBATCH --qos=a100-30min
#SBATCH --time=00:30:00
#SBATCH --gres=gpu:1
#SBATCH --mem=60G
#SBATCH --cpus-per-task=4 
#SBATCH --output=logs/cp_3_NS_%j.out
#SBATCH --error=logs/cp_3_NS_%j.err

# 1. Setup and Environment Check
cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_3

echo "CP3 Nuc Stitch"

IMAGE=$1
OUT_PATH=$2


pixi run python -m cellpose \
	--image_path "$IMAGE" \
	--savedir "$OUT_PATH" \
	--use_gpu \
	--pretrained_model Nuclei \
	--diameter 50 \
	--flow_threshold -3.742 \
	--cellprob_threshold 1.966 \
	--save_tif \
	--batch_size 900 \
	--stitch_threshold 0.5 \
	--no_npy \
	--verbose
