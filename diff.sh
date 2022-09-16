latexdiff gibbs_mdpi_submission1.tex gibbs.tex  > diff.tex
latexmk -pdf -f diff.tex
evince diff.pdf
