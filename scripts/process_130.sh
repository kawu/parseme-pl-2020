#!/bin/bash

# Echo on
set -x

# Paths
DATA=data
UDPIPE_PL=udpipe/models/polish-pdb-ud-2.5-191206.udpipe
PARSEME_PL=parseme_corpus_pl
SPLIT=split
D130=out/130
TO_CUPT=./utils/st-organizers/to_cupt.py

for cupt_file in $DATA/$SPLIT/130-*
do
  cupt_file="$(basename -- $cupt_file)"
  stem="${cupt_file%.*}"
  python3 main.py parse --disable-tagger -i $DATA/$SPLIT/$cupt_file -m $DATA/$UDPIPE_PL > $DATA/$D130/udpipe.conllu

  # Merge the original .cupt PCC file with UDPipe's output.
  cd $DATA
  $TO_CUPT --input $SPLIT/$cupt_file --conllu $D130/udpipe.conllu --lang PL > $D130/$stem.cupt
  rm $D130/udpipe.conllu
  cd ..
done
