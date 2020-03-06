#!/bin/bash

# Echo on
set -x

# Paths
DATA=data
CONV=conv
UDPIPE_PL=udpipe/models/polish-pdb-ud-2.5-191206.udpipe
PDB=PDB/UD_Polish-PDB
SPLIT=split
OUT=out
TO_CUPT=./utils/st-organizers/to_cupt.py

# Determine tagset conversion maps
# python3 main.py tagset -i $DATA/$PDB/*.conllu --upos $DATA/$OUT/upos_conv.txt --feats $DATA/$OUT/feat_conv.txt

# Perform conversion
python3 main.py convert -i $DATA/$SPLIT/NKJP.cupt --upos $CONV/upos_conv.txt --feats $CONV/feat_conv.txt --qub $CONV/qub_conv.txt --manual $CONV/manual_conv.txt > $DATA/$OUT/input.cupt

# Reparse (syntax level only)
python3 main.py parse --disable-tagger -i $DATA/$OUT/input.cupt -m $DATA/$UDPIPE_PL > $DATA/$OUT/NKJP.cupt
# python3 main.py parse --disable-tagger -i $DATA/$OUT/input.cupt -m $DATA/$UDPIPE_PL > $DATA/$OUT/udpipe.conllu
rm $DATA/$OUT/input.cupt

# # Merge the input .cupt file with UDPipe's output.
# cd $DATA
# $TO_CUPT --input $OUT/input.cupt --conllu $OUT/udpipe.conllu --lang PL > $OUT/NKJP.cupt
# rm $OUT/udpipe.conllu
# cd ..
