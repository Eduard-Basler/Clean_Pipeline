import argparse, os, itertools, nd2, tifffile

p = argparse.ArgumentParser()
for flag in ['-series', '-channel', '-z', '-t']: 
    p.add_argument(flag, type=int)
p.add_argument('input_file')
p.add_argument('output_pattern')
args = p.parse_args()

# Shift user inputs from 1-based down to 0-based for internal Python slicing
s = args.series - 1 if args.series is not None else None
c = args.channel - 1 if args.channel is not None else None
z = args.z - 1 if args.z is not None else None
t = args.t - 1 if args.t is not None else None

base_name = os.path.splitext(os.path.basename(args.input_file))[0]
out_pattern = args.output_pattern.replace("{name}", base_name)

with nd2.ND2File(args.input_file) as f:
    data = f.to_xarray()
    dims = {'P': (s, '%s'), 'C': (c, '%c'), 'Z': (z, '%z'), 'T': (t, '%t')}
    
    ranges = {d: [val] if val is not None else range(f.sizes[d])
              for d, (val, tag) in dims.items()
              if d in f.sizes and (val is not None or tag in out_pattern)}

    for indices in itertools.product(*ranges.values()):
        selector = dict(zip(ranges.keys(), indices))
        img = data.isel(**selector).squeeze().values

        out = out_pattern
        for dim, idx in selector.items():
            # Shift the index up (+ 1) so filenames print out as 1-based
            out = out.replace(dims[dim][1], str(idx + 1))

        out_dir = os.path.dirname(out)
        if out_dir: 
            os.makedirs(out_dir, exist_ok=True)

        tifffile.imwrite(out, img)
        print(f"Saved: {out}")
