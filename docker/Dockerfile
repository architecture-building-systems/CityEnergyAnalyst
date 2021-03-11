FROM continuumio/miniconda3:4.9.2 as base

COPY ./environment.yml /tmp/environment.yml

# replace conda with C++ reimplementation mamba for faster builds
RUN conda install mamba -n base -c conda-forge

# create the conda environment and install cea...
RUN mamba env create -f /tmp/environment.yml -n cea \
    && conda clean -afy 
ENV PATH /opt/conda/envs/cea/bin:$PATH

# bugfix for matplotlib, see here: https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
RUN mkdir -p /root/.config/matplotlib \
    && echo "backend: Agg" > /root/.config/matplotlib/matplotlibrc

# The dev-stage image; keeps conda installed so
# can use conda to add new packages 
FROM base AS cea-dev

# Remove Python Bytecode files & Static Libraries to save 400MB in space
RUN find /opt/conda/ -follow -type f -name '*.a' -delete \
    && find /opt/conda/ -follow -type f -name '*.pyc' -delete

# When image is run, activate the environment
ENV PATH "/Daysim/bin:$PATH"
SHELL ["/bin/bash", "-c"]
ENTRYPOINT conda activate cea

# The build-stage image; package conda env
# so can use in an image without conda installed
FROM base as cea-build

# conda-pack the environment (with cea pre-installed)
RUN conda install -c conda-forge conda-pack
RUN conda-pack -n cea -o /tmp/env.tar \
    && mkdir /venv \
    && cd /venv \
    && tar xf /tmp/env.tar \
    && rm /tmp/env.tar
RUN /venv/bin/conda-unpack

# The runtime-stage image; we can use Debian as the
# base image since the Conda env also includes Python
# for us.
FROM debian:buster AS cea-runtime

COPY --from=base /root/.config/matplotlib /root/.config/matplotlib
COPY --from=cea-build /venv /venv
COPY ./Daysim /Daysim
COPY ./cea.config /root/cea.config

# Add venv & Daysim to Path
ENV PATH "/venv/cea/bin:/Daysim/bin:$PATH"

# add a folder for projects
RUN mkdir /projects

# Use bash in Dockerfile RUN commands and make sure bashrc is sourced when
# executing commands with /bin/bash -c
ENV BASH_ENV /root/.bashrc
SHELL ["/bin/bash", "-c"]

# Install latest CEA from Github
RUN apt-get update \
    && apt-get install -y git \
    && source /venv/bin/activate \
    && pip install --no-deps git+https://github.com/architecture-building-systems/CityEnergyAnalyst@master#egg=cityenergyanalyst

# When image is run, run the code with the environment
# activated:
ENTRYPOINT source /venv/bin/activate \
    && cea dashboard