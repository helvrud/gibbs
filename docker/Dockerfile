# Dockerfile for espresso 4.1

FROM ubuntu:focal   
LABEL Oleg Rud <oleg.rud@natur.cuni.cz>
ENV DEBIAN_FRONTEND noninteractive


RUN useradd -ms /bin/bash kvint
RUN useradd -ms /bin/bash kazakov
RUN useradd -ms /bin/bash ml
RUN apt-get update
RUN apt-get install -y python3-pip
WORKDIR /home/kvint




ENV USERNAME kvint
COPY .bashrc /home/kvint
COPY env.rc /home/kvint

COPY packages/ /home/kvint/

RUN ls /home/kvint
RUN ls .
RUN ls ~
CMD pip3 install /home/kvint/socket_server/
CMD pip3 install /home/kvint/montecarlo/



# RUN apt update && apt-get install -y \
#    libgl1-mesa-dev \ 
#    libglu1-mesa-dev \
#    freeglut3-dev \
#    libgles2-mesa-dev
#
####
#### You should also search 'UBUNTU_PKG_NAME = "nvidia-367"' and replace it to 'UBUNTU_PKG_NAME = "nvidia"'
#### for all matched files in the NVIDIA_CUDA-8.0_Samples folder to make it works.
####
# RUN mkdir /usr/lib/nvidia && \
#    ### solve for  /usr/bin/ld: cannot find -lnvcuvid \
#    ### 3_Imaging/cudaDecodeGL \
#    ln -s /usr/local/nvidia/lib64/libnvcuvid.so.1 /usr/lib/nvidia/libnvcuvid.so && \
#    ### solve for >>> WARNING - libEGL.so not found, please install libEGL.so <<< \
#    ### 3_Imaging/EGLStreams_CUDA_Interop \
#    ln -s /usr/local/nvidia/lib64/libEGL.so.1 /usr/lib/nvidia/libEGL.so && \
#    ### solve for >>> WARNING - libGLES.so not found, please install libGLES.so <<< \
#    ### 2_Graphics/simpleGLES_EGLOutput \
#    ### 2_Graphics/simpleGLES \
#    ### 2_Graphics/simpleGLES_screen \
#    ### 5_Simulations/nbody_opengles \
#    ### 5_Simulations/fluidsGLES \
#    ### 5_Simulations/nbody_screen \
#    ln -s /usr/local/nvidia/lib64/libGLESv2_nvidia.so.2 /usr/lib/nvidia/libGLESv2.so

RUN apt-get install -y \
    apt-utils \
    cmake \
    build-essential \
    curl \
    pkg-config \
    openmpi-bin libopenmpi-dev \
    libgsl-dev \
    clang \
    libfftw3-dev \
    libboost-dev libboost-serialization-dev libboost-mpi-dev libboost-filesystem-dev libboost-test-dev \
    libgsl-dev \
    cython3 python3 python3-numpy python3-scipy python3-h5py python3-tqdm python3-sphinx python3-pip \
    lcov \
    git \
    vim \
    pep8 pylint3 \
    doxygen \
    libhdf5-serial-dev \
    libpython3-dev \
    libhdf5-openmpi-dev \
    libhdf5-dev \
    ccache \
    python3-scipy \
    python3-numpy \
    python3-virtualenv \
    python3-pandas \
    python3-ipython \
    python3-tqdm \
#& pip3 install --upgrade sphinx sphinxcontrib-bibtex multipletau \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

#RUN pip3 install numpy

RUN ln -sfn /usr/bin/python3 /usr/bin/python
#


RUN git clone https://github.com/espressomd/espresso.git
RUN cd espresso
RUN mkdir -p espresso/es-build
WORKDIR /home/kvint/espresso/es-build
RUN cmake ..
RUN make -j 8
RUN make install 
USER kvint
ENV USERNAME kvint
CMD /bin/bash -c "source $HOME/.bashrc"


#COPY mcmd_polyelctrolyte .
#RUN cd /home/kvint/socket_server/

#RUN pip3 install tqdm
#RUN pip3 install ipython



