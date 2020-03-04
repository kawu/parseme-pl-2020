#!/bin/bash

# Echo on
set -x

# Paths
DATA=data
EXTRA=extra
UDPIPE_PL=udpipe/models/polish-pdb-ud-2.5-191206.udpipe
PARSEME_PL=parseme_corpus_pl
PDB=PDB/UD_Polish-PDB
SPLIT=split
OUT=out
TO_CUPT=./utils/st-organizers/to_cupt.py

# Determine tagset conversion maps
# python3 main.py tagset -i $DATA/$PDB/*.conllu --upos $DATA/$OUT/upos_conv.txt --feats $DATA/$OUT/feat_conv.txt

# Perform conversion
python3 main.py convert -i $DATA/$SPLIT/NKJP.cupt --upos $EXTRA/upos_conv.txt --feats $EXTRA/feat_conv.txt --qub $EXTRA/qub_conv.txt --manual $EXTRA/manual_conv.txt > $DATA/$OUT/input.cupt

# Reparse (syntax level only)
python3 main.py parse --disable-tagger -i $DATA/$OUT/input.cupt -m $DATA/$UDPIPE_PL > $DATA/$OUT/udpipe.conllu

# Merge the input .cupt file with UDPipe's output.
cd $DATA
$TO_CUPT --input $OUT/input.cupt --conllu $OUT/udpipe.conllu --lang PL > $OUT/NKJP.cupt
rm $OUT/input.cupt
rm $OUT/udpipe.conllu
cd ..
