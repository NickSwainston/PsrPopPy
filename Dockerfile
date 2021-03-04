FROM continuumio/miniconda

# Install dependancies
RUN apt-get update && \
    apt-get install -y \
        tcsh \
        gfortran \
        python-wxtools \
        libgtk2.0-dev && \
    apt-get clean all && \
    rm -r /var/lib/apt/lists/*
RUN conda install \
        numpy \
        scipy \
        matplotlib \
        wxpython

# Install psrpoppy
WORKDIR /tmp/psrpoppy_build
RUN git clone https://github.com/samb8s/PsrPopPy.git && \
    cd PsrPopPy/psrpoppy/fortran && \
    sed -i '10 a $gf -shared -o libgamma.so -fno-second-underscore gamma.o' make_linux.csh && \
    tcsh make_linux.csh
ENV PYTHONPATH "/tmp/psrpoppy_build/PsrPopPy"
ENV PATH "$PATH:/tmp/psrpoppy_build/PsrPopPy/bin"
ENV PATH "$PATH:/tmp/psrpoppy_build/PsrPopPy/psrpoppy"
