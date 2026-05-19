#!/bin/bash
#SBATCH --job-name=Cellpose_Single
#SBATCH --partition=titan                      
#SBATCH --qos=titan-6hours                     
#SBATCH --time=02:00:00                        
#SBATCH --gres=gpu:1                           
#SBATCH --mem=64G                              
#SBATCH --cpus-per-task=4                      
#SBATCH --output=logs/cp_%j.out               
#SBATCH --error=logs/cp_%j.err                

IMAGE_NAME=$1
CHANNEL=$2

INPUT_BASE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Input/TIFF"
SAVE_BASE="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Output/Cellpose_SAM_RAW"

DIR="${INPUT_BASE}/${IMAGE_NAME}/${CHANNEL}"
SAVEDIR="${SAVE_BASE}/${IMAGE_NAME}/${CHANNEL}"

mkdir -p "$SAVEDIR"
mkdir -p logs

# -----------------------------------------------------------------
# 1. START SECOND-BY-SECOND LIVE MONITORING
# -----------------------------------------------------------------
TRACK_LOG="logs/mem_track_${SLURM_JOB_ID}.log"
echo "Time | RAM Used/Total | VRAM Used/Total" > "$TRACK_LOG"

while true; do
    TIMESTAMP=$(date +%H:%M:%S)
    RAM_INFO=$(free -h | awk '/Mem:/ {print $3 "/" $2}')
    VRAM_INFO=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk '{print $1 "MiB/" $3 "MiB"}')
    
    echo "$TIMESTAMP | $RAM_INFO | $VRAM_INFO" >> "$TRACK_LOG"
    sleep 1
done &

# Save the Process ID of the background loop so we can stop it later
MONITOR_PID=$!
# -----------------------------------------------------------------

cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_SAM_TITAN

# 2. Run Cellpose
pixi run python -m cellpose \
  --dir "$DIR" \
  --savedir "$SAVEDIR" \
  --use_gpu \
  --z_axis 0 \
  --batch_size 48 \
  --diameter 76.271 \
  --flow_threshold -3.742 \
  --cellprob_threshold 0.759 \
  --min_size 23959 \
  --stitch_threshold 0.456 \
  --norm_percentile 1.82 98.53 \
  --save_tif \
  --no_npy \
  --verbose

# 3. Stop the background monitor when Cellpose finishes
kill "$MONITOR_PID"