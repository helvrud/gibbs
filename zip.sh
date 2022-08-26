#!/bin/bash

#rm -r zip/figs || mkdir -p zip/figures

# chek that esi is up to date
#latexmk -pdf scf-gel
#latexmk -pdf esi

name="gibbs"

main_file=$name".tex"
files="definitions.tex gibbs.pdf gibbs.bbl esi.pdf esi.tex"
figs=`grep 'includegraphics' $main_file | grep -v "grep"| grep -v '%.include' |sed 's/^.*\\includegraphics.*{fig/fig/' |  grep eps | sed 's/\.eps.*$/\.eps/' | sed 's/\}//g'`
figs="$figs `grep 'includegraphics' $main_file          | grep -v '%.include' |sed 's/^.*\\includegraphics.*{fig/fig/' |  grep png | sed 's/\.png.*$/\.png/' | sed 's/\}//g'`"
figs="$figs `grep 'includegraphics' $main_file          | grep -v '%.include' |sed 's/^.*\\includegraphics.*{fig/fig/' |  grep pdf | sed 's/\.pdf.*$/\.pdf/' | sed 's/\}//g'`"
#echo "figs: $figs";

for f in $figs; do echo $f; done

zip $name.zip $main_file $files $figs

echo "Test whether it works"
mkdir -p try
rm -r try/* 
echo "wd: `pwd`"
cd try
echo "wd: `pwd`"
cp ../$name.zip ./
unzip $name.zip
echo "wd: `pwd`"
latexmk -pdf $name && evince $name".pdf"


