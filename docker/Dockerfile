FROM continuumio/miniconda
COPY ./environment.yml /tmp/environment.yml
RUN apt-get update -y && apt-get -y install gcc git

RUN conda env create -q -f /tmp/environment.yml -n cea
RUN /bin/bash -c "source activate cea && \
    pip install git+https://github.com/architecture-building-systems/CityEnergyAnalyst.git@1005-fix-installation-guide-for-ubuntu"

# use the environment - no need to source because it's the only environment anyway...
ENV PATH /opt/conda/envs/cea/bin:$PATH
CMD ipython