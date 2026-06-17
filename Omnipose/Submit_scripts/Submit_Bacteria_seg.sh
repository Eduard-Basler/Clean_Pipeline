#!/bin/bash
#SBATCH --job-name=Omni_BS
#SBATCH --partition=a100-80g
#SBATCH --qos=a100-30min
#SBATCH --time=00:30:00
#SBATCH --gres=gpu:1
#SBATCH --mem=120G
#SBATCH --cpus-per-task=4 
#SBATCH --output=logs/Omni_BS/%j.out
#SBATCH --error=logs/Omni_BS/%j.err

# Create the logging directory and step into the project folder
mkdir -p logs/Omni_BS
cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Omnipose

# Read inputs
IMAGE_PATH=$1
OUT_PATH=$2

cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Omnipose

# Execute the simple Python pipeline
pixi run python run_omnipose_simple.py "$IMAGE_PATH" "$OUT_PATH"

