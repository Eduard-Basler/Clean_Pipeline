#!/bin/bash
#SBATCH --job-name=Cellpose_Titan_Predict
#SBATCH --partition=titan                      # Switched to titan partition
#SBATCH --qos=titan-6hours                     # Switched to titan 6-hour QoS
#SBATCH --time=02:00:00                        # 2 hours requested
#SBATCH --gres=gpu:1                           # 1 Titan GPU
#SBATCH --mem=32G                              # 32 GB RAM
#SBATCH --cpus-per-task=3                      # 4 CPU cores for data loading
#SBATCH --output=cellpose_%j.out               # Standard output log
#SBATCH --error=cellpose_%j.err                # Standard error log

# Navigate to your project directory (recommended for pixi to find your environment)
cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_SAM

# Run the Cellpose prediction
pixi run python -m cellpose \
  --dir $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/TIFF/20251212_transwell_sATA1517_24hPI_60xOIL_rep3_/Channel_4 \
  --savedir $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Output/Cellpose_SAM_RAW/20251212_transwell_sATA1517_24hPI_60xOIL_rep3_/Channel_4 \
  --use_gpu \
  --z_axis 0 \
  --batch_size 64 \
  --diameter 76.271 \
  --flow_threshold -3.742 \
  --cellprob_threshold 0.759 \
  --min_size 23959 \
  --stitch_threshold 0.456 \
  --norm_percentile 1.82 98.53 \
  --save_tif \
  --no_npy \
  --verbose