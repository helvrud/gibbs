#!/bin/bash
# set paths / dirs
_path="$HOME/gibbs/scripts/data/"
 
# binary file name
_unison=/usr/bin/unison-2.48-gtk
 
# server names 
# sync server1.cyberciti.com with rest of the server in cluster
_rserver="owain.natur.cuni.cz"
 
${_unison} -batch "${p}"  "ssh://${_rserver}/${_path}"

