import argparse
from pathlib import Path
import tifffile
from careamics.careamist import CAREamist

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--predict_source", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    careamist = CAREamist(source=args.checkpoint)

    input_files = sorted(Path(args.predict_source).glob("*.tif*"))

    for file_path in input_files:

        predictions = careamist.predict(
            source=file_path,  # Passed the individual file instead of the folder
            data_type="tiff",
            axes="ZYX",
            tile_size=[32, 256, 256],
            tile_overlap=[8, 64, 64],
            batch_size=16,
            predict_dataloader_params={"num_workers": 4}
        )

        pred_array = predictions[0]

        save_path = out_dir / f"CLEAN_{file_path.name}"
        tifffile.imwrite(save_path, pred_array.squeeze())
        print(f"Saved: {save_path.name}")

    print("\n>>> ALL PREDICTIONS COMPLETE.")