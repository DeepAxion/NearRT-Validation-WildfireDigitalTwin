import os
import numpy as np
import rasterio

def calculate_mean_nbr_image(directory, output_path):
    # Initialize a list to hold all NBR data arrays
    nbr_stack = []

    # Iterate over files in the directory to find NBR TIF files
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith("NBR.TIF"):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")

                # Read the NBR file using rasterio
                with rasterio.open(file_path) as src:
                    nbr_data = src.read(1).astype(float)
                    
                    # Mask out the no-data values and replace with NaN
                    nbr_data = np.where((nbr_data == src.nodata) | np.isinf(nbr_data), np.nan, nbr_data)

                    # Add the processed NBR data to the stack
                    nbr_stack.append(nbr_data)
    
    if nbr_stack:
        # Stack all NBR arrays along a new third axis (depth)
        nbr_stack = np.stack(nbr_stack, axis=0)
        
        # Calculate the mean along the depth axis, ignoring NaNs
        mean_nbr_image = np.nanmean(nbr_stack, axis=0)
	
        # Handle the case where the entire pixel stack was NaN
        mean_nbr_image = np.where(np.isnan(mean_nbr_image), np.nan, mean_nbr_image)

        # Save the mean NBR image to a new file
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=mean_nbr_image.shape[0],
            width=mean_nbr_image.shape[1],
            count=1,
            dtype='float32',
            crs=src.crs,
            transform=src.transform
        ) as dst:
            dst.write(mean_nbr_image, 1)
        
        print(f"Mean NBR image saved to: {output_path}")
    else:
        print("No valid NBR values found.")

# Main execution
if __name__ == "__main__":
    directory = 'Landsat_AUGCOMP'  # Update this path
    output_file = 'Landsat_AUGCOMP/mean_nbr.TIF'

    calculate_mean_nbr_image(directory, output_file)
