#!/bin/bash
#SBATCH --job-name=CP_Test
#SBATCH --partition=titan
#SBATCH --qos=titan-6hours
#SBATCH --time=00:30:00        # Short time limit for quick testing
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --cpus-per-task=2
#SBATCH --output=test_cp_%j.out
#SBATCH --error=test_cp_%j.err

# ─── UPDATE THIS SINGLE PATH IF NEEDED ────────────────────────────
# Absolute path to where your active data directory lives
DATA_ROOT="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Split_Views/20251212_transwell_sATA1946_sATA2044_16hPI_60xOIL_rep2_006_s1_CHUNKS"
# ──────────────────────────────────────────────────────────────────
cd ~/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_SAM_TITAN
# --- SET YOUR TEST PARAMETERS HERE ---
TEST_VIEW="XZ"       # Options: XY, XZ, YZ
TEST_BATCH=64        # The batch size you want to verify
TEST_DIAM=45.000     # Your target diameter setting
TEST_FLOW=-2.000
TEST_CELLP=0.500
# ------------------------------------

# Now targets the absolute data root path safely
IN_CHUNK="${DATA_ROOT}/${TEST_VIEW}/Channel_1/Chunk_0"
OUT_CHUNK="${DATA_ROOT}/${TEST_VIEW}/Channel_1/Masks/Chunk_0"

mkdir -p "$OUT_CHUNK"
mkdir -p logs

echo "🚀 Starting test on $(hostname)"
echo "Reading from: ${IN_CHUNK}"
echo "Writing to:   ${OUT_CHUNK}"
echo "Processing View: ${TEST_VIEW} | Batch Size: ${TEST_BATCH} | Diameter: ${TEST_DIAM}"

pixi run python -m cellpose \
  --dir "$IN_CHUNK" \
  --savedir "$OUT_CHUNK" \
  --use_gpu \
  --batch_size "$TEST_BATCH" \
  --diameter "$TEST_DIAM" \
  --flow_threshold "$TEST_FLOW" \
  --cellprob_threshold "$TEST_CELLP" \
  --save_tif \
  --no_npy \
  --verbose

echo "🎉 Test run complete! Check test_cp_${SLURM_JOB_ID}.out for execution times."