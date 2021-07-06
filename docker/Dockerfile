FROM continuumio/miniconda3 as cea-build
COPY ./environment.yml /tmp/environment.yml

# create the conda environment and install cea
RUN conda env create -q -f /tmp/environment.yml -n cea
ENV PATH /opt/conda/envs/cea/bin:$PATH
RUN /bin/bash -c "source activate cea && pip install --no-deps git+https://github.com/architecture-building-systems/CityEnergyAnalyst@master#egg=cityenergyanalyst"

# conda-pack the environment (with cea pre-installed)
RUN conda install -c conda-forge conda-pack
RUN conda-pack -n cea -o /tmp/env.tar \
&& mkdir /venv \
&& cd /venv \
&& tar xf /tmp/env.tar \
&& rm /tmp/env.tar
RUN /venv/bin/conda-unpack

# Build Daysim to prevent errors in OS lib dependencies
FROM debian:stable-slim AS daysim-build

RUN apt update && apt install git cmake build-essential libgl1-mesa-dev freeglut3-dev -y
RUN git clone https://github.com/MITSustainableDesignLab/Daysim.git
RUN mkdir build && cd build && cmake -DBUILD_HEADLESS=on -DCMAKE_INSTALL_PREFIX=$HOME/Daysim ../Daysim && make && make install

# next: build the Daysim specific stuff
COPY ./CMakeLists.txt /Daysim/CMakeLists.txt
RUN cd build && cmake -DBUILD_HEADLESS=on -DCMAKE_INSTALL_PREFIX=$HOME/Daysim ../Daysim && make && mv ./bin/rtrace ./bin/rtrace_dc && cp ./bin/* /root/Daysim/bin

# The runtime-stage image; we can use Debian as the
# base image since the Conda env also includes Python
# for us.
FROM debian:stable-slim AS cea-runtime

RUN apt-get update && apt-get install -y libgl1

COPY --from=cea-build /venv /venv
COPY --from=daysim-build /root/Daysim/bin /venv/Daysim
COPY ./cea.config /root/cea.config


# bugfix for matplotlib, see here: https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
RUN mkdir -p /root/.config/matplotlib && echo "backend: Agg" > /root/.config/matplotlib/matplotlibrc

# add a folder for projects
RUN mkdir /projects

# When image is run, run the code with the environment
# activated:
ENV PATH "/venv/cea/bin:/venv/Daysim:$PATH"
SHELL ["/bin/bash", "-c"]
ENTRYPOINT source /venv/bin/activate && cea dashboard