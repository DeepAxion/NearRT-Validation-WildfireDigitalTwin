import os
import glob
import numpy as np
import rasterio
import argparse


def find_band_files(dir_path):
    """locate the B5 and B7 band files in the specified directory."""
    b5_file = glob.glob(os.path.join(dir_path, '*_B5*'))[0]
    b7_file = glob.glob(os.path.join(dir_path, '*_B7*'))[0]
    return b5_file, b7_file

def read_raster(file_path):
    """read a single raster band from the file."""
    with rasterio.open(file_path) as src:
        band = src.read(1)
    return band 

def calculate_nbr(band_5, band_7):
    """calculate the Normalized Burn Ratio (NBR) from B5 and B7 bands."""
    np.seterr(divide='ignore', invalid='ignore')
    nbr = (band_5.astype(float) - band_7.astype(float)) / (band_5 + band_7)
    return nbr

def process_scene(scene_dir):
    """process a single scene to calculate the NBR and save the result in the same folder."""
    b5_file, b7_file = find_band_files(scene_dir)
    band_5 = read_raster(b5_file)
    band_7 = read_raster(b7_file)
    nbr = calculate_nbr(band_5, band_7)
    
    # Define the output file path within the scene folder
    base_name = os.path.basename(b5_file)  # ge the final component of reference filename (e.g LC08...B5)
    output_file_name = base_name.replace("B5", "NBR")  # replace "B5" with "NBR"
    output_file = os.path.join(scene_dir, output_file_name)

    # save the NBR to a new raster file
    with rasterio.open(b5_file) as src:
        profile = src.profile
    profile.update(dtype=rasterio.float32, count=1)
    
    with rasterio.open(output_file, 'w', **profile) as dst:
        dst.write(nbr.astype(rasterio.float32), 1)
    print(f"NBR calculated and saved for {output_file_name} at {output_file}")

          
if __name__ == '__main__':
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process scenes to calculate NBR and save in each scene folder.')
    parser.add_argument('-i', '--input_dir', required=True,
                        help='Path to the base directory containing scene folders.', type=str)

    # Parse arguments
    args = parser.parse_args()
    base_dir = os.path.normpath(args.input_dir)

    # Process all scenes
    for scene_dir in os.listdir(base_dir):
        full_scene_dir = os.path.join(base_dir, scene_dir)
        if os.path.isdir(full_scene_dir):  # ensure it's a directory
            process_scene(full_scene_dir)
