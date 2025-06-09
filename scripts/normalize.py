import os
import numpy as np
import rasterio

def calculate_mean_nbr(directory):
    nbr_values = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith("NBR.TIF"):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")

                # Read the NBR file using rasterio
                with rasterio.open(file_path) as src:
                    nbr_data = src.read(1)

                    # Mask out the no-data values
                    nbr_data = np.where((nbr_data == src.nodata) | np.isinf(nbr_data), np.nan, nbr_data)

                    # Append non-NaN values to the list
                    valid_nbr_values = nbr_data[~np.isnan(nbr_data)]
                    nbr_values.extend(valid_nbr_values)

    # Calculate the mean of all NBR values
    if nbr_values:
        mean_nbr = np.nanmean(nbr_values)
        std_nbr = np.nanstd(nbr_values)  # Calculate standard deviation
        print(f"Mean NBR value: {mean_nbr}")
        print(f"Standard deviation of NBR values: {std_nbr}")

        return mean_nbr, std_nbr
    else:
        print("No valid NBR values found.")
        return None, None

def normalize_nbr_image(image_path, mean_nbr, std_nbr, output_path):
    with rasterio.open(image_path) as src:
        nbr_data = src.read(1).astype(float)

        # Replace no-data values with NaN
        nbr_data = np.where(nbr_data == src.nodata, np.nan, nbr_data)

        # Normalize the NBR data
        normalized_nbr = (nbr_data - mean_nbr) / std_nbr

        # Save the normalized NBR data to a new file
        with rasterio.open(
            output_path, 
            'w', 
            driver='GTiff',
            height=src.height,
            width=src.width,
            count=1,
            dtype='float32',
            crs=src.crs,
            transform=src.transform
        ) as dst:
            dst.write(normalized_nbr, 1)
        print(f"Normalized image saved to: {output_path}")

# Main execution
if __name__ == "__main__":
    directory = 'Landsat_AUGCOMP'  # Update this path
    image_to_normalize = 'Landsat_AUGCOMP/h002v008/002008_20200825/LC08_CU_002008_20200825_20210504_02_SR_NBR.TIF'  # Update this path
    output_path = 'Landsat_AUGCOMP/h002v008/002008_20200825/normalized_nbr.TIF'

    mean_nbr, std_nbr = calculate_mean_nbr(directory)
    
    if mean_nbr is not None and std_nbr is not None:
        normalize_nbr_image(image_to_normalize, mean_nbr, std_nbr, output_path)

