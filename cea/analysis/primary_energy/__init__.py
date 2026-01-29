"""
Primary Energy Calculation Module

This module calculates primary energy consumption from end-use demand based on
supply system efficiency and network losses.

Separated from demand module to maintain clean separation:
- demand module: building physics (end-use demand only)
- primary_energy module: supply system conversion (efficiency, components)
- costs/LCA modules: economic and environmental impacts
"""
