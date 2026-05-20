#!/bin/bash
#SBATCH --job-name=Batch_Calib_A100
#SBATCH --partition=a100-80g
#SBATCH --qos=a100-30min
#SBATCH --time=00:10:00
#SBATCH --gres=gpu:1
#SBATCH --mem=60G
#SBATCH --cpus-per-task=4 
#SBATCH --output=logs/cp_3_NUC_%j.out
#SBATCH --error=logs/cp_3_NUC_%j.err

# 1. Setup and Environment Check
cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_3

IMAGE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/TIFF/20251212_transwell_sATA1517_24hPI_60xOIL_rep3_/Channel_1/20251212_transwell_sATA1517_24hPI_60xOIL_rep3__s1_c1.tiff"
OUT_PATH="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Output/Calibration"
mkdir -p "$OUT_PATH"

pixi run python -m cellpose \
	--image_path "$IMAGE" \
	--savedir "$OUT_PATH" \
	--use_gpu \
	--pretrained_model Nuclei \
	--pretrained_model_ortho Nuclei \
	--do_3D \
	--diameter 50 \
	--flow_threshold -3.742 \
	--cellprob_threshold -3.16 \
	--min_size 139085 \
	--anisotropy 2.43 \
	--flow3D_smooth 1.74 \
	--save_tif \
	--batch_size 900 \
	--no_npy \
	--verbose
