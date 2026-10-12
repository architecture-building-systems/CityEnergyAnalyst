# ---- build: materialise the locked environment ----
# trixie (glibc 2.41) is required: pixi.lock is solved against glibc 2.39
FROM ghcr.io/prefix-dev/pixi:0.72.0-trixie-slim AS build
WORKDIR /app
COPY pyproject.toml pixi.lock ./
# --locked fails the build if pixi.lock is out of sync with pyproject.toml
RUN pixi install --locked

# ---- install CEA itself (not part of the lock) without touching its dependencies ----
COPY . /src
RUN pixi run uv build --wheel /src --out-dir /wheels \
 && pixi run uv pip install --no-deps /wheels/cityenergyanalyst-*.whl \
 && pixi run python -c "import cea; print(cea.__version__)"

# activation script (sets PATH, CONDA_PREFIX and GDAL_DATA/PROJ_* via activate.d) and entrypoint
RUN pixi shell-hook -s bash > /app/activate.sh \
 && printf '#!/bin/bash\nsource /app/activate.sh\nexec "$@"\n' > /app/entrypoint.sh

# ---- runtime ----
FROM debian:trixie-slim AS cea
LABEL org.opencontainers.image.source=https://github.com/architecture-building-systems/CityEnergyAnalyst

# Default 57439 is the uid/gid of the previous mambaorg/micromamba image's user, so ownership of
# bind-mounted project folders is unchanged. Override at build time, e.g.
#   docker build --build-arg CEA_UID=1000 --build-arg CEA_GID=1000 .
ARG CEA_UID=57439
ARG CEA_GID=57439
RUN groupadd --gid ${CEA_GID} cea \
 && useradd --uid ${CEA_UID} --gid ${CEA_GID} --create-home --shell /bin/bash cea \
 && mkdir -p /project/reference-case-open \
 && chown -R cea:cea /project

# the prefix path must match the build stage exactly - conda prefixes are not relocatable
COPY --from=build --chown=cea:cea /app/.pixi/envs/default /app/.pixi/envs/default
COPY --from=build --chmod=0755 /app/activate.sh /app/entrypoint.sh /app/

# PATH fallback for runs that skip the entrypoint (singularity shell/exec, docker exec)
# MPLBACKEND bugfix for matplotlib, see https://stackoverflow.com/questions/37604289
ENV PATH=/app/.pixi/envs/default/bin:$PATH \
    MPLBACKEND=Agg

USER cea
WORKDIR /home/cea

# write config files
RUN cea-config write --general:project /project/reference-case-open \
 && cea-config write --general:scenario-name baseline \
 && cea-config write --server:host 0.0.0.0

# Expose dashboard port
EXPOSE 5050

# Direct entrypoint - no tini needed (server has SIGCHLD handler for zombie reaping)
ENTRYPOINT ["/app/entrypoint.sh"]
# exec form so signals reach uvicorn directly
CMD ["cea", "dashboard"]
