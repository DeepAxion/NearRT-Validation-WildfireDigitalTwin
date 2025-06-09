##delete corrupted .tar files, download and run tar_test.py again
##when all .tar files are downloaded and confirmed to not be corrupted, then run this script

#script to take .tar downloads of Landsat Burned Area Collection 2 data and organize the contents into subfolders
#renames the .png files so they appear in their directory in chronological order based on acquisition date
#generates stack.csv file

import os
import argparse
import glob
import tarfile
import time
import shutil
import pandas as pd
from xml.dom import minidom

# extract BP.tif, BC.tif, .png, and .xml files from .tar and put them in indiviual folders within a tile folder
def extract_tar(in_tar, out_dir, new_tar_folder):
    
    print('Exctracting files from .tar in', in_tar)
    
    #extract the three files from .tar
    try:
        tar = tarfile.open(in_tar, mode='r:*')
    except:
        print('ERROR opening:', in_tar)
        
    tar_members = tar.getmembers()
    
    for i in range(0, len(tar_members)):
        tm = tar_members[i].name
        
        if 'BP.TIF' in tm:
            tar.extract(tm, os.path.join(out_dir, 'scene_BP'))
        elif 'BC.TIF' in tm:
            tar.extract(tm, os.path.join(out_dir, 'scene_BC'))
        elif '.png' in tm:
            tar.extract(tm, os.path.join(out_dir, 'scene_png'))
        elif '.xml' in tm:
            tar.extract(tm, os.path.join(out_dir, 'metadata'))
        elif 'BA.json' in tm:
            tar.extract(tm, os.path.join(out_dir, 'BA_json'))
        elif 'BA_stac.json' in tm:
            tar.extract(tm, os.path.join(out_dir, 'BA_stac_json'))
        else:
            pass
        
    tar.close()
    
    #move .tar to new folder within tile folder
    print('Moving', in_tar, 'to new folder')
    tar_path = os.path.abspath(in_tar)
    shutil.move(tar_path, new_tar_folder)
    
# generate stack.csv
def generate_stack_csv(in_dir, tar_folder):
    
     #list of xml files to use
     meta_folder = os.path.join(tar_folder, 'metadata')
     #xml_files = sorted(glob.glob(os.path.join(meta_folder, '*.xml')))
     xml_files = glob.glob(os.path.join(meta_folder, '*.xml'))
     
     #create empty dataframe
     stack = pd.DataFrame()
     
     #get data
     for xml in xml_files:
         doc = minidom.parse(xml)

         #file
         ARD_ID = doc.getElementsByTagName('ARD_PRODUCT_ID')[0]
         filename = ARD_ID.firstChild.data
         
         #H and V
         h = doc.getElementsByTagName('TILE_GRID_H')[0]
         hh = h.firstChild.data
         v = doc.getElementsByTagName('TILE_GRID_V')[0]
         vv = v.firstChild.data
         
         #path and row
         p = doc.getElementsByTagName('WRS_PATH')[0]
         path = p.firstChild.data
         r = doc.getElementsByTagName('WRS_ROW')[0]
         row = r.firstChild.data
         
         #sensor
         spacecraft = doc.getElementsByTagName('SPACECRAFT_ID')[0]
         sensor = spacecraft.firstChild.data[-1:]
         
         #full acquisition date, year, month, and day acquired
         acquisition_date = doc.getElementsByTagName('DATE_ACQUIRED')[0]
         a_date = acquisition_date.firstChild.data
         year = a_date[0:4]
         month = a_date[5:7]
         day = a_date[8:]
         
         #julian
         struct_time = time.strptime(a_date, '%Y-%m-%d')
         julian = struct_time[7]
         
         #RMSE
         geometric_rmse_model = doc.getElementsByTagName('GEOMETRIC_RMSE_MODEL')
         if len(geometric_rmse_model) > 0: 
             geometric_rmse_model = doc.getElementsByTagName('GEOMETRIC_RMSE_MODEL')[0]
             RMSE = float(geometric_rmse_model.firstChild.data)
             
         #not sure exactly what to put here - some .xmls do not have this data    
         else:
             RMSE = 'NA'
            
         #cloud cover
         cloud_cover = doc.getElementsByTagName('CLOUD_COVER')[0]
         cloudcover = float(cloud_cover.firstChild.data)
         
         #snow and ice
         snow_ice = doc.getElementsByTagName('SNOW_ICE_COVER')[0]
         snowice = float(snow_ice.firstChild.data)
         
         #fill
         fill_ = doc.getElementsByTagName('FILL')[0]
         fill = float(fill_.firstChild.data)
         
         #instrument
         instru = doc.getElementsByTagName('SENSOR_ID')[0]
         instrument = instru.firstChild.data
         
         #production date
         production_date = doc.getElementsByTagName('DATE_PRODUCT_GENERATED')[0]
         p_date = production_date.firstChild.data
         
         ###not sure exactly what the output column means but making it 1 for every row so it can be read by QA tool
         output = 1
         
         #add data to stack.csv
         df_temp = pd.DataFrame(data={'FILE': filename, 'HH': hh, 'VV': vv, 'PATH': path, 'ROW': row, \
                                      'SENSOR': sensor, 'YEAR': year, 'MONTH': month, 'DAY': day, \
                                          'JULIAN': julian, 'RMSE': RMSE, 'CLOUD_COVER': cloudcover, \
                                              'SNOW_ICE': snowice, 'FILL': fill, 'INSTRUMENT': instrument, 'ACQUISITION_DATE': a_date, \
                                                  'PRODUCTION_DATE': p_date, 'OUTPUT': output}, index=[0])
             
         df_temp = df_temp.set_index('FILE')
         #stack = stack.append(df_temp)
         stack = pd.concat([stack, df_temp])
    
     #write dataframe to csv
     stack.sort_values(by='ACQUISITION_DATE', axis=0, inplace=True)
     stack.to_csv(os.path.join(tar_folder, 'stack_new.csv'))

# change .png file names to acquistion date
def png_name_change(png, tar_folder):
    new_png_name = os.path.basename(png)[15:23] + 'L' + os.path.basename(png)[0:4]
    os.rename(png, os.path.join(tar_folder, 'scene_png', new_png_name + '.png'))
    

if __name__ == '__main__':
    #create command-line argument(s) - specify directory with .tar files for extraction and organization
    #create and set up parser
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--tar_directory', required=True, help='Path to folder where .tar files are located. (Required)', type=str, dest='tar_directory')    

    #store values in array
    args = parser.parse_args()

    #assign tar_directory argument to variable
    tar_dir = os.path.normpath(args.tar_directory)

    #make new directory within tile folder for .tars
    new_tar_folder = os.path.join(tar_dir, 'tar_downloads')
    
    if not os.path.exists(new_tar_folder):
        os.mkdir(new_tar_folder)
    
    #list of .tar files to extract from
    tar_files_list = glob.glob(os.path.join(tar_dir, '*.tar'))

    #lists for files that throw errors
    errors1 = []
    errors2 = []
    
    #loop extract_tar over list
    for file in tar_files_list:
        try:
            extract_tar(file, tar_dir, new_tar_folder)
        except:
            error = file
            errors1.append(error)
            
    png_files_list = glob.glob(os.path.join(tar_dir, 'scene_png', '*.png'))

    for file in png_files_list:
        print(file)
        try:
            png_name_change(file, tar_dir)
        except:
            error = file
            errors2.append(error)
    
    generate_stack_csv(tar_dir, tar_dir)
    
    print('ERRORS opening the following .tar files:', errors1)
    print('Could not rename file (already exists):', errors2)
