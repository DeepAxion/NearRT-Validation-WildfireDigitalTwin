import os
import numpy as np
import glob
import rasterio
import imageio
import argparse

def read_nbr(file_path):
    """read a single nbr band from the file."""
    with rasterio.open(file_path) as src:
        nbr_data = src.read(1).astype(float)
        nbr_data = np.where((nbr_data == src.nodata) | np.isinf(nbr_data), np.nan, nbr_data)
        # clamp values over 1 and below -1
        nbr_data = np.where(nbr_data > 1, 1, nbr_data)
        nbr_data = np.where(nbr_data < -1, -1, nbr_data)
    return nbr_data

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
def calculate_mean_and_std_nbr_image(directory):
    nbr_stack = []
    output_mean_path = None  # Initialize to None
    output_std_path = None
    nbr_path = None

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith("NBR.TIF"):
                # process each file
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")
                # extract the parent directory
                parent_dir = os.path.dirname(root)

                # get the output path for the mean image *once*, before the loop
                if not output_mean_path: # check if it is initialized
                    output_mean_path = os.path.join(parent_dir, "mean_nbr_image.tif")
                    output_std_path = os.path.join(parent_dir, "std_nbr_image.tif")
                
                #read nbr band
                nbr_data = read_nbr(file_path)
                nbr_stack.append(nbr_data)
                if nbr_path is None: 
                    nbr_path = file_path
    
    if nbr_stack:
        # stack all NBR arrays along a new third axis
        nbr_stack = np.stack(nbr_stack, axis=0)
        nbr_stack = np.nan_to_num(nbr_stack, nan=0)
        
        # calculate mean and std pixel-wise
        mean_nbr_image = np.mean(nbr_stack, axis=0).astype(float)
        std_nbr_image = np.std(nbr_stack, axis=0).astype(float)

	    # shift the nbr image
        mean_nbr_image_output = (mean_nbr_image + 0.5) * 127.5
        std_nbr_image_output = std_nbr_image * 255
        
        # save the mean image
        # with rasterio.open(
        #     output_mean_path,
        #     'w',
        #     driver='GTiff',
        #     height=mean_nbr_image_output.shape[0],
        #     width=mean_nbr_image_output.shape[1],
        #     count=1,
        #     dtype='float32',
        #     crs=nbr_data.crs,
        #     transform=nbr_data.transform
        # ) as dst:
        #     dst.write(mean_nbr_image_output, 1)
        with rasterio.open(nbr_path) as src:
            profile = src.profile
            profile.update(dtype=rasterio.float32, count=1)
    
        with rasterio.open(output_mean_path, 'w', **profile) as dst:
            dst.write(mean_nbr_image_output.astype(rasterio.float32), 1)

        # save as PNG (Normalize values to [0, 255] for PNG)
        png_output_path = output_mean_path.replace('.TIF', '.png')
        
        # convert to 8-bit format
        mean_8bit = mean_nbr_image_output.astype(np.uint8)  # Convert to 8-bit format

        # save PNG
        imageio.imwrite(png_output_path, mean_8bit)

        print(f"Normalized image saved as PNG to: {png_output_path}") 
        print(f"Mean NBR image saved to: {output_mean_path}")
        
        # save the std image
        # with rasterio.open(
        #     output_std_path,
        #     'w',
        #     driver='GTiff',
        #     height=std_nbr_image_output.shape[0],
        #     width=std_nbr_image_output.shape[1],
        #     count=1,
        #     dtype='float32',
        #     crs=nbr_data.crs,
        #     transform=nbr_data.transform
        # ) as dst:
        #     dst.write(std_nbr_image_output, 1)
        
        with rasterio.open(nbr_path) as src:
            profile = src.profile
            transform = src.transform # Get transform from original file
            crs = src.crs # Get crs from original file
            profile.update(dtype=rasterio.float32, count=1)
    
            with rasterio.open(output_std_path, 'w', **profile) as dst:
                dst.write(std_nbr_image_output.astype(rasterio.float32), 1)
            
        # save as PNG (Normalize values to [0, 255] for PNG)
        png_output_path = output_std_path.replace('.TIF', '.png')
        
        # convert to 8-bit format
        std_8bit = std_nbr_image_output.astype(np.uint8)  # Convert to 8-bit format

        # save PNG
        imageio.imwrite(png_output_path, std_8bit)
        
        print(f"Normalized image saved as PNG to: {png_output_path}") 
        print(f"Standard Deviation NBR image saved to: {output_std_path}")
        
        return mean_nbr_image, std_nbr_image

    #     # Normalize the input image
    #     with rasterio.open(input_normalized_path) as src:
    #         arbitrary_image = src.read(1).astype(float)
    #         arbitrary_image = np.where((arbitrary_image == src.nodata) | np.isinf(arbitrary_image), np.nan, arbitrary_image)
    #         arbitrary_image = np.where(arbitrary_image > 1, 1, arbitrary_image)
    #         arbitrary_image = np.where(arbitrary_image < -1, -1, arbitrary_image)

def normalize_nbr(directory, mean_nbr_image, std_nbr_image):
    
    # # get the mean and the std nbr image
    # mean_nbr_image, std_nbr_image = calculate_mean_and_std_nbr_image(directory)
    
    # get the nbr image 
    nbr_file = glob.glob(os.path.join(directory, '*_NBR*'))[0]
    nbr_image = read_nbr(nbr_file)
    # check and convert nan values to 0
    nbr_image = np.nan_to_num(nbr_image, nan=0.0,  posinf=255.0, neginf=0.0)
    
    # normalize the nbr
    # temporarily suppress the error messages
    with np.errstate(divide='ignore', invalid='ignore'):
        normalized_nbr = (mean_nbr_image - nbr_image).astype(float) / std_nbr_image
        
    # shift the image values
    normalized_nbr = normalized_nbr * 30 + 128
    
    # define the output file path within the scene folder
    base_name = os.path.basename(nbr_file)  # get the final component of reference filename (e.g LC08...B5)
    output_file_name = base_name.replace("NBR", "NBR_norm")  # replace "B5" with "NBR"
    output_file = os.path.join(directory, output_file_name)
    
    # convert to 8-bit format
    normalized_8bit = normalized_nbr.astype(np.uint8)  # Convert to 8-bit format
    
    # # save the normalized image
    # with rasterio.open(nbr_file) as src:
    #     profile = src.profile
    # profile.update(dtype=rasterio.float32, count=1)
    
    # with rasterio.open(output_file, 'w', **profile) as dst:
    #     dst.write(normalized_nbr.astype(rasterio.float32), 1)
    
    with rasterio.open(nbr_file) as src:
        profile = src.profile
        profile.update(dtype=np.uint8, count=1)  # Set dtype to uint8

        with rasterio.open(output_file, 'w', **profile) as dst:
            dst.write(normalized_8bit, 1)  # Write the 8-bit data
    
    # print(f"Normalized image saved to: {output_file}")
    
    # save as PNG (Normalize values to [0, 255] for PNG)
    png_output_path = output_file.replace('.TIF', '.png')

    # save PNG
    imageio.imwrite(png_output_path, normalized_8bit)
    
    print(f"Normalized image saved to: {png_output_path}")
    
    
# Main block to call the function
if __name__ == "__main__":
    # set up input and output paths
    # input_directory = 'experiments'  # replace with your NBR files directory
    # output_mean_file = 'experiments/mean_nbr_image.TIF'  # output for mean image
    # output_std_file = 'experiments/std_nbr_image.TIF'  # output for standard deviation image
    # input_normalized_file = 'experiments/002008_20200809/LC08_CU_002008_20200809_20210504_02_SR_NBR.TIF'  # input normalized image
    # output_normalized_file = 'experiments/normalized_image_1.TIF'  # output for normalized image

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process scenes to calculate NBR and save in each scene folder.')
    parser.add_argument('-i', '--input_dir', required=True,
                        help='Path to the base directory containing scene folders.', type=str)

    # Parse arguments
    args = parser.parse_args()
    base_dir = os.path.normpath(args.input_dir)
    
    # get the mean and the std nbr image
    print(base_dir)
    mean_nbr_image, std_nbr_image = calculate_mean_and_std_nbr_image(base_dir)
    
    # Process all scenes
    for scene_dir in os.listdir(base_dir):
        full_scene_dir = os.path.join(base_dir, scene_dir)
        if os.path.isdir(full_scene_dir):  # ensure it's a directory
            normalize_nbr(full_scene_dir, mean_nbr_image, std_nbr_image)
    
