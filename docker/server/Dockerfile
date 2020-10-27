FROM continuumio/miniconda3 as cea-build
COPY ./environment.yml /tmp/environment.yml

# create the conda environment and install cea...
RUN conda env create -q -f /tmp/environment.yml -n cea
ENV PATH /opt/conda/envs/cea/bin:$PATH
RUN /bin/bash -c "source activate cea && pip install --no-deps git+https://github.com/architecture-building-systems/CityEnergyAnalyst/tree/2834-docker-container-for-remap"

# conda-pack the environment (with cea pre-installed)
RUN conda install -c conda-forge conda-pack
RUN conda-pack -n cea -o /tmp/env.tar && mkdir /venv && cd /venv && tar xf /tmp/env.tar && rm /tmp/env.tar
RUN /venv/bin/conda-unpack

# The runtime-stage image; we can use Debian as the
# base image since the Conda env also includes Python
# for us.
FROM debian:buster AS cea-runtime

COPY --from=cea-build /venv /venv
COPY ./Daysim /Daysim
COPY ./cea.config ~/cea.config


# bugfix for matplotlib, see here: https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
RUN mkdir -p ~/.config/matplotlib && echo "backend: Agg" > ~/.config/matplotlib/matplotlibrc

# use the environment - no need to source because it's the only environment anyway...
ENV PATH "/venv/cea/bin:/Daysim/bin:$PATH"
CMD ipython