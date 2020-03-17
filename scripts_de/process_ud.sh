#!/bin/bash

# Echo on
set -x

# Params
LANG=DE
DATA=data_de
SPLIT=split
UD=UD_German-GSD
TO_CUPT=./utils/st-organizers/to_cupt.py
OUT=out

# We assume that splitting is already performed
# (see the prepare.sh script)

# Align the CUPT part with UD
python3 main.py align -d $DATA/$SPLIT/UD.cupt -s $DATA/$UD/*.conllu > $DATA/$OUT/ud_aligned.conllu

# Merge the original .cupt file with aligned UD.
cd $DATA
$TO_CUPT --input $SPLIT/UD.cupt --conllu $OUT/ud_aligned.conllu --lang $LANG > $OUT/UD.cupt
rm $OUT/ud_aligned.conllu
cd ..
