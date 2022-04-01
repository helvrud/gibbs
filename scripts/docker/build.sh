#!/bin/bash

docker build  -t helvrud/ubuntu-gibbs2 .

#docker run -it helvrud/ubuntu-gibbs /bin/bash

#docker tag espresso_latest kvint/espresso_latest
docker push helvrud/ubuntu-gibbs2:latest

# In order to run the docker
#docker run -it --mount type=bind,source=/home/kvint/gibbs,target=//home/kvint/gibbs helvrud/ubuntu-gibbs2 /bin/bash

########################################################
# then on metacentrum run
#singularity build ubuntu-gibbs2.img docker://helvrud/ubuntu-gibbs2
#singularity shell ubuntu-gibbs2.img
#	> cd /home/kvint/espresso/espresso/es-build
#	> cmake ..
#	> make -j4
