FROM condaforge/mambaforge:latest as cea-build

# create the conda environment and install cea
COPY environment.yml /tmp/environment.yml
RUN mamba env create -f /tmp/environment.yml -n cea && mamba clean -afy

# conda-pack the environment
RUN mamba install -c conda-forge conda-pack
RUN conda-pack -n cea -o /tmp/env.tar \
&& mkdir /venv \
&& cd /venv \
&& tar xf /tmp/env.tar \
&& rm /tmp/env.tar
RUN /venv/bin/conda-unpack

# install cea after dependencies to avoid running conda too many times when rebuilding
COPY . /cea
RUN /bin/bash -c "source /venv/bin/activate && pip install /cea"

# Build Daysim in image to prevent errors in OS lib dependencies
FROM ubuntu:focal AS daysim-build

RUN apt update && DEBIAN_FRONTEND="noninteractive" apt install -y \
git \
cmake \
build-essential \
libgl1-mesa-dev \
libglu1-mesa-dev

RUN git clone https://github.com/MITSustainableDesignLab/Daysim.git /Daysim 

# only build required binaries
RUN mkdir build \
&& cd build \
&& cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_HEADLESS=ON -DOpenGL_GL_PREFERENCE=GLVND /Daysim \
&& make ds_illum \
&& make epw2wea \
&& make gen_dc \
&& make oconv \
&& make radfiles2daysim \
&& mv ./bin /Daysim_build

# uncommenting line in CMakeLists to build rtrace_dc
RUN sed -i 's/#add_definitions(-DDAYSIM)/add_definitions(-DDAYSIM)/' /Daysim/src/rt/CMakeLists.txt \
&& cd build \
&& cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_HEADLESS=ON -DOpenGL_GL_PREFERENCE=GLVND /Daysim \
&& make rtrace \
&& mv ./bin/rtrace /Daysim_build/rtrace_dc


FROM ubuntu:latest AS cea-runtime

# For pythonOCC to work (used by py4design)
RUN apt-get update && apt-get install -y libgl1

COPY --from=cea-build /venv /venv
COPY --from=daysim-build /Daysim_build /venv/Daysim

# bugfix for matplotlib, see here: https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
RUN mkdir -p ~/.config/matplotlib && echo "backend: Agg" > ~/.config/matplotlib/matplotlibrc

# add a folder for projects
RUN mkdir /projects
RUN /bin/bash -c "source /venv/bin/activate && cea-config write --general:project /projects"

# When image is run, run the code with the environment
# activated:
ENV PATH "/venv/bin:/venv/cea/bin:/venv/Daysim:$PATH"
SHELL ["/bin/bash", "-c"]
CMD cea dashboard
