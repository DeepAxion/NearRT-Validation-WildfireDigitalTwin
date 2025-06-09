##delete corrupted .tar files, download and run tar_test.py again
##when all .tar files are downloaded and confirmed to not be corrupted, then run this script

#script to take .tar downloads of Landsat Burned Area Collection 2 data and organize the contents into subfolders
#renames the .png files so they appear in their directory in chronological order based on acquisition date
#generates stack.csv file

import os
import tarfile
import glob
import shutil
import argparse
import re

def extract_tar(in_tar, out_dir, new_tar_folder):
    print('Extracting files from .tar in', in_tar)
    
    try:
        tar = tarfile.open(in_tar, mode='r:*')
    except Exception as e:
        print('ERROR opening:', in_tar, '-', e)
        return  # skip if cannot open
    
    tar_members = tar.getmembers()
    
    for member in tar_members:
        tm = member.name
        
        # using regex to match the filename and extract the acquisition date 
        match = re.search(r'LC0[8-9]_CU_(\d{6})_(\d{8})_\d{8}_\d{2}_SR_B([1-9])', tm)
        if match:
            tile = match.group(1)  # capture the tile number
            acquisition_date = match.group(2) # get acquisition date
            band_number = match.group(3)  # Capture the band number (e.g., '1', '2', etc.)
            
            # define folder name based on tile number and acquisition date
            scene_folder_name = f"{tile}_{acquisition_date}"
            scene_output_dir = os.path.join(out_dir, scene_folder_name)
            os.makedirs(scene_output_dir, exist_ok=True)
            
            # extract the file (unzip)
            tar.extract(member, scene_output_dir)
            print(f'Extracted {tm} to {scene_output_dir}')
        else:
            pass  # skip is file doesn't match
    
    tar.close()
    
    # move .tar to a new folder within the tile folder
    print('Moving', in_tar, 'to new folder')
    tar_path = os.path.abspath(in_tar)
    shutil.move(tar_path, new_tar_folder)

if __name__ == '__main__':
    # Set up command-line argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--tar_directory', required=True,
                        help='Path to folder where .tar files are located. (Required)', 
                        type=str, dest='tar_directory')

    # Parse command-line arguments
    args = parser.parse_args()
    tar_dir = os.path.normpath(args.tar_directory)

    # create a new directory within the tile folder for moved .tar files
    new_tar_folder = os.path.join(tar_dir, 'tar_downloads')
    os.makedirs(new_tar_folder, exist_ok=True)

    # get list of .tar files to extract
    tar_files_list = glob.glob(os.path.join(tar_dir, '*.tar'))

    # lists for tracking files that throw errors
    errors_opening = []

    # loop through each .tar file (dirs) and extract contents
    for file in tar_files_list:
        try:
            extract_tar(file, tar_dir, new_tar_folder)
        except Exception as e:
            print(f'Error processing {file}: {e}')
            errors_opening.append(file)

    # print error summary
    print('ERRORS opening the following .tar files:', errors_opening)
