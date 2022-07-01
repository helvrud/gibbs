latexdiff gibbs_old.tex gibbs.tex  > diff.tex
latexmk -pdf -f diff.tex
evince diff.pdf
