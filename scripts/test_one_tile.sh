#!/bin/bash
TILE_H=$1
TILE_V=$2
TILE_LONG=`printf "h%0.3dv%0.3d\n" $TILE_H $TILE_V`

python test_downloaded_files.py -d D:/BA_C2_CU/downloads/$TILE_LONG
