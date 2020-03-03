#!/bin/bash

# Args
if [ ! $# -eq 4 ]; then
  echo Usage: `basename $0` 'MODEL' 'INPUT-DIR' 'TMP-DIR' 'OUTPUT-DIR'
  echo
  exit
fi

UDPIPE_PL=$1
# =udpipe/models/polish-pdb-ud-2.5-191206.udpipe
INP=$2
TMP=$3
OUT=$4

# Echo on
set -x

for xz_file in $INP/*.conllu.xz
do
  xz_file="$(basename -- $xz_file)"
  cp $INP/$xz_file $TMP/inp.conllu.xz
  unxz $TMP/inp.conllu.xz
  python3 main.py parse --raw -i $TMP/inp.conllu -m $UDPIPE_PL > $TMP/out.conllu
  xz $TMP/out.conllu
  mv $TMP/out.conllu.xz $OUT/$xz_file
  # Clean-up
  rm $TMP/*conllu*
done
