#!/bin/bash
# launch.sh

# ─── UPDATE THIS SINGLE PATH ──────────────────────────────────────
# Point this to where your active data directory lives
DATA_ROOT="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Split_Views/20251212_transwell_sATA1946_sATA2044_16hPI_60xOIL_rep2_006_s1_CHUNKS"
# ──────────────────────────────────────────────────────────────────

WORKER_SCRIPT="$HOME/cellpose_worker.sh"

for VIEW in XY XZ YZ; do
    if [ "$VIEW" == "XY" ]; then
        BATCH=64
        DIAM=76.271
        FLOW=-3.742
        CELLP=0.759
    elif [ "$VIEW" == "XZ" ]; then
        BATCH=64
        DIAM=76.271
        FLOW=-3.742
        CELLP=0.759
    elif [ "$VIEW" == "YZ" ]; then
        BATCH=32
        DIAM=76.271
        FLOW=-3.742
        CELLP=0.759
    fi

    for CH in 1 2 3 4; do
        # Build absolute paths pointing out to the data folder
        IN_PATH="${DATA_ROOT}/${VIEW}/Channel_${CH}"
        OUT_PATH="${DATA_ROOT}/${VIEW}/Channel_${CH}/Masks"
        
        echo "Submitting ${VIEW} | Channel ${CH} | Batch: ${BATCH}, Diam: ${DIAM}"
        sbatch "$WORKER_SCRIPT" "$IN_PATH" "$OUT_PATH" "$BATCH" "$DIAM" "$FLOW" "$CELLP"
    done
done