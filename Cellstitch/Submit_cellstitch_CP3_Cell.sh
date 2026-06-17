#!/bin/bash
#SBATCH --job-name=Cellpose_SAM_Bact
#SBATCH --partition=titan                      
#SBATCH --qos=titan-6hours                     
#SBATCH --time=06:00:00                        
#SBATCH --gres=gpu:1                           
#SBATCH --mem=64G                              
#SBATCH --cpus-per-task=4                      
#SBATCH --output=logs/CP3_Cell/%j.out               
#SBATCH --error=logs/CP3_Cell/%j.err    

cd $HOME/Imaging_Project_sciCORE/CLEAN/Pipeline_Final/Scripts/Cellpose_3_TITAN


echo "CP3 Cell 3D"

IMAGE=$1
OUT_PATH=$2

pixi run python cellstitch_CP3_Cell.py $IMAGE $OUT_PATH

