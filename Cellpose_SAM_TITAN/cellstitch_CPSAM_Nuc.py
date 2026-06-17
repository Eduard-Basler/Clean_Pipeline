import tifffile, torch, numpy as np, argparse, os
from pathlib import Path
from cellpose import models, io
from cellstitch_cuda.pipeline import full_stitch

# Initialize Cellpose logging
io.logger_setup()

def run_cellstitch(input_path, output_path, batch_xy, batch_yz, batch_xz):
    print(f"Loading Stack: {input_path.name}")
    img = tifffile.imread(input_path) # Expected shape: (Z, C, Y, X)
    
    model = models.CellposeModel(gpu=True)

    # Base evaluation parameters (Corrected Syntax and channel_axis)
    eval_kwargs = {
        "channels": [0, 0], # Matches your working script
        "diameter": 50,
        "cellprob_threshold": -3.16,
        "flow_threshold": -3.742
    }

    # 1. Segment XY
    print(f"Segmenting XY (batch_size={batch_xy})...")
    xy_masks, _, _ = model.eval(list(img), batch_size=batch_xy, **eval_kwargs)
    xy_masks = np.stack(xy_masks).astype(np.uint32)

    # 2. Segment YZ (Transpose Z, Y, X -> Y, Z, X)
    print(f"Segmenting YZ (batch_size={batch_yz})...")
    img_yz = img.transpose(1, 0, 2)
    yz_masks, _, _ = model.eval(list(img_yz), batch_size=batch_yz, **eval_kwargs)
    yz_masks = np.stack(yz_masks).transpose(1, 0, 2).astype(np.uint32)

    # 3. Segment XZ (Transpose Z, Y, X -> X, Y, Z)
    print(f"Segmenting XZ (batch_size={batch_xz})...")
    img_xz = img.transpose(2, 1, 0)
    xz_masks, _, _ = model.eval(list(img_xz), batch_size=batch_xz, **eval_kwargs)
    xz_masks = np.stack(xz_masks).transpose(2, 1, 0).astype(np.uint32)

    # Optimal Transport Stitching
    print("Stitching views with CellStitch...")
    cellstitch_masks = full_stitch(xy_masks, yz_masks, xz_masks)

    # Handle directory vs file output
    if output_path.is_dir() or not output_path.suffix:
        output_path.mkdir(parents=True, exist_ok=True)
        out_file = output_path / f"{input_path.stem}_CELLSTITCH.tif"
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        out_file = output_path

    tifffile.imwrite(out_file, cellstitch_masks.astype(np.uint32), compression='zlib')
    print(f"✅ Saved Stitched Volume: {out_file.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to input 3D TIFF (Z, Y, X)")
    parser.add_argument("output", help="Path to output directory")
    args = parser.parse_args()

    run_cellstitch(Path(args.input), Path(args.output), 32, 64, 64)