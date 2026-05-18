cd ~/Pipeline_Final/Scripts/Cellpose
pixi run python -m cellpose \
--dir /home/basler0004/Pipeline_Final/Input/TIFF/Python_Split/ \
--savedir /home/basler0004/Pipeline_Final/Temp_Prediction_Cellpose/Cellpose_SAM/ \
--use_gpu \
--diameter 6 \
--flow_threshold 0 \
--cellprob_threshold -2.5 \
--norm_percentile 30 99.99 \
--min_size 5 \
--batch_size 32 \
--save_tif \
--no_npy \
--verbose \
--niter 300
