#!/bin/bash

# # Args
# if [ ! $# -eq 1 ]; then
#   echo Usage: `basename $0` 'INPUT-DIR'
#   echo
#   exit
# fi

INP="$@"

# Echo on
# set -x

for xz_file in $INP
do
#   echo $xz_file
  xz_file="$(basename -- $xz_file)"
  file="${xz_file%.*}"
  unxz $INP/$xz_file
  python3 main.py words -i $INP/$file
  xz $INP/$file
done
