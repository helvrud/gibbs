latexdiff orig.tex edit.tex  > diff.tex
latexmk -pdf -f diff.tex
evince diff.pdf
