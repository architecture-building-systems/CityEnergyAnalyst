# Module input and output files

## Benchmark graphs

### Input files

* `db/Benchmarks/benchmark_targets.xls`
* `db/Benchmarks/benchmark_today.xls`
* `scenario/inputs/building-properties/building_occupancy.shp`
* `scenario/outputs/data/demand/Total_demand.csv`
* `scenario/outputs/data/emissions/Total_LCA_embodied.csv`
* `scenario/outputs/data/emissions/Total_LCA_operation.csv`
* `scenario/outputs/data/emissions/Total_LCA_mobility.csv`

### Output files

* (user defined pdf file)

## Data helper

### Input files

* `scenario/inputs/building-properties/building_occupancy.shp`
* `scenario/inputs/building-properties/age.shp`
* `db/Archetypes/Archetypes_properties.xlsx`

## Output files

* `scenario/inputs/building-properties/indoor_comfort.shp`
* `scenario/inputs/building-properties/technical_systems.shp`
* `scenario/inputs/building-properties/architecture.shp`
* `scenario/inputs/building-properties/thermal_properties.shp`
* `scenario/inputs/building-properties/internal_loads.shp`

## Demand graphs

### Input files

* `scenario/outputs/data/demand/Total_demand.csv`
* `scenario/outputs/data/demand/{building_name}.csv`
  * (one for each building in the scenario)

### Output files

* `scenario/outputs/plots/timeseries/{building_name}.pdf`
  * (one for each building in the scenario)
  
## Demand

### Input files

* `scenario/outputs/data/solar-radiation/radiation.csv`
* `scenario/outputs/data/solar-radiation/properties_surfaces.csv`
* `scenario/inputs/building-properties/overrides.csv`
* `scenario/inputs/building-properties/thermal_properties.shp`
* `scenario/inputs/building-geometry/zone.shp`
* `scenario/inputs/building-properties/building_occupancy.shp`
* `scenario/inputs/building-properties/age.shp`
* `scenario/inputs/building-properties/internal_loads.shp`
* `scenario/inputs/building-properties/indoor_comfort.shp`
* `scenario/inputs/building-properties/architecture.shp`
* `scenario/inputs/building-properties/technical_systems.shp`
* `db/Systems/emission_systems.csv`
* `db/Archetypes/Archetypes_schedules.xlsx`

### Output files

* `TEMPDIR/{building_name}T.csv`
    * (one per building in the scenario)
* `scenario/outputs/data/demand/{building_name}.csv`
  * (one per building in the scenario)
* `scenario/outputs/data/demand/Total_demand.csv`

## Emissions

### Input files

* `scenario/outputs/data/demand/Total_demand.csv`
* `scenario/inputs/building-properties/building_supply.shp`
* `db/Systems/supply_systems.csv`

### Output files

* `scenario/outputs/data/emissions/Total_LCA_operation.csv`
* `scenario/outputs/data/emissions/Edataf_LCA_operation.csv`
* `scenario/outputs/data/emissions/Eprof_LCA_operation.csv`
* `scenario/outputs/data/emissions/Eauxf_LCA_operation.csv`
* `scenario/outputs/data/emissions/Ealf_LCA_operation.csv`
* `scenario/outputs/data/emissions/Ef_LCA_operation.csv`
* `scenario/outputs/data/emissions/Qcref_LCA_operation.csv`
* `scenario/outputs/data/emissions/Qcdataf_LCA_operation.csv`
* `scenario/outputs/data/emissions/Qcsf_LCA_operation.csv`
* `scenario/outputs/data/emissions/QCf_LCA_operation.csv`
* `scenario/outputs/data/emissions/Qwwf_LCA_operation.csv`
* `scenario/outputs/data/emissions/Qhsf_LCA_operation.csv`

## Embodied energy

### Input files

* `scenario/inputs/building-properties/building_occupancy.shp`
* `scenario/inputs/building-properties/architecture.shp`
* `scenario/inputs/building-properties/age.shp`
* `scenario/inputs/building-geometry/zone.shp`
* `db/Archetypes/Archetypes_properties.xlsx`

### Output files

* `scenario/outputs/data/emissions/Total_LCA_embodied.csv`

## Mobility

### Input files

* `scenario/inputs/building-properties/building_occupancy.shp`
* `db/Benchmarks/mobility.xls`
* `scenario/outputs/data/demand/Total_demand.csv`

### Output files

* `scenario/outputs/data/emissions/Total_LCA_mobility.csv`

### Input files

* `scenario/inputs/building-geometry/zone.shp`
* csv file to analyze

### Output files

* `scenario/outputs/plots/heatmaps/{field}/*`
  * an ArcGIS heatmap for each field in the csv file to analyze 
