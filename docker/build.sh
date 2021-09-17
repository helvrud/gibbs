#!/bin/bash
#if [[ $# -eq 0 ]] ; then
#    echo 'You need to pass as an arguments: data = format YYYY_MM_DD and electro = 1 or 0 '
#    exit 0
#fi
#echo "Builder v0.0.4"

#date=$1
#echo "date: " ${date}
#echo "electro: "$2
#if [ $2 == 1 ]
#then
#    echo "Electro"
#    espresso_config="myconfig_with_electro.hpp"
#else
#    echo "NO Electro"
#    espresso_config="myconfig_without_electro.hpp"

#fi
#cp espresso_config/configs/${espresso_config} espresso_config/myconfig.hpp
#echo "Building..."
#name="es-ubu_cupy3_"${date}
#echo "Container name: "${name}
#docker build -t ${name} .
docker build --no-cache -t helvrud/ubuntu .

#docker tag espresso_latest kvint/espresso_latest
docker push helvrud/ubuntu

########################################################
# then on metacentrum run
singularity build ubuntu.img docker://helvrud/ubuntu
singularity shell -B /storage/brno2/home/kvint:/home/kvint ubuntu.img
	> cd /home/kvint/espresso/espresso/es-build
	> cmake ..
	> make -j4
