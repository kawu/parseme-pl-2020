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
OUT=out

# We assume that splitting is already performed
# (see the prepare.sh script)

# Align the CUPT part with PDB
python3 main.py align -d $DATA/$SPLIT/PDB.cupt -s $DATA/$PDB/*.conllu > $DATA/$OUT/pdb_aligned.conllu

# Merge the original .cupt file with aligned PDB.
cd $DATA
$TO_CUPT --input $SPLIT/PDB.cupt --conllu $OUT/pdb_aligned.conllu --lang PL > $OUT/PDB.cupt
rm $OUT/pdb_aligned.conllu
cd ..
