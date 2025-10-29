FROM ghcr.io/prefix-dev/pixi:bookworm-slim AS build

# build cea-external-tools wheel
COPY external /tmp/external
WORKDIR /tmp/external

RUN pixi run docker-build-wheel

FROM mambaorg/micromamba:bookworm-slim AS cea
LABEL org.opencontainers.image.source=https://github.com/architecture-building-systems/CityEnergyAnalyst

USER root
# Tini is optional now - we have SIGCHLD handler in server for zombie reaping
# Uncomment the next line if you encounter issues with orphaned processes or signals
# RUN apt-get update && apt-get install -y tini && rm -rf /var/lib/apt/lists/*

# create directory for projects and set MAMBA_USER as owner
RUN mkdir -p /project && chown $MAMBA_USER /project

USER $MAMBA_USER
# create conda environment and configure matplotlib
# bugfix for matplotlib, see here: https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
COPY --chown=$MAMBA_USER:$MAMBA_USER conda-lock.yml /tmp/conda-lock.yml
RUN micromamba config set extract_threads 1 \
    && micromamba install --name base --yes --file /tmp/conda-lock.yml \
    && micromamba clean --all --yes \
    && mkdir -p ~/.config/matplotlib \
    && echo "backend: Agg" > ~/.config/matplotlib/matplotlibrc \
    && rm -f /tmp/conda-lock.yml

# active environment to install CEA
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# install cea-external-tools
COPY --from=build --chown=$MAMBA_USER:$MAMBA_USER /tmp/external/dist /tmp/external_dist
RUN pip install /tmp/external_dist/cea_external_tools-*.whl && rm -rf /tmp/external_dist

# install cea and clean up
COPY --chown=$MAMBA_USER:$MAMBA_USER . /tmp/cea
RUN pip install /tmp/cea && rm -rf /tmp/cea

# write config files
RUN cea-config write --general:project /project/reference-case-open \
    && cea-config write --general:scenario-name baseline \
    && cea-config write --server:host 0.0.0.0 \
    # create dummy project folder
    && mkdir -p /project/reference-case-open

# Expose dashboard port
EXPOSE 5050

# Direct entrypoint - no tini needed (server has SIGCHLD handler for zombie reaping)
# If you need tini, uncomment the line below and comment out the next ENTRYPOINT line
# ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/_entrypoint.sh"]
ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]
CMD cea dashboard
