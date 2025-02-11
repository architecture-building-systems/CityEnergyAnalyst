FROM ghcr.io/reyery/daysim:release AS daysim

FROM mambaorg/micromamba:1.5.10 AS cea

USER root

# create directory for projects and set MAMBA_USER as owner of the project directory
RUN mkdir -p /project
RUN chown $MAMBA_USER /project

USER $MAMBA_USER
# create the conda environment and install cea
COPY --chown=$MAMBA_USER:$MAMBA_USER conda-lock.yml /tmp/conda-lock.yml
RUN micromamba config set extract_threads 1 \
    && micromamba install --name base --yes --file /tmp/conda-lock.yml \
    && micromamba clean --all --yes

# bugfix for matplotlib, see here: https://stackoverflow.com/questions/37604289/tkinter-tclerror-no-display-name-and-no-display-environment-variable
RUN mkdir -p ~/.config/matplotlib && echo "backend: Agg" > ~/.config/matplotlib/matplotlibrc

# active environment to install CEA
ARG MAMBA_DOCKERFILE_ACTIVATE=1

# install cea after dependencies to avoid running conda too many times when rebuilding
COPY --chown=$MAMBA_USER:$MAMBA_USER . /tmp/cea
RUN pip install /tmp/cea

# Copy Daysim from build stage
COPY --from=daysim / /Daysim

# write config files
RUN cea-config write --general:project /project/reference-case-open \
    && cea-config write --general:scenario-name baseline \
    && cea-config write --radiation:daysim-bin-directory /Daysim \
    && cea-config write --server:host 0.0.0.0  # required for flask to receive requests from the docker host

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh"]
CMD cea dashboard
