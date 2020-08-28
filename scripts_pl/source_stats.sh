#!/bin/bash

# Args
if [ ! $# -eq 1 ]; then
  echo Usage: `basename $0` 'PARSEME_PL_CORPUS'
  echo
  exit
fi

data=$1

# Daily newspapers

newspaper_names="BrukowiecOchlanski|EkspressWieczorny|GazetaGoleniowska|GazetaKociewska|GazetaLubuska|GazetaMalborska|GazetaPomorska|GazetaTczewska|GazetaWroclawska|GlosPomorza|GlosSzczecinski|KurierKwidzynski|KurierSzczecinski|NIE|NowaTrybunaOpolska|Rzeczpospolita|SlowoPowszechne|SuperExpress|TrybunaLudu|TrybunaSlaska|ZycieINowoczesnosc|ZycieWarszawy"

echo "Daily newspapers:"

x1=`grep "# source_sent_id" $data/NKJP.cupt | cut -d' ' -f5 | grep "^130-" | wc -l`
x2=`grep "# source_sent_id" $data/PCC.cupt | wc -l`
x3=`grep "# orig_file_sentence" $data/PDB.cupt $data/pl-pdb-* | cut -d' ' -f4 | grep "^130-" | wc -l`
x4=`grep "# orig_file_sentence" $data/PDB.cupt $data/pl-pdb-* | cut -d' ' -f4 | grep -E $newspaper_names | wc -l`

echo $x1, $x2, $x3, $x4
echo $(($x1 + $x2 + $x3 + $x4))
