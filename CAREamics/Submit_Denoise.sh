#!/bin/bash
#SBATCH --job-name=N2V2_A100_Predict
#SBATCH --partition=a100            
#SBATCH --qos=a100-6hours           
#SBATCH --time=02:00:00             
#SBATCH --gres=gpu:1                
#SBATCH --mem=32G                   
#SBATCH --cpus-per-task=4           

cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/CAREamics

SCRIPT_PATH="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/CAREamics/Denoise.py"

$PYTHON_EXEC $SCRIPT_PATH \
    --predict_source "$1" \
    --checkpoint "$2" \
    --output_dir "$3"