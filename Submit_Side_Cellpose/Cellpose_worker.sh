#!/bin/bash
#SBATCH --job-name=CP_Chunk
#SBATCH --partition=titan
#SBATCH --qos=titan-6hours
#SBATCH --time=06:00:00
#SBATCH --gres=gpu:1
#SBATCH --mem=128G
#SBATCH --cpus-per-task=4
#SBATCH --array=0-19
#SBATCH --output=logs/cp_%A_%a.out
#SBATCH --error=logs/cp_%A_%a.err

cd ~/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_SAM_TITAN

IN_DIR=$1
OUT_DIR=$2
BATCH=$3
DIAM=$4
FLOW=$5
CELLP=$6

IN_CHUNK="${IN_DIR}/Chunk_${SLURM_ARRAY_TASK_ID}"
OUT_CHUNK="${OUT_DIR}/Chunk_${SLURM_ARRAY_TASK_ID}"

mkdir -p "$OUT_CHUNK"
mkdir -p logs

pixi run python -m cellpose \
  --dir "$IN_CHUNK" \
  --savedir "$OUT_CHUNK" \
  --use_gpu \
  --z_axis 0 \
  --batch_size "$BATCH" \
  --diameter "$DIAM" \
  --flow_threshold "$FLOW" \
  --cellprob_threshold "$CELLP" \
  --save_tif \
  --no_npy