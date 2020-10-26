FROM continuumio/miniconda3 as cea-build
COPY ./environment.yml /tmp/environment.yml

# create the conda environment and install cea...
RUN conda env create -q -f /tmp/environment.yml -n cea
RUN /bin/bash -c "source activate cea && \
    pip install git+https://github.com/architecture-building-systems/CityEnergyAnalyst.git && \
    cea extract-reference-case --destination ~/ && \
    cea-config demand --scenario ~/reference-case-open/baseline && \
    cea-config radiation --daysim-bin-directory /root/Daysim/bin"

# bugfix for matplotlib, see here: https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
RUN mkdir -p ~/.config/matplotlib && echo "backend: Agg" > ~/.config/matplotlib/matplotlibrc

# The runtime-stage image; we can use Debian as the
# base image since the Conda env also includes Python
# for us.
FROM debian:buster AS cea-runtime
# use the environment - no need to source because it's the only environment anyway...
ENV PATH "/opt/conda/envs/cea/bin:/root/Daysim/bin:$PATH"
CMD ipython