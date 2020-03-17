#!/bin/bash

# Echo on
set -x

# Paths
DATA=data_de
PARSEME=parseme_corpus_de
UD=UD_German-GSD
SPLIT=split
OUT=out

# Re-create the splitting...
rm -r $DATA/$SPLIT
mkdir $DATA/$SPLIT

# ... and the output directory
rm -r $DATA/$OUT
mkdir $DATA/$OUT

# Split the .cupt files based on their source (PCC, 130-2, etc.)
python3 main.py split -i $DATA/$PARSEME/*.cupt --pdb $DATA/$UD/*.conllu -o $DATA/$SPLIT
