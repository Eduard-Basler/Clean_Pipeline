#!/bin/bash
#SBATCH --job-name=CP3_Bact_Sweep
#SBATCH --partition=titan
#SBATCH --qos=titan-6hours
#SBATCH --time=06:00:00
#SBATCH --gres=gpu:1
#SBATCH --mem=78G
#SBATCH --cpus-per-task=3
#SBATCH --output=logs/cp3_bact_%j.out
#SBATCH --error=logs/cp3_bact_%j.err

# Order template:
# sbatch XXX.sh [INPUT_PATH] [OUTPUT_BASE_PATH] [BATCH_SIZE] [DIAMETER] [FLOW] [CELLPROB] [STITCH]

IN=$1
OUT_BASE=$2
BATCH_SIZE=$3
DIAMETER=$4
FLOW=$5
CELLPROB=$6
STITCH=$7

cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_3_TITAN


PARAM_STRING="${BATCH_SIZE}_${DIAMETER}_${FLOW}_${CELLPROB}_${STITCH}"
OUT="${OUT_BASE}/Param_${PARAM_STRING}"
mkdir -p "$OUT"

PARAM_LOG="${OUT}/parameters.txt"
echo "Date/Time: $(date)" > "$PARAM_LOG"
echo "Slurm Job ID: ${SLURM_JOB_ID}" >> "$PARAM_LOG"
echo "Input Image: ${IN}" >> "$PARAM_LOG"
echo "Parameters (Batch, Diam, Flow, Prob, Stitch): $PARAM_STRING" >> "$PARAM_LOG"


echo "PARAMS | Bacteria Sweep CP3 | $BATCH_SIZE | $DIAMETER | $FLOW | $CELLPROB | $STITCH"

pixi run python -m cellpose \
  --image_path "$IN" \
  --savedir "$OUT" \
  --pretrained_model deepbacs_cp3 \
  --chan 0 \
  --chan2 0 \
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
  
