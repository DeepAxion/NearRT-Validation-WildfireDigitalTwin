# run these scripts in sequence to download, test, and organize Landsat BA data for a single ARD tile
bash download_one_tile.sh 24 16
bash test_one_tile.sh 24 16
bash organize_one_tile.sh 24 16

# or edit these scripts and run to download, test, and organize multiple tiles
# right now, they include all tiles for conus
bash download_multiple_tiles.sh (for Linux, type chmod +x download_one_tile.sh to grant execute permission)
bash test_multiple_tiles.sh
bash organize_multiple_tiles.sh
