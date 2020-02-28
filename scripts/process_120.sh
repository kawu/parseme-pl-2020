#!/bin/bash

# Echo on
set -x

# Paths
DATA=data
# UDPIPE_PL=udpipe/models/polish-pdb-ud-2.5-191206.udpipe
# PARSEME_PL=parseme_corpus_pl
SPLIT=split
PDB=PDB/UD_Polish-PDB
D120=out/120
TO_CUPT=./utils/st-organizers/to_cupt.py

# We assume that splitting is already performed
# (see the process_pcc.sh script)

# Align the 120 part with PDB
python3 main.py align -d $DATA/$SPLIT/120-.cupt -s $DATA/$PDB/*.conllu > $DATA/$D120/pdb_aligned.conllu

# Merge the original .cupt 120 file with aligned PDB.
cd $DATA
$TO_CUPT --input $SPLIT/120-.cupt --conllu $D120/pdb_aligned.conllu --lang PL > $D120/120_pdb.cupt
