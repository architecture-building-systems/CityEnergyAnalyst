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

# Build Daysim in image to prevent errors in OS lib dependencies
FROM debian:stable-slim AS daysim-build

RUN apt update && apt install git cmake build-essential libgl1-mesa-dev libglu1-mesa-dev -y
RUN git clone https://github.com/MITSustainableDesignLab/Daysim.git
# uncommenting line in CMakeLists to install daysim binaries
RUN sed -i 's/#//' /Daysim/src/daysim/CMakeLists.txt
RUN mkdir build && cd build && cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_HEADLESS=ON -DCMAKE_INSTALL_PREFIX=$HOME/Daysim ../Daysim && make && make install

# uncommenting line CMakeLists to build rtrace_dc
RUN sed -i 's/#add_definitions(-DDAYSIM)/add_definitions(-DDAYSIM)/' /Daysim/src/rt/CMakeLists.txt
RUN cd build && cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_HEADLESS=ON ../Daysim && make rtrace && mv ./bin/rtrace $HOME/Daysim/bin/rtrace_dc

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