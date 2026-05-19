import argparse
from pathlib import Path
import tifffile
from careamics.careamist import CAREamist
import torch
torch.set_float32_matmul_precision('medium')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--predict_source", required=True, help="Path to a single noisy TIFF file")
    parser.add_argument("--checkpoint", required=True, help="Path to the .ckpt model")
    parser.add_argument("--output_dir", required=True, help="Directory where the output will save")
    args = parser.parse_args()

    # 1. Resolve paths cleanly
    file_path = Path(args.predict_source).expanduser().resolve()
    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not file_path.is_file():
        raise FileNotFoundError(f"🚨 Provided path is not a valid file: '{file_path}'")

    print(f"🎯 Loading model weights: {Path(args.checkpoint).name}")
    careamist = CAREamist(source=args.checkpoint)

    # 2. Run prediction directly on the file path string
    print(f"✨ Denoising file: {file_path.name}")
    predictions = careamist.predict(
        source=str(file_path),  # CAREamics takes the file path string directly
        data_type="tiff",
        axes="ZYX",
        tile_size=[32, 256, 256],
        tile_overlap=[8, 64, 64],
        batch_size=21,
        predict_dataloader_params={"num_workers": 3}
    )

    # 3. Unpack and save
    pred_array = predictions[0]
    save_path = out_dir / f"CLEAN_{file_path.name}"
    tifffile.imwrite(save_path, pred_array.squeeze())
    
    print(f"✅ Success! Saved denoised file to: {save_path}")
    print("\n>>> ALL PREDICTIONS COMPLETE.")