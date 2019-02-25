FROM continuumio/miniconda
COPY ./environment.yml /tmp/environment.yml
RUN apt-get update -y && apt-get -y install gcc git libgl1-mesa-glx

RUN conda env create -q -f /tmp/environment.yml -n cea
RUN /bin/bash -c "source activate cea && \
    pip install git+https://github.com/architecture-building-systems/CityEnergyAnalyst.git@1005-fix-installation-guide-for-ubuntu && \
    cea extract-reference-case --destination ~/ && \
    cea-config demand --scenario ~/reference-case-open/baseline"

# bugfix for matplotlib, see here: https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
RUN mkdir -p ~/.config/matplotlib && echo "backend: Agg" > ~/.config/matplotlib/matplotlibrc

# use the environment - no need to source because it's the only environment anyway...
ENV PATH /opt/conda/envs/cea/bin:$PATH
CMD ipython