#!/bin/bash
TILE_H=$1
TILE_V=$2
TILE_LONG=`printf "h%0.3dv%0.3d\n" $TILE_H $TILE_V`
TYPE=$3
DIR=$4

# rm $DIR/$TILE_LONG/scene_png/*.png
rm $DIR/$TILE_LONG/tar_downloads/*.tar
rm $DIR/$TILE_LONG/stack_new.csv

python3 organize_C2_tar_download_${TYPE}.py -d $DIR/$TILE_LONG
