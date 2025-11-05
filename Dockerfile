FROM ghcr.io/prefix-dev/pixi:bookworm-slim AS build

# build cea-external-tools wheel
COPY external /tmp/external
WORKDIR /tmp/external

RUN pixi run docker-build-wheel

FROM mambaorg/micromamba:bookworm-slim AS cea
LABEL org.opencontainers.image.source=https://github.com/architecture-building-systems/CityEnergyAnalyst

USER root

# create directory for projects and set MAMBA_USER as owner
RUN mkdir -p /project && chown $MAMBA_USER /project

USER $MAMBA_USER
# create conda environment and configure matplotlib
# bugfix for matplotlib, see here: https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
COPY --chown=$MAMBA_USER:$MAMBA_USER conda-lock.yml /tmp/conda-lock.yml
RUN micromamba config set extract_threads 1 \
    && micromamba install --name base --yes --file /tmp/conda-lock.yml \
    && micromamba install --name base --yes -c conda-forge uv \
    && micromamba clean --all --yes \
    && mkdir -p ~/.config/matplotlib \
    && echo "backend: Agg" > ~/.config/matplotlib/matplotlibrc \
    && rm -f /tmp/conda-lock.yml

# active environment to install CEA
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# Using --system for uv to install packages into the base environment
# install cea-external-tools
COPY --from=build --chown=$MAMBA_USER:$MAMBA_USER /tmp/external/dist /tmp/external_dist
RUN uv pip install --system /tmp/external_dist/cea_external_tools-*.whl && rm -rf /tmp/external_dist

# Copy only pyproject.toml first for better layer caching
COPY --chown=$MAMBA_USER:$MAMBA_USER pyproject.toml /tmp/cea/pyproject.toml
WORKDIR /tmp/cea

# Install dependencies only (cached layer - only rebuilds if pyproject.toml changes)
# Filter out cea-external-tools since it's already installed from the pre-built wheel above
# This ensures we use the exact wheel from the build stage and avoid version resolution conflicts
RUN uv pip install --system -r <(python3 -c "import tomllib; deps=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']; print('\n'.join([d for d in deps if not d.startswith('cea-external-tools')]))")

# Copy full source code and install CEA without dependencies
COPY --chown=$MAMBA_USER:$MAMBA_USER . /tmp/cea
RUN uv pip install --system --no-deps /tmp/cea && rm -rf /tmp/cea

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
