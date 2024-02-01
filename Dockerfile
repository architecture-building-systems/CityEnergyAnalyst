# Build Daysim in image to prevent errors in OS lib dependencies
FROM debian:bookworm-slim AS daysim-build

RUN apt update && DEBIAN_FRONTEND="noninteractive" apt install -y \
git \
cmake \
build-essential \
libgl1-mesa-dev \
libglu1-mesa-dev

RUN git clone -b fix-ds-illum-variable --single-branch https://github.com/reyery/Daysim.git /Daysim

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


FROM mambaorg/micromamba as cea-build

COPY --from=daysim-build /Daysim_build /Daysim

USER root
# install git required to install from git repository and clean apt cache
RUN apt update  \
    && DEBIAN_FRONTEND="noninteractive" apt install -y git \
    && rm -rf /var/lib/apt/lists/*

# create directory for projects and set MAMBA_USER as owner of the project directory
RUN mkdir -p /project
RUN chown $MAMBA_USER /project

USER $MAMBA_USER
# create the conda environment and install cea
COPY --chown=$MAMBA_USER:$MAMBA_USER conda-lock.yml /tmp/conda-lock.yml
RUN micromamba install --name base --yes --file /tmp/conda-lock.yml \
    && micromamba clean --all --yes

# bugfix for matplotlib, see here: https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
RUN mkdir -p ~/.config/matplotlib && echo "backend: Agg" > ~/.config/matplotlib/matplotlibrc

# active environment to install CEA
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# install cea after dependencies to avoid running conda too many times when rebuilding
COPY --chown=$MAMBA_USER:$MAMBA_USER . /tmp/cea
RUN pip install /tmp/cea
RUN cea-config write --general:project /project
RUN cea-config write --radiation:daysim-bin-directory /Daysim
# required for flask to receive reqests from the docker host
RUN cea-config write --server:host 0.0.0.0

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]
CMD cea dashboard
