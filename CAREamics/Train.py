import argparse
import os
import torch
from careamics.careamist import CAREamist
from careamics.config import create_n2v_configuration


if __name__ == "__main__":
    # Parse folder input
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_source", required=True)
    args = parser.parse_args()

    # Automatically extract the folder name (e.g., "Channel_1", "Channel_2")
    # rstrip("/") ensures trailing slashes don't break the string parsing
    channel_folder = os.path.basename(args.train_source.rstrip("/"))
    
    # Create a completely unique experiment identifier
    dynamic_exp_name = f"N2V2_{channel_folder}"
    print(f"\n>>> TARGET DETECTED: {channel_folder}")
    print(f">>> ISOLATING EXPERIMENT TO DIR: ./careamics_checkpoints/{dynamic_exp_name}\n")

    # Configure N2V2 using the dynamic name
    config = create_n2v_configuration(
        experiment_name=dynamic_exp_name,
        data_type="tiff",
        axes="ZYX",
        patch_size=[32, 256, 256],  
        batch_size=8,               
        num_epochs=100,
        # THE DEADLOCK FIX: Safely capping PyTorch's workers per the official docs!
        train_dataloader_params={"num_workers": 4},
        val_dataloader_params={"num_workers": 2}
    )
    # Train
    careamist = CAREamist(source=config, work_dir="./careamics_checkpoints")
    careamist.train(
        train_source=args.train_source, 
        use_in_memory=True, 
        val_percentage=0.15          
    )