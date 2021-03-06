#!/bin/bash

# Echo on
set -x

# Paths
DATA=data
UDPIPE_PL=udpipe/models/polish-pdb-ud-2.5-191206.udpipe
SPLIT=split
OUT=out
TO_CUPT=./utils/st-organizers/to_cupt.py

# We assume that splitting is already performed
# (see the prepare.sh script)

# Re-parse with UDPipe the PCC part
python3 main.py parse -i $DATA/$SPLIT/PCC.cupt -m $DATA/$UDPIPE_PL > $DATA/$OUT/PCC.cupt

# # Merge the original .cupt PCC file with UDPipe's output.
# cd $DATA
# $TO_CUPT --input $SPLIT/PCC.cupt --conllu $OUT/udpipe.conllu --lang PL > $OUT/PCC.cupt
# rm $OUT/udpipe.conllu
# cd ..
