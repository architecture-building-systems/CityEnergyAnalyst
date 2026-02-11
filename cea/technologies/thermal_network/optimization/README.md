# Thermal Network Optimisation

**STATUS: DEPRECATED**

This module contains the legacy thermal network optimisation script using genetic algorithms to optimise network design variables (plant locations, layout, building connections).

## Why Deprecated

This optimisation approach is no longer actively maintained and has been superseded by newer optimisation methods in CEA.

## Usage

While deprecated, this script is still accessible via:

```bash
cea thermal-network-optimization
```

Or in Python:
```python
import cea.api
cea.api.thermal_network_optimization(scenario='/path/to/scenario')
```

## Alternative Approaches

For network optimisation, consider:
- Manual network layout design using `network-layout` script
- Multi-phase network expansion planning using `thermal-network` with multi-phase mode
- External optimisation tools with CEA API integration

## Migration Notes

If you are currently using this script:
1. The cost calculation utilities have been moved to `common/costs.py`
2. The detailed thermal network model is now in `detailed/model.py`
3. Consider migrating to multi-phase expansion planning for staged network deployment

## Maintenance Status

- This code is kept for backwards compatibility only
- Bug fixes: Yes (critical issues only)
- New features: No
- Documentation updates: No

For questions, please open an issue at: https://github.com/architecture-building-systems/CityEnergyAnalyst/issues
