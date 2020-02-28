#!/bin/bash

# Echo on
set -x

# Paths
DATA=data
PARSEME_PL=parseme_corpus_pl
SPLIT=split
OUT=out

# Re-create the splitting...
rm -r $DATA/$SPLIT
mkdir $DATA/$SPLIT

# ... and the output directories
rm -r $DATA/$OUT
mkdir $DATA/$OUT
for out_dir in 120 130 310 330 PCC
do
  mkdir $DATA/$OUT/$out_dir
done

# Split the .cupt files based on their source (PCC, 130-2, etc.)
python3 main.py split -i $DATA/$PARSEME_PL/*.cupt -o $DATA/$SPLIT
