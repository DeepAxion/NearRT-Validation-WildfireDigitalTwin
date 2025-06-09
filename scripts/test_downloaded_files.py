#script to test if .tar downloads can be opened

import os
import argparse
import tarfile
import glob

def tar_test(tar):
    
    print('Testing:', tar)
    
    try:
        tar_test = tarfile.open(tar, mode='r:*')
    except:
        print('ERROR opening:', tar)
              
    tar_test.close()

if __name__ == '__main__':
    #create command-line argument(s) - specify directory with .tar files to try opening
    #create and set up parser
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--tar_directory', required=True, help='Path to folder where .tar files are located. (Required)', type=str, dest='tar_directory')    

    #store values in array
    args = parser.parse_args()

    #assign tar_directory argument to variable
    tar_dir = args.tar_directory
    
    #list of .tar files to try opening
    tar_files_list = glob.glob(os.path.join(tar_dir, '*.tar'))
    
    #list for files that throw errors
    errors = []
    
    for file in tar_files_list:
        try:
            tar_test(file)
        except:
            error = file
            errors.append(error)
    
    if len(errors) == 0:
        print('No errors!')
    else:
        print('Errors opening the following .tar files:', errors)
    
