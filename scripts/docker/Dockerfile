# Dockerfile for espresso 4.1.3
FROM ubuntu:focal as build0
LABEL Oleg Rud <oleg.rud@natur.cuni.cz>
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y python3-pip

RUN useradd -ms /bin/bash kvint
WORKDIR /home/kvint
ENV USERNAME kvint

RUN apt-get install -y -f\
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
    cython3 \
    lcov \
    vim \
    pep8 pylint3 \
    doxygen \
    libhdf5-serial-dev \
    libpython3-dev \
    libhdf5-openmpi-dev \
    libhdf5-dev \
    ccache \
    git \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt /home/kvint
RUN pip3 install -r requirements.txt
RUN ln -sfn /usr/bin/python3 /usr/bin/python

FROM build0 as build_espresso


COPY .bashrc /home/kvint
CMD /bin/bash -c "source $HOME/.bashrc"

COPY env.rc /home/kvint



COPY espresso/ /home/kvint/espresso/
RUN cd espresso
RUN mkdir -p es-build
WORKDIR /home/kvint/espresso/espresso/es-build
RUN cmake ..
RUN make -j 4
RUN make install

#FROM build_espresso as build_MCMD
WORKDIR /home/kvint
USER kvint
ENV USERNAME kvint

