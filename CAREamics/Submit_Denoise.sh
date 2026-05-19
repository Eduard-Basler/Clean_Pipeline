#!/bin/bash
#SBATCH --job-name=N2V2_A100_Predict
#SBATCH --partition=a100            
#SBATCH --qos=a100-30min           
#SBATCH --time=00:30:00             
#SBATCH --gres=gpu:1                
#SBATCH --mem=64G                   
#SBATCH --cpus-per-task=4   
#SBATCH --output=logs/split_%j.out
#SBATCH --error=logs/split_%j.err        

cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/CAREamics

SCRIPT_PATH="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/CAREamics/Denoise.py"

pixi run python "$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/CAREamics/Denoise.py" \
    --predict_source "$1" \
    --checkpoint "$2" \
    --output_dir "$3"