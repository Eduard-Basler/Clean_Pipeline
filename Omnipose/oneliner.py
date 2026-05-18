import skimage.io as io
from cellpose_omni import models

# 1. Load your 3D image stack (Expected shape: [Z, Y, X])
img = io.imread('/home/basler0004/Pipeline_Final/Input/TIFF/77179/Channel_2/20251212_your_3d_volume.tif')

# 2. Initialize the true 3D model (dim=3 requires a 3D-trained model)
model = models.CellposeModel(gpu=True, model_type='plant_omni', dim=3)

# 3. Execute the 3D segmentation
masks, flows, styles = model.eval(
    img,
    channels=[0, 0],     # Adjust channels based on your image
    mask_threshold=-5,   
    omni=True            # No do_3D=True needed here; the model processes true 3D natively
)

# 4. Save the resulting 3D mask stack
io.imsave('segmented_true_3d_masks.tif', masks)
print("True 3D Segmentation complete! Masks saved.")
