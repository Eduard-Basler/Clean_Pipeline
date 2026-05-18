#!/bin/bash
#SBATCH --job-name=N2V2_Train
#SBATCH --partition=a100-80g
#SBATCH --qos=a100-1day
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:a100-80g:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=200G
#SBATCH --output=n2v2_%j.log

# Paths
PYTHON_EXEC="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/CAREamics/.pixi/envs/default/bin/python"
SCRIPT_PATH="$HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/CAREamics/Train.py"

# Run
$PYTHON_EXEC $SCRIPT_PATH --train_source "$1"