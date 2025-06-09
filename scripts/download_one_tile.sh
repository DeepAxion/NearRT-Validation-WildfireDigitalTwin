#!/bin/bash
TILE_H=$1
TILE_V=$2
DATE=$3
DATASET=$4
SPACECRAFT=$5
DESTINATION=$6
# USER=Bakhoi2003
# PW=Khoinguyen2003
# TOKEN=UBFOvHpcmewTpVh4f!U6!c_iH8p4mwwGS7wCdTxAkMfJpIOd70S7XA@5MQWPwId8
TILE_LONG=`printf "h%0.3dv%0.3d\n" $TILE_H $TILE_V`


# python -O m2m_download.py --acq-date $DATE --dataset landsat_ba_tile_c2 --user $USER --password $PW -d D:/BA_C2_CU/downloads/$TILE_LONG --region CU --horizontal $TILE_H --vertical $TILE_V
python3 -O m2m_download.py --acq-date $DATE \
			--dataset $DATASET\
			--spacecraft $SPACECRAFT \
        	-cc 10 \
			-d $DESTINATION/$TILE_LONG/ \
			--region CU \
			--horizontal $TILE_H --vertical $TILE_V\
		    -search-only
