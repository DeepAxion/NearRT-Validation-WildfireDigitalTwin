#!/bin/bash
LOCATION=$1
DATE=$2
DATASET=$3
PLATFORM=$4
DESTINATION=$5
# USER=Bakhoi2003
# PW=Khoinguyen2003
# TOKEN=UBFOvHpcmewTpVh4f!U6!c_iH8p4mwwGS7wCdTxAkMfJpIOd70S7XA@5MQWPwId8
TILE_LONG=`printf "h%0.3dv%0.3d\n" $TILE_H $TILE_V`


# python -O m2m_download.py --acq-date $DATE --dataset landsat_ba_tile_c2 --user $USER --password $PW -d D:/BA_C2_CU/downloads/$TILE_LONG --region CU --horizontal $TILE_H --vertical $TILE_V
python3 -O m2m_download.py --acq-date $DATE \
                        --tile-number $LOCATION\
			--dataset $DATASET\
			--platform $PLATFORM \
			-d $DESTINATION/$/ \
			--region CU \
                        --search-only\
			
