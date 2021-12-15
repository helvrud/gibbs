#!/bin/bash

rm -r packages
cp -r ../packages .

docker build  -t miklakt/ubuntu-gibbs .

#docker run -it helvrud/ubuntu-gibbs /bin/bash

#docker tag espresso_latest kvint/espresso_latest
docker push miklakt/ubuntu-gibbs:latest

# In order to run the docker
#docker run -it --mount type=bind,source=/home/kvint/gibbs,target=//home/kvint/gibbs helvrud/ubuntu-gibbs /bin/bash

########################################################
# then on metacentrum run
#singularity build ubuntu-gibbs.img docker://miklakt/ubuntu-gibbs
#singularity shell ubuntu-gibbs.img
#	> cd /home/kvint/espresso/espresso/es-build
#	> cmake ..
#	> make -j4
