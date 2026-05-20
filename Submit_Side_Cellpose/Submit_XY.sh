#!/bin/bash
#SBATCH --job-name=CP_XY
#SBATCH --partition=titan
#SBATCH --qos=titan-30min
#SBATCH --time=00:30:00
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --cpus-per-task=2
#SBATCH --array=0-19
#SBATCH --output=logs/cp_xy_%A_%a.out
#SBATCH --error=logs/cp_xy_%A_%a.err

# ─── PATH CONFIGURATION ───────────────────────────────────────────
DATA_ROOT="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Split_Views/20251212_transwell_sATA1946_sATA2044_16hPI_60xOIL_rep2_006_s1_CHUNKS"
# ──────────────────────────────────────────────────────────────────

# Parameters for Top-Down (XY)
BATCH=100
DIAM=76.271
FLOW=-3.742
CELLP=0.759

mkdir -p logs

cd ~/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_SAM_TITAN

# Run across all 4 channels sequentially inside this array task slot
for CH in 1 2 3 4; do
    IN_CHUNK="${DATA_ROOT}/XY/Channel_${CH}/Chunk_${SLURM_ARRAY_TASK_ID}"
    OUT_CHUNK="${DATA_ROOT}/XY/Channel_${CH}/Masks/Chunk_${SLURM_ARRAY_TASK_ID}"
    
    mkdir -p "$OUT_CHUNK"
    
    echo "Processing XY | Channel ${CH} | Chunk ${SLURM_ARRAY_TASK_ID}"
    
    pixi run python -m cellpose \
      --dir "$IN_CHUNK" \
      --savedir "$OUT_CHUNK" \
      --use_gpu \
      --batch_size "$BATCH" \
      --diameter "$DIAM" \
      --flow_threshold "$FLOW" \
      --cellprob_threshold "$CELLP" \
      --save_tif \
      --no_npy
done