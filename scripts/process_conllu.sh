#!/bin/bash

# Echo on
set -x

# Paths
DATA=data
UDPIPE_PL=udpipe/models/polish-pdb-ud-2.5-191206.udpipe
INP=...
TMP=...
OUT=...

for xz_file in $DATA/$INP/*.conllu.xz
do
  xz_file="$(basename -- $xz_file)"
  cp $DATA/$INP/$xz_file $DATA/$TMP/inp.conllu.xz
  unxz $DATA/$TMP/inp.conllu.xz
  python3 main.py parse --raw -i $DATA/$TMP/inp.conllu -m $DATA/$UDPIPE_PL > $DATA/$TMP/out.conllu
  xz $DATA/$TMP/out.conllu
  mv $DATA/$TMP/out.conllu.xz $DATA/$OUT/$xz_file
done
