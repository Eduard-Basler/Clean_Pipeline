import os, tifffile, numpy as np, argparse
from pathlib import Path

def slice_testing_image(input_dir, output_dir):
    base_dir = Path(input_dir)
    out_root = Path(output_dir)
    
    # Extract sample name from path to keep metadata accurate
    sample_name = base_dir.name
    
    metadata = [f"Original Sample: {sample_name} \nPosition: s1\n" + "="*54]
    print(f"🚀 Chunking on compute node...\nReading from: {base_dir}\nWriting to:    {out_root}")

    for ch in range(1, 5):
        file_path = base_dir / f"Channel_{ch}" / f"{sample_name}_s1_c{ch}.tiff"
        if not file_path.exists(): 
            print(f"⚠️ Skipping Channel {ch} (File not found: {file_path.name})")
            continue
            
        img = tifffile.imread(file_path) # (Z, Y, X) -> (101, 2720, 2720)
        
        # Maps view to its matching axis in the 3D volume array
        for view_name, axis in [("XY", 0), ("XZ", 1), ("YZ", 2)]:
            # Create array splits across the chosen perspective axis
            chunks = np.array_split(np.arange(img.shape[axis]), 20)
            
            for chunk_id, indices in enumerate(chunks):
                if len(indices) == 0: continue
                
                chunk_dir = out_root / view_name / f"Channel_{ch}" / f"Chunk_{chunk_id}"
                chunk_dir.mkdir(parents=True, exist_ok=True)
                
                # Write individual loose 2D frames
                for idx in indices:
                    # Dynamically slice out the single 2D plane based on our current view axis
                    frame = img[idx, :, :] if axis == 0 else (img[:, idx, :] if axis == 1 else img[:, :, idx])
                    tifffile.imwrite(chunk_dir / f"Slice_{idx}.tiff", frame.astype(np.uint16), compression='zlib')

                metadata.append(f"{view_name} | Channel_{ch} | Chunk_{chunk_id} | Slices: {indices[0]}-{indices[-1]} | Files: {len(indices)}")
        print(f"✅ Finished Channel {ch}")

    out_root.mkdir(parents=True, exist_ok=True)
    with open(out_root / "metadata.txt", "w") as f:
        f.write("\n".join(metadata))
    print(f"\n🎉 Done! Structure generated successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Slice 3D channels into loose 2D chunks across XY, XZ, YZ views.")
    parser.add_argument("--input", required=True, help="Path to the sample base directory containing Channel_1, Channel_2, etc.")
    parser.add_argument("--output", required=True, help="Path to the destination root directory for chunks")
    args = parser.parse_args()

    slice_testing_image(args.input, args.output)