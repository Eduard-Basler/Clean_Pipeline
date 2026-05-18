import os
import glob
import numpy as np
import skimage.io as skio
import segment3D.parameters as uSegment3D_params
import segment3D.usegment3d as uSegment3D
import segment3D.filters as uSegment3D_filters
import segment3D.file_io as uSegment3D_fio

# This is the required "shield" for multiprocessing in Python
if __name__ == '__main__':
    
    # 1. Load and stack your folder of 2D masks
    # =============================================================================
    mask_folder = './Masks' # Make sure this matches the path that worked for you!

    # Find all .tif files in alphabetical/numerical order
    slice_files = sorted(glob.glob(os.path.join(mask_folder, '*.tif')))

    if len(slice_files) == 0:
        raise FileNotFoundError(f"No .tif masks found in {mask_folder}.")

    print(f"Found {len(slice_files)} slices. Reading and stacking...")

    # Read slices individually and stack them into a 3D volume (Shape: Z, Y, X)
    mask_slices = [skio.imread(f) for f in slice_files]
    labels_xy = np.stack(mask_slices, axis=0)

    # Clean up slices slice-by-slice to filter out minor spatial noise
    labels_xy = uSegment3D_filters.filter_2d_label_slices(labels_xy, bg_label=0, minsize=8)

    # 2. Configure Aggregation Parameters
    # =============================================================================
    params = uSegment3D_params.get_2D_to_3D_aggregation_params()

    # Using exact heat equation solver with central fixed points
    params['indirect_method']['dtform_method'] = 'cellpose_improve'
    params['indirect_method']['edt_fixed_point_percentile'] = 0.01
    params['gradient_descent']['gradient_decay'] = 0.25
    params['gradient_descent']['n_iter'] = 250
    params['gradient_descent']['momenta'] = 0.98

    # 3. Run 3D Aggregation (Stitching)
    # =============================================================================
    print("Starting 2D-to-3D aggregation from the XY slice stack...")

    # Supplying [labels_xy, [], []] tells u-Segment3D we only have the XY projection view
    segmentation3D, (probability3D, gradients3D) = uSegment3D.aggregate_2D_to_3D_segmentation_indirect_method(
        segmentations=[labels_xy, [], []], 
        img_xy_shape=labels_xy.shape, 
        precomputed_binary=(labels_xy > 0), # Automatically sets up known object foreground
        params=params
    )

    # Optional: post-processing size filter to drop any merged objects smaller than 250 voxels
    segmentation3D = uSegment3D_filters.remove_small_labels(segmentation3D, min_size=250)

    # 4. Save 3D Volume Results
    # =============================================================================
    output_file = './stitched_3D_output.tif'
    uSegment3D_fio.save_segmentation(output_file, segmentation3D)

    print(f"Stitching finished! Your 3D stitched volume is saved at: {output_file}")
