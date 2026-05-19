#!/bin/bash
#SBATCH --job-name=Cellpose_SAM_Cyto
#SBATCH --partition=titan                      
#SBATCH --qos=titan-6hours                     
#SBATCH --time=06:00:00                        
#SBATCH --gres=gpu:1                           
#SBATCH --mem=256G                              
#SBATCH --cpus-per-task=3                      
#SBATCH --output=logs/cpsam_cyto_%j.out               
#SBATCH --error=logs/cpsam_cyto_%j.err                

# Order template:
# sbatch XXX.sh [INPUT_PATH] [OUTPUT_PATH] [BATCH_SIZE] [DIAMETER] [FLOW] [CELLPROB] [STITCH]

IN=$1
OUT=$2
BATCH_SIZE=$3
DIAMETER=$4
FLOW=$5
CELLPROB=$6
STITCH=$7

cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_SAM_TITAN

# -----------------------------------------------------------------
# 1. START SECOND-BY-SECOND LIVE MONITORING
# -----------------------------------------------------------------
mkdir -p logs # Ensure the logs directory exists
TRACK_LOG="logs/mem_track_${SLURM_JOB_ID}.log"
echo "Time | RAM Used/Total | VRAM Used/Total" > "$TRACK_LOG"

while true; do
    TIMESTAMP=$(date +%H:%M:%S)
    RAM_INFO=$(free -h | awk '/Mem:/ {print $3 "/" $2}')
    VRAM_INFO=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk '{print $1 "MiB/" $2 "MiB"}')

    echo "$TIMESTAMP | $RAM_INFO | $VRAM_INFO" >> "$TRACK_LOG"
    sleep 2
done &

MONITOR_PID=$!
# -----------------------------------------------------------------

# Print parameters for the log parser
echo "PARAMS | Cyto | $BATCH_SIZE | $DIAMETER | $FLOW | $CELLPROB | $STITCH"

pixi run python -m cellpose \
  --image_path "$IN" \
  --savedir "$OUT" \
  --use_gpu \
  --z_axis 0 \
  --batch_size "$BATCH_SIZE" \
  --diameter "$DIAMETER" \
  --flow_threshold "$FLOW" \
  --cellprob_threshold "$CELLPROB" \
  --stitch_threshold "$STITCH" \
  --save_tif \
  --no_npy \
  --verbose

# -----------------------------------------------------------------
# 2. STOP MONITORING (Crucial step so the job wraps up cleanly)
# -----------------------------------------------------------------
kill $MONITOR_PID