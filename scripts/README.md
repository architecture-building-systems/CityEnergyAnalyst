# Scripts

Utility scripts for running CEA on external systems and repository maintenance.

## Subfolders

### euler/
Scripts for running the CEA sensitivity analysis on the [Euler HPC cluster](https://scicomp.ethz.ch/wiki/Euler) at ETH Zurich. See [euler/README.md](euler/README.md) for detailed usage instructions.

**Note**: Only researchers at ETH Zurich with a nethz account can use the Euler cluster.

### cleanup/
Repository maintenance scripts for cleaning up git history.

## Utility Scripts

### config_type_generator.py
Generates the `cea/config.pyi` type stub from `cea/default.config`. Run manually after changing `config.py` or `default.config`:

```bash
python scripts/config_type_generator.py
```

Also runs automatically via `.github/workflows/update-config-stubs.yml`.

### record_osm_fixtures.py
Refreshes `cea/tests/fixtures/osm_zug/`, the recorded Overpass API responses that
`test_inputs_setup_workflow.py` replays instead of hitting the live API (which has
repeatedly timed out from GitHub-hosted CI runners). Run manually only if the workflow
starts calling `osmnx.features_from_polygon`/`osmnx.graph_from_bbox` differently:

```bash
python scripts/record_osm_fixtures.py
```
