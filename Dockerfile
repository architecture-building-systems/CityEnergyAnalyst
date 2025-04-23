FROM ghcr.io/reyery/daysim:release AS daysim

#FROM ghcr.io/reyery/cea/crax:latest AS crax
# Fetch from prebuild
FROM debian:12-slim AS crax-prebuild
RUN apt-get update && apt-get install -y curl unzip
# Download the zip file directly with curl
RUN curl -L -o /tmp/Linux.zip https://github.com/wanglittlerain/CEA_radiationCRAX/raw/f427fd4ffadb12a34ed59b8838b2fb38c9da9551/bin/Linux.zip
# Extract only the files inside the Linux folder to the root directory
RUN mkdir -p /tmp/extract && unzip /tmp/Linux.zip -d /tmp/extract && \
    mkdir -p /CRAX && cp -r /tmp/extract/Linux/* /CRAX && \
    rm -rf /tmp/extract /tmp/Linux.zip

FROM mambaorg/micromamba:2.0 AS cea
LABEL org.opencontainers.image.source=https://github.com/architecture-building-systems/CityEnergyAnalyst

USER root
# create directory for projects and set MAMBA_USER as owner
RUN mkdir -p /project && chown $MAMBA_USER /project

# Install Arrow libraries and dependencies to support CRAX binaries
RUN apt-get update && apt-get install -y \
    ca-certificates \
    lsb-release \
    curl && \
    curl -sSL https://packages.apache.org/artifactory/arrow/$(lsb_release --id --short | tr 'A-Z' 'a-z')/apache-arrow-apt-source-latest-$(lsb_release --codename --short).deb > apache-arrow-latest.deb && \
    apt-get install ./apache-arrow-latest.deb && \
    rm apache-arrow-latest.deb && apt-get update \
    && apt-get install -y --no-install-recommends \
    libarrow-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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

# install cea and clean up
COPY --chown=$MAMBA_USER:$MAMBA_USER . /tmp/cea
RUN pip install /tmp/cea && rm -rf /tmp/cea

# Copy Daysim from build stage
COPY --from=daysim --chown=$MAMBA_USER:$MAMBA_USER / /opt/conda/lib/python3.8/site-packages/cea/resources/radiation/bin/linux

# Copy USR binary
COPY --from=crax-prebuild --chown=$MAMBA_USER:$MAMBA_USER /CRAX /opt/conda/lib/python3.8/site-packages/cea/resources/radiationCRAX/bin/linux
# Ensure container user is able to execute the binaries
RUN chmod -R +x /opt/conda/lib/python3.8/site-packages/cea/resources/radiationCRAX/bin/linux


# write config files
RUN cea-config write --general:project /project/reference-case-open \
    && cea-config write --general:scenario-name baseline \
    && cea-config write --server:host 0.0.0.0 \
    # create dummy project folder
    && mkdir -p /project/reference-case-open

# Expose dashboard port
EXPOSE 5050

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]
CMD cea dashboard
