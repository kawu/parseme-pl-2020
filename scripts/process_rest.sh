#!/bin/bash

# Echo on
set -x

# Paths
DATA=data
# UDPIPE_PL=udpipe/models/polish-pdb-ud-2.5-191206.udpipe
# PARSEME_PL=parseme_corpus_pl
SPLIT=split
PDB=PDB/UD_Polish-PDB
TO_CUPT=./utils/st-organizers/to_cupt.py

# We assume that splitting is already performed
# (see the prepare.sh script)

PREFS="120 310 330"
for pref in $PREFS
do
  OUT=out/$pref
  FILES=$DATA/$SPLIT/$pref-*
  for cupt_file in $FILES
  do
    echo CUPT: $cupt_file
    cupt_file="$(basename -- $cupt_file)"
    # Align the CUPT part with PDB
    python3 main.py align -d $DATA/$SPLIT/$cupt_file -s $DATA/$PDB/*.conllu > $DATA/$OUT/pdb_aligned.conllu
    # Merge the original .cupt file with aligned PDB.
    cd $DATA
    $TO_CUPT --input $SPLIT/$cupt_file --conllu $OUT/pdb_aligned.conllu --lang PL > $OUT/$pref.cupt
    rm $OUT/pdb_aligned.conllu
    cd ..
  done
done
