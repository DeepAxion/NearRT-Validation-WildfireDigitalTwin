#!/bin/bash
TILE_H=$1
TILE_V=$2
TILE_LONG=`printf "h%0.3dv%0.3d\n" $TILE_H $TILE_V`
DIR=$3

python3 calculate_nbr.py -i $DIR/$TILE_LONG
