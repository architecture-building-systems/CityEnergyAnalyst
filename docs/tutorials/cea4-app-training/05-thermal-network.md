# Thermal Network Design

Thermal network design features enable the planning and analysis of district heating and cooling systems. The process is divided into two parts: layout generation and thermal hydraulic analysis.

---

## Thermal Network Part 1: Layout

### Overview
Automatically generates thermal network piping layouts using minimum spanning tree algorithms that follow street geometries. This feature creates the spatial configuration of district heating (DH) or district cooling (DC) networks connecting buildings to central plants.

### When to Use
- Designing new district heating or cooling networks
- Comparing different network configurations
- Estimating network length and coverage
- Planning infrastructure for district energy systems

### How It Works
The algorithm:
1. Identifies buildings to connect based on demand
2. Finds optimal pipe routes following streets
3. Minimizes total pipe length
4. Creates network nodes and edges
5. Outputs GIS shapefiles for the network

### Prerequisites
- **Energy Demand Part 2** - Must be completed (to know building loads)
- **Streets Helper** - Street network must exist
- Zone geometry

### Required Input Files
- **Street network**: Shapefile of streets (`streets.shp`)
- **Total demand**: Building energy demands (`Total_demand.csv`)
- **Zone geometry**: Building footprints

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Network type** | DH (heating) or DC (cooling) | DH or DC |
| **Allow looped networks** | Create redundant paths | No (tree) |
| **Consider all buildings** | Or select subset to connect | All with demand |

### How to Use

1. **Complete prerequisites**:
   - ✅ Energy Demand calculation
   - ✅ Streets Helper (street network)

2. **Run layout generation**:
   - Navigate to **Thermal Network Design**
   - Select **Thermal Network Part 1: Layout**
   - Choose network type (DH or DC)
   - Configure options
   - Click **Run**

3. **Processing time**: Usually < 1 minute for typical districts

### Output Files

**Network edges**: `{scenario}/inputs/networks/DH/edges.shp` (or DC)
- Pipe segments along streets
- Length of each segment
- Start/end coordinates

**Network nodes**: `{scenario}/inputs/networks/DH/nodes.shp` (or DC)
- Building connection points
- Pipe junctions
- Node coordinates and building references

### Understanding Layout Results

Key metrics to review:
- **Total pipe length** (m or km)
- **Number of connected buildings**
- **Network density** (pipe length per connected building)
- **Building connection points**

Typical network characteristics:
- Tree networks: Pipe length = 0.8-1.5× linear distance between buildings
- Looped networks: Pipe length = 1.2-2.0× tree network length
- Urban density: 20-80 m pipe per building

### Visualising the Network
1. Use CEA-4 App 3D viewer to see network overlay
2. Export to Rhino/Grasshopper for detailed visualisation
3. Open shapefiles in QGIS or ArcGIS

### Tips
- **Accurate streets matter**: Network follows streets, so street quality affects results
- **Check connectivity**: Verify all desired buildings are connected
- **Consider future expansion**: Leave capacity for additional connections
- **Manual editing**: You can manually edit the generated shapefiles if needed

### Troubleshooting

**Issue**: Not all buildings connected
- **Solution**: Check street network covers all building areas
- **Solution**: Some buildings may be too far from streets

**Issue**: Network layout doesn't follow streets well
- **Solution**: Improve street network quality with Streets Helper
- **Solution**: Manually add missing street segments

**Issue**: Missing output shapefiles
- **Solution**: Check for error messages in the log
- **Solution**: Verify Total_demand.csv exists and has valid data

---

## Thermal Network Part 2: Flow & Sizing

### Overview
Performs detailed thermal hydraulic simulation of the network created in Part 1. This feature calculates mass flow rates, pipe sizes, temperatures, pressure drops, and pump requirements for district heating or cooling systems.

### When to Use
- After generating network layout (Part 1)
- Sizing pipes for district energy systems
- Calculating pumping energy and pressure requirements
- Assessing thermal losses in distribution
- Verifying network hydraulic feasibility

### What It Calculates

**Hydraulic Analysis**:
- Mass flow rates in each pipe segment (kg/s)
- Required pipe diameters (mm)
- Pressure drops along network (Pa)
- Pump head and power requirements (kW)

**Thermal Analysis**:
- Supply and return temperatures at each node (°C)
- Heat losses from pipes (kW, kWh/year)
- Temperature drops along network
- Building substation heat exchangers

**Network Performance**:
- Total annual heat delivered (MWh/year)
- Total annual heat losses (MWh/year, %)
- Pumping energy consumption (MWh/year)
- Peak loads and flows (kW, kg/s)

### Prerequisites
- **Thermal Network Part 1** - Network layout must exist
- **Energy Demand Part 2** - Building hourly demands needed
- Weather file for ground temperature

### Required Input Files
- **Network layout**: Nodes and edges shapefiles (from Part 1)
- **Building demands**: Individual building demand files (`BXXX.csv`)
- **Component databases**: Pipe and system properties
- **Weather file**: For ground temperature calculation

### Key Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **Network type** | DH or DC | DH or DC |
| **Supply temperature** | Network supply temp | 80°C (DH) / 6°C (DC) |
| **Return temperature** | Network return temp | 50°C (DH) / 12°C (DC) |
| **Pipe insulation** | Insulation standard | Standard / High performance |
| **Ground temperature** | For heat loss calculation | From weather file |
| **Multiprocessing** | Parallel processing | Enabled |

### How to Use

1. **Complete network layout** (Part 1)

2. **Configure parameters**:
   - Navigate to **Thermal Network Design**
   - Select **Thermal Network Part 2: Flow & Sizing**
   - Select network type (must match Part 1)
   - Set supply/return temperatures:
     - **District heating**: 70-90°C supply, 40-50°C return
     - **District cooling**: 5-8°C supply, 12-15°C return
   - Choose pipe insulation standard
   - Enable multiprocessing

3. **Run analysis**:
   - Click **Run**
   - Processing time: 10-60 minutes depending on network size and complexity

### Output Files

**Pipe sizing results**: `{scenario}/outputs/data/thermal-network/DH/plant_building_names.csv`
- Connected buildings and their loads

**Edge results**: `{scenario}/outputs/data/thermal-network/DH/edges.csv`
- Pipe diameters (mm)
- Mass flow rates (kg/s)
- Pressure drops (Pa)
- Heat losses (W/m)
- Temperature drops (K)

**Node results**: `{scenario}/outputs/data/thermal-network/DH/nodes.csv`
- Node pressures (Pa)
- Temperatures (°C)
- Building heat exchanger sizing

**Network summary**: `{scenario}/outputs/data/thermal-network/DH/network_summary.csv`
- Total pipe length and volume
- Total heat losses (annual)
- Pumping energy requirements
- Cost estimates

### Understanding Results

#### Key Performance Indicators

**Heat Losses**:
- Well-designed DH: 10-20% annual losses
- Older DH networks: 20-35% losses
- Low-temperature DH: 5-15% losses

**Pumping Energy**:
- Typical: 1-3% of delivered heat energy
- Long networks or high ΔT: Up to 5%
- Affects system efficiency significantly

**Pipe Sizes**:
- Small buildings: DN25-DN50 (25-50 mm diameter)
- Medium buildings: DN50-DN100
- Main distribution: DN100-DN300
- Large district mains: DN300-DN600

#### Validation Checks

1. **Pressure feasibility**: All pressures should be positive (no cavitation)
2. **Temperature feasibility**: Return temp > supply temp at all points should never occur
3. **Reasonable losses**: Total losses typically 10-20% for new networks
4. **Flow velocities**: Typically 0.5-3 m/s (check derived from mass flow and diameter)

### Advanced Options

#### Network Temperature Regimes

**High-Temperature DH** (80-90°C):
- Traditional systems
- Higher heat losses
- Suitable for old buildings

**Low-Temperature DH** (50-70°C):
- Modern systems
- Lower heat losses
- Requires better building insulation
- Enables heat recovery sources

**Very Low-Temperature DH** (30-50°C):
- Ultra-modern systems
- Minimal heat losses
- Requires heat pumps at buildings
- Can also provide cooling

#### Pipe Insulation Standards

- **Standard**: Typical for urban DH (λ ≈ 0.023 W/mK)
- **High performance**: Better insulation for lower losses (λ ≈ 0.018 W/mK)
- **Twin pipes**: Pre-insulated pipe pairs (supply + return)

### Tips

1. **Temperature optimisation**: Lower supply temperatures reduce heat losses
2. **Pressure management**: Long networks may need intermediate pumping stations
3. **Insulation pays off**: Better insulation reduces operating costs
4. **Validate with reality**: Compare results with existing network data if available
5. **Consider future growth**: Size pipes with expansion margin (10-20%)

### Troubleshooting

**Issue**: Simulation fails or crashes
- **Solution**: Check network layout for disconnected segments
- **Solution**: Verify all buildings in network have valid demand data
- **Solution**: Try disabling multiprocessing for debugging

**Issue**: Unrealistic pressure drops (very high or negative)
- **Solution**: Check network connectivity and flow directions
- **Solution**: Verify pipe properties in database
- **Solution**: Review supply/return temperature settings

**Issue**: Very high heat losses (>30%)
- **Solution**: Check pipe insulation settings
- **Solution**: Verify ground temperature is reasonable
- **Solution**: Consider lower supply temperatures

**Issue**: No pump requirements calculated
- **Solution**: Check that network has defined plant location
- **Solution**: Verify pressure boundary conditions

---

## Complete Thermal Network Workflow

### Standard District Heating Workflow

1. **Data Preparation**:
   - Run [Energy Demand Part 2](04-demand-forecasting.md) for all buildings
   - Run [Streets Helper](08-data-management.md#streets-helper) to get street network

2. **Network Layout**:
   - Run Thermal Network Part 1: Layout
   - Select DH (district heating)
   - Review generated layout in 3D viewer or GIS

3. **Network Sizing**:
   - Run Thermal Network Part 2: Flow & Sizing
   - Set appropriate supply/return temperatures (e.g., 80°C / 50°C)
   - Review results: pipe sizes, heat losses, pumping energy

4. **Optimisation** (Optional):
   - Run [District-Scale Optimisation](07-supply-optimisation.md) to find optimal plant and system configuration
   - Iterate on network configuration if needed

5. **Analysis**:
   - Run [Emissions](06-life-cycle-analysis.md#emissions) to assess carbon footprint
   - Run [Energy Supply System Costs](06-life-cycle-analysis.md#energy-supply-system-costs) for economic analysis
   - Use [Visualisation tools](10-visualisation.md) to present results

### District Cooling Workflow
Same as heating, but:
- Choose DC (district cooling) in Part 1
- Set cooling temperatures in Part 2 (e.g., 6°C / 12°C)
- Focus on cooling demands from demand calculation

---

## Network Design Best Practices

### Layout Design
- **Follow streets**: Easier permitting and construction
- **Minimize length**: Reduce capital cost and heat losses
- **Strategic branching**: Balance tree simplicity with reliability
- **Future-proof**: Consider expansion areas

### Operating Strategy
- **Temperature optimisation**: Lower temps = lower losses
- **Load management**: Balance peak loads across network
- **Seasonal adjustment**: Vary temperatures with season
- **Smart controls**: Use real-time monitoring and control

### Pipe Sizing Principles
- **Design for peak load**: Ensure adequate capacity for coldest day
- **Consider velocity limits**: 0.5-3 m/s typical range
- **Pressure constraints**: Maximum ~16 bar in most systems
- **Standard sizes**: Use common pipe diameters for cost efficiency

---

## Related Features
- **[Energy Demand Forecasting](04-demand-forecasting.md)** - Provides building loads (prerequisite)
- **[Data Management](08-data-management.md#streets-helper)** - Streets Helper for network path
- **[Supply System Optimisation](07-supply-optimisation.md)** - Network and plant optimisation
- **[Life Cycle Analysis](06-life-cycle-analysis.md)** - Emissions and costs for networks

---

## Further Reading
- District heating design handbook
- EN 13941: Design and installation of pre-insulated bonded pipe systems
- IEA DHC Annex documents
- 4th Generation District Heating (4GDH) concepts

---

[← Back: Energy Demand](04-demand-forecasting.md) | [Back to Index](index.md) | [Next: Life Cycle Analysis →](06-life-cycle-analysis.md)
