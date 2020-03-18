#!/bin/bash

# Echo on
set -x

# Paths
DATA=data_de
UDPIPE_MODEL=udpipe/models/german-gsd-ud-2.5-191206.udpipe
SPLIT=split
OUT=out
TO_CUPT=./utils/st-organizers/to_cupt.py

# We assume that splitting is already performed
# (see the prepare.sh script)

# Re-parse with UDPipe the PCC part
python3 main.py parse --raw -i $DATA/$SPLIT/OTHER.cupt -m $DATA/$UDPIPE_MODEL > $DATA/$OUT/udpipe.conllu

# Merge the original .cupt PCC file with UDPipe's output.
cd $DATA
$TO_CUPT --input $SPLIT/OTHER.cupt --conllu $OUT/udpipe.conllu --lang DE > $OUT/OTHER.cupt
rm $OUT/udpipe.conllu
cd ..
