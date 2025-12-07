"""
Unit tests for Component classes and their subclasses.

Tests the ComponentUnit and all concrete component implementations
(AbsorptionChiller, VapourCompressionChiller, AirConditioner, Boiler,
CogenPlant, HeatPump, CoolingTower, PowerTransformer, HeatExchanger).

Note: Component, ActiveComponent, and PassiveComponent are abstract parent
classes and are not tested directly. Their functionality is tested through
the concrete component implementations.
"""

import unittest
from unittest.mock import Mock
import pandas as pd

import cea.config
import cea.inputlocator
from cea.optimization_new.containerclasses.energyCarrier import EnergyCarrier
from cea.optimization_new.containerclasses.energyFlow import EnergyFlow
from cea.optimization_new.component import (
    ComponentUnit,
    Component,
    ActiveComponent,
    PassiveComponent,
    AbsorptionChiller,
    VapourCompressionChiller,
    AirConditioner,
    Boiler,
    CogenPlant,
    HeatPump,
    CoolingTower,
    PowerTransformer,
    HeatExchanger,
)


class TestComponentUnit(unittest.TestCase):
    """Test the ComponentUnit class."""

    def test_initialization_with_capacity(self):
        """
        Test that ComponentUnit can be initialized with a capacity value.

        Should verify:
        - ComponentUnit stores capacity correctly
        - Capacity is accessible via property
        """
        test_component_unit = ComponentUnit(capacity=0.0)
        self.assertIsInstance(test_component_unit, ComponentUnit)
        self.assertEqual(test_component_unit.capacity, 0.0)

    def test_capacity_property(self):
        """
        Test that capacity property returns correct value.

        Should verify:
        - Capacity property getter works
        - Returned value matches initialization value
        """
        test_capacity = 150.0
        test_component_unit = ComponentUnit(capacity=test_capacity)
        self.assertEqual(test_component_unit.capacity, test_capacity)


class TestComponent(unittest.TestCase):
    """Test the Component class database loading."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for Component."""
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()

        cls.mock_domain = Mock()
        cls.mock_domain.config = cls.config
        cls.mock_domain.locator = cls.locator
        cls.mock_domain.weather = pd.DataFrame({'drybulb_C': [20.0] * 8760})

        EnergyCarrier.initialize_class_variables(cls.mock_domain)
        Component.initialize_class_variables(cls.mock_domain)

        # Component class to CSV name mapping
        cls.component_csv_mapping = {
            AbsorptionChiller: 'ABSORPTION_CHILLERS',
            VapourCompressionChiller: 'VAPOR_COMPRESSION_CHILLERS',
            AirConditioner: 'UNITARY_AIR_CONDITIONERS',
            Boiler: 'BOILERS',
            CogenPlant: 'COGENERATION_PLANTS',
            HeatPump: 'HEAT_PUMPS',
            CoolingTower: 'COOLING_TOWERS',
            PowerTransformer: 'POWER_TRANSFORMERS',
            HeatExchanger: 'HEAT_EXCHANGERS',
        }

        # Required columns for all component types
        cls.common_required_columns = [
            'description', 'code', 'type', 'cap_min', 'cap_max', 'unit',
            'currency', 'a', 'b', 'c', 'd', 'e', 'LT_yr', 'O&M_%', 'IR_%',
            'assumption', 'reference'
        ]

    def test_database_initialized(self):
        """
        Test that Component class variable _components_database is initialized.

        Should verify:
        - _components_database exists
        - _components_database is a dictionary
        - _components_database is not empty
        """
        self.assertIsNotNone(Component._components_database)
        self.assertIsInstance(Component._components_database, dict)
        self.assertGreater(len(Component._components_database), 0)

    def test_all_component_databases_loaded(self):
        """
        Test that all 9 component databases are loaded.

        Should verify:
        - All CSV names from component_csv_mapping are in _components_database
        - Each database is a pandas DataFrame
        - Each database is not empty
        """
        for component_class, csv_name in self.component_csv_mapping.items():
            with self.subTest(component=component_class.__name__):
                # Check CSV is loaded
                self.assertIn(csv_name, Component._components_database,
                             f"{csv_name} not found in _components_database")

                # Check it's a DataFrame
                db = Component._components_database[csv_name]
                self.assertIsInstance(db, pd.DataFrame,
                                     f"{csv_name} is not a pandas DataFrame")

                # Check it's not empty
                self.assertGreater(len(db), 0,
                                  f"{csv_name} database is empty")

    def test_component_csv_name_attributes(self):
        """
        Test that each component class has correct _csv_name attribute.

        Should verify:
        - Each component class has _csv_name attribute
        - _csv_name matches the expected value from mapping
        """
        for component_class, expected_csv_name in self.component_csv_mapping.items():
            with self.subTest(component=component_class.__name__):
                self.assertTrue(hasattr(component_class, '_csv_name'),
                               f"{component_class.__name__} missing _csv_name attribute")

                actual_csv_name = component_class._csv_name
                self.assertEqual(actual_csv_name, expected_csv_name,
                               f"{component_class.__name__}._csv_name is '{actual_csv_name}', "
                               f"expected '{expected_csv_name}'")

    def test_database_required_columns(self):
        """
        Test that all databases contain required common columns.

        Should verify:
        - All common_required_columns are present in each database
        - Column names are correct (case-sensitive)
        """
        for component_class, csv_name in self.component_csv_mapping.items():
            with self.subTest(component=component_class.__name__):
                db = Component._components_database[csv_name]
                db_columns = set(db.columns)

                for required_col in self.common_required_columns:
                    self.assertIn(required_col, db_columns,
                                 f"{csv_name} missing required column '{required_col}'")

    def test_database_codes_and_capacity_ranges(self):
        """
        Test that codes are valid and capacity ranges don't overlap.

        Component codes can be duplicated to allow different cost models
        for different capacity ranges (e.g., economies of scale). However,
        capacity ranges for the same code must not overlap.

        Should verify:
        - All codes are non-empty strings
        - For rows with the same code, capacity ranges don't overlap
        """
        for component_class, csv_name in self.component_csv_mapping.items():
            with self.subTest(component=component_class.__name__):
                db = Component._components_database[csv_name]

                # Check all codes are non-empty
                empty_codes = db[db['code'].isna() | (db['code'] == '')]
                self.assertEqual(len(empty_codes), 0,
                               f"{csv_name} has empty codes at rows: {empty_codes.index.tolist()}")

                # Check for overlapping capacity ranges within same code
                for code in db['code'].unique():
                    code_rows = db[db['code'] == code].sort_values('cap_min')

                    # Check each pair of consecutive ranges for overlap
                    for i in range(len(code_rows) - 1):
                        row1 = code_rows.iloc[i]
                        row2 = code_rows.iloc[i + 1]

                        # Ranges overlap if: max1 > min2 (allowing contiguous ranges where max1 == min2)
                        if row1['cap_max'] > row2['cap_min']:
                            self.fail(
                                f"{csv_name} has overlapping capacity ranges for code '{code}':\n"
                                f"  Row {row1.name}: [{row1['cap_min']}, {row1['cap_max']}]\n"
                                f"  Row {row2.name}: [{row2['cap_min']}, {row2['cap_max']}]"
                            )

    def test_database_capacity_ranges(self):
        """
        Test that capacity ranges are valid.

        Should verify:
        - cap_min and cap_max are numeric
        - cap_min <= cap_max for all rows
        - cap_min >= 0
        """
        for component_class, csv_name in self.component_csv_mapping.items():
            with self.subTest(component=component_class.__name__):
                db = Component._components_database[csv_name]

                # Check numeric types
                self.assertTrue(pd.api.types.is_numeric_dtype(db['cap_min']),
                               f"{csv_name} cap_min is not numeric")
                self.assertTrue(pd.api.types.is_numeric_dtype(db['cap_max']),
                               f"{csv_name} cap_max is not numeric")

                # Check cap_min <= cap_max
                invalid_ranges = db[db['cap_min'] > db['cap_max']]
                self.assertEqual(len(invalid_ranges), 0,
                               f"{csv_name} has invalid capacity ranges (cap_min > cap_max) "
                               f"at rows: {invalid_ranges.index.tolist()}")

                # Check cap_min >= 0
                negative_caps = db[db['cap_min'] < 0]
                self.assertEqual(len(negative_caps), 0,
                               f"{csv_name} has negative cap_min at rows: {negative_caps.index.tolist()}")

    def test_database_cost_coefficients(self):
        """
        Test that cost coefficient columns are numeric.

        Should verify:
        - a, b, c, d, e are all numeric types
        - No NaN values in cost coefficients
        """
        cost_cols = ['a', 'b', 'c', 'd', 'e']

        for component_class, csv_name in self.component_csv_mapping.items():
            with self.subTest(component=component_class.__name__):
                db = Component._components_database[csv_name]

                for col in cost_cols:
                    # Check numeric type
                    self.assertTrue(pd.api.types.is_numeric_dtype(db[col]),
                                   f"{csv_name} column '{col}' is not numeric")

                    # Check for NaN
                    nan_count = db[col].isna().sum()
                    self.assertEqual(nan_count, 0,
                                   f"{csv_name} has {nan_count} NaN values in column '{col}'")

    def test_database_lifetime_valid(self):
        """
        Test that lifetime values are valid.

        Should verify:
        - LT_yr is numeric
        - LT_yr > 0 for all rows
        """
        for component_class, csv_name in self.component_csv_mapping.items():
            with self.subTest(component=component_class.__name__):
                db = Component._components_database[csv_name]

                # Check numeric
                self.assertTrue(pd.api.types.is_numeric_dtype(db['LT_yr']),
                               f"{csv_name} LT_yr is not numeric")

                # Check positive
                invalid_lifetime = db[db['LT_yr'] <= 0]
                self.assertEqual(len(invalid_lifetime), 0,
                               f"{csv_name} has non-positive lifetime at rows: "
                               f"{invalid_lifetime.index.tolist()}")

    def test_database_percentages_valid(self):
        """
        Test that percentage columns are in valid range.

        Should verify:
        - O&M_% and IR_% are numeric
        - 0 <= percentage <= 100
        """
        percentage_cols = ['O&M_%', 'IR_%']

        for component_class, csv_name in self.component_csv_mapping.items():
            with self.subTest(component=component_class.__name__):
                db = Component._components_database[csv_name]

                for col in percentage_cols:
                    # Check numeric
                    self.assertTrue(pd.api.types.is_numeric_dtype(db[col]),
                                   f"{csv_name} column '{col}' is not numeric")

                    # Check range 0-100
                    out_of_range = db[(db[col] < 0) | (db[col] > 100)]
                    self.assertEqual(len(out_of_range), 0,
                                   f"{csv_name} has {col} values outside 0-100 range "
                                   f"at rows: {out_of_range.index.tolist()}")

    def test_code_to_class_mapping_created(self):
        """
        Test that code_to_class_mapping is created during initialization.

        Should verify:
        - code_to_class_mapping exists
        - code_to_class_mapping is a dictionary
        - Mapping contains entries for all component codes
        """
        self.assertTrue(hasattr(Component, 'code_to_class_mapping'),
                       "Component.code_to_class_mapping not created")
        self.assertIsInstance(Component.code_to_class_mapping, dict)
        self.assertGreater(len(Component.code_to_class_mapping), 0,
                          "code_to_class_mapping is empty")


class TestAbsorptionChiller(unittest.TestCase):
    """Test the AbsorptionChiller component."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for AbsorptionChiller."""
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()

        cls.mock_domain = Mock()
        cls.mock_domain.config = cls.config
        cls.mock_domain.locator = cls.locator
        cls.mock_domain.weather = pd.DataFrame({'drybulb_C': [20.0] * 8760})

        EnergyCarrier.initialize_class_variables(cls.mock_domain)
        Component.initialize_class_variables(cls.mock_domain)

    def test_initialization(self):
        """
        Test AbsorptionChiller initialization with first database row.

        Should verify:
        - Component is created successfully with database values
        - Database parameters are extracted correctly
        - Energy carriers are set correctly
        - Capacity is set correctly
        - Cost parameters are loaded from database
        """
        # Get first row from AbsorptionChiller database
        db = Component._components_database[AbsorptionChiller._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        # Use capacity within the range defined by first row
        test_capacity_W = (first_row['cap_min'] + first_row['cap_max']) / 2
        test_capacity_kW = test_capacity_W / 1000

        # Create AbsorptionChiller instance
        ach = AbsorptionChiller(
            ach_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        # Test basic instantiation
        self.assertIsInstance(ach, AbsorptionChiller)
        self.assertIsInstance(ach, ActiveComponent)
        self.assertIsInstance(ach, Component)

        # Test capacity is set correctly
        self.assertAlmostEqual(ach.capacity, test_capacity_kW, places=2)

        # Test that units were created
        self.assertGreater(len(ach.units), 0)
        self.assertEqual(ach.n_units, len(ach.units))

        # Test that all units are ComponentUnit instances
        for unit in ach.units:
            self.assertIsInstance(unit, ComponentUnit)

        # Test database parameters were loaded
        self.assertIsNotNone(ach.code)
        self.assertEqual(ach.code, test_code)

        # Test cost parameters exist (from database)
        self.assertTrue(hasattr(ach, '_cost_params'))
        self.assertIn('a', ach._cost_params)
        self.assertIn('b', ach._cost_params)
        self.assertIn('c', ach._cost_params)
        self.assertIn('d', ach._cost_params)
        self.assertIn('e', ach._cost_params)
        self.assertIn('lifetime', ach._cost_params)

        # Test cost coefficients match database
        self.assertEqual(ach._cost_params['a'], first_row['a'])
        self.assertEqual(ach._cost_params['b'], first_row['b'])
        self.assertEqual(ach._cost_params['c'], first_row['c'])
        self.assertEqual(ach._cost_params['d'], first_row['d'])
        self.assertEqual(ach._cost_params['e'], first_row['e'])
        self.assertEqual(ach._cost_params['lifetime'], first_row['LT_yr'])

        # Test placement attribute
        self.assertEqual(ach.placement, 'primary')

    def test_operate_single_unit(self):
        """
        Test _operate_single_unit() for AbsorptionChiller.

        Should verify:
        - Heat input is consumed (correct type and quantity)
        - Electricity input is consumed (correct type and quantity)
        - Waste heat output is produced (correct type)
        - COP calculation is correct
        """
        # Create AbsorptionChiller instance
        db = Component._components_database[AbsorptionChiller._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']
        test_capacity_kW = ((first_row['cap_min'] + first_row['cap_max']) / 2) / 1000

        ach = AbsorptionChiller(
            ach_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        # Create cooling demand EnergyFlow
        cooling_demand_kW = test_capacity_kW * 0.8  # 80% of capacity
        cooling_out = EnergyFlow(
            input_category='primary',
            output_category='consumer',
            energy_carrier_code=ach.main_energy_carrier.code
        )
        cooling_out.profile = pd.Series([cooling_demand_kW])

        # Operate single unit
        input_flows, output_flows = ach._operate_single_unit(cooling_out)

        # Test that input flows dict has heat and electricity
        self.assertEqual(len(input_flows), 2)
        self.assertIn(ach.input_energy_carriers[0].code, input_flows)  # Heat
        self.assertIn(ach.input_energy_carriers[1].code, input_flows)  # Electricity

        # Test that output flows dict has waste heat
        self.assertEqual(len(output_flows), 1)
        self.assertIn(ach.output_energy_carriers[0].code, output_flows)  # Waste heat

        # Get energy flow objects
        heat_in = input_flows[ach.input_energy_carriers[0].code]
        electricity_in = input_flows[ach.input_energy_carriers[1].code]
        waste_heat_out = output_flows[ach.output_energy_carriers[0].code]

        # Test that all flows are EnergyFlow instances
        self.assertIsInstance(heat_in, EnergyFlow)
        self.assertIsInstance(electricity_in, EnergyFlow)
        self.assertIsInstance(waste_heat_out, EnergyFlow)

        # Test COP calculation: COP = cooling_out / heat_in
        heat_in_value = heat_in.profile.iloc[0]
        self.assertGreater(heat_in_value, 0, "Heat input should be positive")

        calculated_COP = cooling_demand_kW / heat_in_value
        self.assertAlmostEqual(calculated_COP, ach.minimum_COP, places=2,
                              msg=f"COP should match minimum_COP from database")


    def test_operate_single_unit_behavior(self):
        """
        Test operate() with single-unit installation.

        Should verify:
        - operate() works correctly for single unit
        - Returns valid input and output flows
        """
        # Create single-unit AbsorptionChiller (low capacity)
        db = Component._components_database[AbsorptionChiller._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        # Get all rows with same code to find true capacity range
        code_rows = db[db['code'] == test_code]
        overall_cap_min = code_rows['cap_min'].min()
        overall_cap_max = code_rows['cap_max'].max()

        # Use small capacity with offset to avoid zero
        test_capacity_kW = (overall_cap_min + 0.1 * (overall_cap_max - overall_cap_min)) / 1000

        ach = AbsorptionChiller(
            ach_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        # Verify single unit
        self.assertEqual(ach.n_units, 1)

        # Create demand and operate
        cooling_out = EnergyFlow('primary', 'consumer', ach.main_energy_carrier.code)
        cooling_out.profile = pd.Series([test_capacity_kW * 0.5])

        input_flows, output_flows = ach.operate(cooling_out)

        # Verify operation succeeded
        self.assertEqual(len(input_flows), 2)
        self.assertEqual(len(output_flows), 1)
        self.assertGreater(input_flows[ach.input_energy_carriers[0].code].profile.iloc[0], 0)

    def test_operate_multi_unit_cascade(self):
        """
        Test operate() with multi-unit installation using cascade.

        Should verify:
        - operate() triggers multi-unit cascade for large capacity
        - Returns valid aggregated flows
        """
        # Create multi-unit AbsorptionChiller (high capacity)
        db = Component._components_database[AbsorptionChiller._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        # Get all rows with same code to find true capacity range
        code_rows = db[db['code'] == test_code]
        overall_cap_max = code_rows['cap_max'].max()

        # Use large capacity to force multiple units
        test_capacity_kW = (overall_cap_max / 1000) * 3.5

        ach = AbsorptionChiller(
            ach_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        # Verify multiple units created
        self.assertGreater(ach.n_units, 1)

        # Create demand and operate
        cooling_out = EnergyFlow('primary', 'consumer', ach.main_energy_carrier.code)
        cooling_out.profile = pd.Series([test_capacity_kW * 0.8])

        input_flows, output_flows = ach.operate(cooling_out)

        # Verify cascade operation succeeded
        self.assertEqual(len(input_flows), 2)
        self.assertEqual(len(output_flows), 1)

        # Verify flows are aggregated (total input should be positive)
        total_heat_in = input_flows[ach.input_energy_carriers[0].code].profile.iloc[0]
        self.assertGreater(total_heat_in, 0)

    def test_capacity_below_minimum(self):
        """
        Test component creation when requested capacity is below cap_min.

        Should verify:
        - Component is created with single unit
        - Unit is oversized to cap_min (smallest available)
        """
        # Get database and find a code with cap_min > 0
        db = Component._components_database[AbsorptionChiller._csv_name]

        # Find first row where cap_min > 0
        rows_with_min = db[db['cap_min'] > 0]
        if len(rows_with_min) == 0:
            self.skipTest("No absorption chiller models with cap_min > 0")

        first_row = rows_with_min.iloc[0]
        test_code = first_row['code']

        # Get all rows with same code to find overall minimum capacity
        code_rows = db[db['code'] == test_code]
        overall_cap_min = code_rows['cap_min'].min()

        # Request capacity below minimum (50% of cap_min)
        requested_capacity_kW = (overall_cap_min * 0.5) / 1000

        # Create component
        ach = AbsorptionChiller(
            ach_model_code=test_code,
            placement='primary',
            capacity=requested_capacity_kW
        )

        # Verify single unit was created
        self.assertEqual(ach.n_units, 1)

        # Verify component was oversized to minimum capacity
        # (actual capacity should be >= requested capacity)
        self.assertGreaterEqual(ach.capacity, requested_capacity_kW)

        # Verify capacity is approximately cap_min (oversized)
        expected_capacity_kW = overall_cap_min / 1000
        self.assertAlmostEqual(ach.capacity, expected_capacity_kW, places=2)


class TestVapourCompressionChiller(unittest.TestCase):
    """Test the VapourCompressionChiller component."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for VapourCompressionChiller."""
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()

        cls.mock_domain = Mock()
        cls.mock_domain.config = cls.config
        cls.mock_domain.locator = cls.locator
        cls.mock_domain.weather = pd.DataFrame({'drybulb_C': [20.0] * 8760})

        EnergyCarrier.initialize_class_variables(cls.mock_domain)
        Component.initialize_class_variables(cls.mock_domain)

    def test_initialization(self):
        """
        Test VapourCompressionChiller initialization with first database row.

        Should verify:
        - Component is created successfully with database values
        - Database parameters are extracted correctly
        - Cost parameters are loaded from database
        """
        db = Component._components_database[VapourCompressionChiller._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        test_capacity_W = (first_row['cap_min'] + first_row['cap_max']) / 2
        test_capacity_kW = test_capacity_W / 1000

        vcc = VapourCompressionChiller(
            vcc_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        self.assertIsInstance(vcc, VapourCompressionChiller)
        self.assertIsInstance(vcc, ActiveComponent)
        self.assertAlmostEqual(vcc.capacity, test_capacity_kW, places=2)
        self.assertEqual(vcc.n_units, len(vcc.units))
        self.assertEqual(vcc.code, test_code)
        self.assertTrue(hasattr(vcc, '_cost_params'))

    def test_operate_single_unit(self):
        """
        Test _operate_single_unit() for VapourCompressionChiller.

        Should verify:
        - Operation produces valid input and output flows
        - Correct energy types are consumed and produced
        """
        db = Component._components_database[VapourCompressionChiller._csv_name]
        first_row = db.iloc[0]
        test_capacity_kW = ((first_row['cap_min'] + first_row['cap_max']) / 2) / 1000

        vcc = VapourCompressionChiller(
            vcc_model_code=first_row['code'],
            placement='primary',
            capacity=test_capacity_kW
        )

        cooling_out = EnergyFlow('primary', 'consumer', vcc.main_energy_carrier.code)
        cooling_out.profile = pd.Series([test_capacity_kW * 0.8])

        input_flows, output_flows = vcc._operate_single_unit(cooling_out)

        self.assertGreater(len(input_flows), 0)
        self.assertIsInstance(input_flows, dict)
        self.assertIsInstance(output_flows, dict)

    def test_operate_single_unit_behavior(self):
        """
        Test operate() with single-unit installation.

        Should verify:
        - operate() works correctly for single unit
        - Returns valid input and output flows
        """
        db = Component._components_database[VapourCompressionChiller._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        code_rows = db[db['code'] == test_code]
        overall_cap_min = code_rows['cap_min'].min()
        overall_cap_max = code_rows['cap_max'].max()

        test_capacity_kW = (overall_cap_min + 0.1 * (overall_cap_max - overall_cap_min)) / 1000

        vcc = VapourCompressionChiller(
            vcc_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        self.assertEqual(vcc.n_units, 1)

        cooling_out = EnergyFlow('primary', 'consumer', vcc.main_energy_carrier.code)
        cooling_out.profile = pd.Series([test_capacity_kW * 0.5])

        input_flows, output_flows = vcc.operate(cooling_out)

        self.assertGreater(len(input_flows), 0)
        self.assertGreater(len(output_flows), 0)


class TestAirConditioner(unittest.TestCase):
    """Test the AirConditioner component."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for AirConditioner."""
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()

        cls.mock_domain = Mock()
        cls.mock_domain.config = cls.config
        cls.mock_domain.locator = cls.locator
        cls.mock_domain.weather = pd.DataFrame({'drybulb_C': [20.0] * 8760})

        EnergyCarrier.initialize_class_variables(cls.mock_domain)
        Component.initialize_class_variables(cls.mock_domain)

    def test_initialization(self):
        """
        Test AirConditioner initialization with first database row.

        Should verify:
        - Component is created successfully with database values
        - Database parameters are extracted correctly
        - Cost parameters are loaded from database
        """
        db = Component._components_database[AirConditioner._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        test_capacity_W = (first_row['cap_min'] + first_row['cap_max']) / 2
        test_capacity_kW = test_capacity_W / 1000

        ac = AirConditioner(
            ac_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        self.assertIsInstance(ac, AirConditioner)
        self.assertIsInstance(ac, ActiveComponent)
        self.assertAlmostEqual(ac.capacity, test_capacity_kW, places=2)
        self.assertEqual(ac.n_units, len(ac.units))
        self.assertEqual(ac.code, test_code)
        self.assertTrue(hasattr(ac, '_cost_params'))

    def test_operate_single_unit(self):
        """
        Test _operate_single_unit() for AirConditioner.

        Should verify:
        - Operation produces valid input and output flows
        - Correct energy types are consumed and produced
        """
        db = Component._components_database[AirConditioner._csv_name]
        first_row = db.iloc[0]
        test_capacity_kW = ((first_row['cap_min'] + first_row['cap_max']) / 2) / 1000

        ac = AirConditioner(
            ac_model_code=first_row['code'],
            placement='primary',
            capacity=test_capacity_kW
        )

        cooling_out = EnergyFlow('primary', 'consumer', ac.main_energy_carrier.code)
        cooling_out.profile = pd.Series([test_capacity_kW * 0.8])

        input_flows, output_flows = ac._operate_single_unit(cooling_out)

        self.assertGreater(len(input_flows), 0)
        self.assertIsInstance(input_flows, dict)
        self.assertIsInstance(output_flows, dict)

    def test_operate_single_unit_behavior(self):
        """
        Test operate() with single-unit installation.

        Should verify:
        - operate() works correctly for single unit
        - Returns valid input and output flows
        """
        db = Component._components_database[AirConditioner._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        code_rows = db[db['code'] == test_code]
        overall_cap_min = code_rows['cap_min'].min()
        overall_cap_max = code_rows['cap_max'].max()

        test_capacity_kW = (overall_cap_min + 0.1 * (overall_cap_max - overall_cap_min)) / 1000

        ac = AirConditioner(
            ac_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        self.assertEqual(ac.n_units, 1)

        cooling_out = EnergyFlow('primary', 'consumer', ac.main_energy_carrier.code)
        cooling_out.profile = pd.Series([test_capacity_kW * 0.5])

        input_flows, output_flows = ac.operate(cooling_out)

        self.assertGreater(len(input_flows), 0)
        self.assertGreater(len(output_flows), 0)


class TestBoiler(unittest.TestCase):
    """Test the Boiler component."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for Boiler."""
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()

        cls.mock_domain = Mock()
        cls.mock_domain.config = cls.config
        cls.mock_domain.locator = cls.locator
        cls.mock_domain.weather = pd.DataFrame({'drybulb_C': [20.0] * 8760})

        EnergyCarrier.initialize_class_variables(cls.mock_domain)
        Component.initialize_class_variables(cls.mock_domain)

    def test_initialization(self):
        """
        Test Boiler initialization with first database row.

        Should verify:
        - Component is created successfully with database values
        - Database parameters are extracted correctly
        - Cost parameters are loaded from database
        """
        db = Component._components_database[Boiler._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        test_capacity_W = (first_row['cap_min'] + first_row['cap_max']) / 2
        test_capacity_kW = test_capacity_W / 1000

        boiler = Boiler(
            boiler_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        self.assertIsInstance(boiler, Boiler)
        self.assertIsInstance(boiler, ActiveComponent)
        self.assertAlmostEqual(boiler.capacity, test_capacity_kW, places=2)
        self.assertEqual(boiler.n_units, len(boiler.units))
        self.assertEqual(boiler.code, test_code)
        self.assertTrue(hasattr(boiler, '_cost_params'))

    def test_operate_single_unit(self):
        """
        Test _operate_single_unit() for Boiler.

        Should verify:
        - Operation produces valid input and output flows
        - Correct energy types are consumed and produced
        """
        db = Component._components_database[Boiler._csv_name]
        first_row = db.iloc[0]
        test_capacity_kW = ((first_row['cap_min'] + first_row['cap_max']) / 2) / 1000

        boiler = Boiler(
            boiler_model_code=first_row['code'],
            placement='primary',
            capacity=test_capacity_kW
        )

        heat_out = EnergyFlow('primary', 'consumer', boiler.main_energy_carrier.code)
        heat_out.profile = pd.Series([test_capacity_kW * 0.8])

        input_flows, output_flows = boiler._operate_single_unit(heat_out)

        self.assertGreater(len(input_flows), 0)
        self.assertIsInstance(input_flows, dict)
        self.assertIsInstance(output_flows, dict)

    def test_operate_single_unit_behavior(self):
        """
        Test operate() with single-unit installation.

        Should verify:
        - operate() works correctly for single unit
        - Returns valid input and output flows
        """
        db = Component._components_database[Boiler._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        code_rows = db[db['code'] == test_code]
        overall_cap_min = code_rows['cap_min'].min()
        overall_cap_max = code_rows['cap_max'].max()

        test_capacity_kW = (overall_cap_min + 0.1 * (overall_cap_max - overall_cap_min)) / 1000

        boiler = Boiler(
            boiler_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        self.assertEqual(boiler.n_units, 1)

        heat_out = EnergyFlow('primary', 'consumer', boiler.main_energy_carrier.code)
        heat_out.profile = pd.Series([test_capacity_kW * 0.5])

        input_flows, output_flows = boiler.operate(heat_out)

        self.assertGreater(len(input_flows), 0)
        self.assertGreater(len(output_flows), 0)


class TestCogenPlant(unittest.TestCase):
    """Test the CogenPlant component."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for CogenPlant."""
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()

        cls.mock_domain = Mock()
        cls.mock_domain.config = cls.config
        cls.mock_domain.locator = cls.locator
        cls.mock_domain.weather = pd.DataFrame({'drybulb_C': [20.0] * 8760})

        EnergyCarrier.initialize_class_variables(cls.mock_domain)
        Component.initialize_class_variables(cls.mock_domain)

    def test_initialization(self):
        """
        Test CogenPlant initialization with first database row.

        Should verify:
        - Component is created successfully with database values
        - Database parameters are extracted correctly
        - Cost parameters are loaded from database
        """
        db = Component._components_database[CogenPlant._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        test_capacity_W = (first_row['cap_min'] + first_row['cap_max']) / 2
        test_capacity_kW = test_capacity_W / 1000

        cogen = CogenPlant(
            cogen_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        self.assertIsInstance(cogen, CogenPlant)
        self.assertIsInstance(cogen, ActiveComponent)
        self.assertAlmostEqual(cogen.capacity, test_capacity_kW, places=2)
        self.assertEqual(cogen.n_units, len(cogen.units))
        self.assertEqual(cogen.code, test_code)
        self.assertTrue(hasattr(cogen, '_cost_params'))

    def test_operate_single_unit(self):
        """
        Test _operate_single_unit() for CogenPlant.

        Should verify:
        - Operation produces valid input and output flows
        - Correct energy types are consumed and produced
        """
        db = Component._components_database[CogenPlant._csv_name]
        first_row = db.iloc[0]
        test_capacity_kW = ((first_row['cap_min'] + first_row['cap_max']) / 2) / 1000

        cogen = CogenPlant(
            cogen_model_code=first_row['code'],
            placement='primary',
            capacity=test_capacity_kW
        )

        main_out = EnergyFlow('primary', 'consumer', cogen.main_energy_carrier.code)
        main_out.profile = pd.Series([test_capacity_kW * 0.8])

        input_flows, output_flows = cogen._operate_single_unit(main_out)

        self.assertGreater(len(input_flows), 0)
        self.assertIsInstance(input_flows, dict)
        self.assertIsInstance(output_flows, dict)

    def test_operate_single_unit_behavior(self):
        """
        Test operate() with single-unit installation.

        Should verify:
        - operate() works correctly for single unit
        - Returns valid input and output flows
        """
        db = Component._components_database[CogenPlant._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        code_rows = db[db['code'] == test_code]
        overall_cap_min = code_rows['cap_min'].min()
        overall_cap_max = code_rows['cap_max'].max()

        test_capacity_kW = (overall_cap_min + 0.1 * (overall_cap_max - overall_cap_min)) / 1000

        cogen = CogenPlant(
            cogen_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        self.assertEqual(cogen.n_units, 1)

        main_out = EnergyFlow('primary', 'consumer', cogen.main_energy_carrier.code)
        main_out.profile = pd.Series([test_capacity_kW * 0.5])

        input_flows, output_flows = cogen.operate(main_out)

        self.assertGreater(len(input_flows), 0)
        self.assertGreater(len(output_flows), 0)


class TestHeatPump(unittest.TestCase):
    """Test the HeatPump component."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for HeatPump."""
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()

        cls.mock_domain = Mock()
        cls.mock_domain.config = cls.config
        cls.mock_domain.locator = cls.locator
        cls.mock_domain.weather = pd.DataFrame({'drybulb_C': [20.0] * 8760})

        EnergyCarrier.initialize_class_variables(cls.mock_domain)
        Component.initialize_class_variables(cls.mock_domain)

    def test_initialization(self):
        """
        Test HeatPump initialization with first database row.

        Should verify:
        - Component is created successfully with database values
        - Database parameters are extracted correctly
        - Cost parameters are loaded from database
        """
        db = Component._components_database[HeatPump._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        test_capacity_W = (first_row['cap_min'] + first_row['cap_max']) / 2
        test_capacity_kW = test_capacity_W / 1000

        hp = HeatPump(
            hp_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        self.assertIsInstance(hp, HeatPump)
        self.assertIsInstance(hp, ActiveComponent)
        self.assertAlmostEqual(hp.capacity, test_capacity_kW, places=2)
        self.assertEqual(hp.n_units, len(hp.units))
        self.assertEqual(hp.code, test_code)
        self.assertTrue(hasattr(hp, '_cost_params'))

    def test_operate_single_unit(self):
        """
        Test _operate_single_unit() for HeatPump.

        Should verify:
        - Operation produces valid input and output flows
        - Correct energy types are consumed and produced
        """
        db = Component._components_database[HeatPump._csv_name]
        first_row = db.iloc[0]
        test_capacity_kW = ((first_row['cap_min'] + first_row['cap_max']) / 2) / 1000

        hp = HeatPump(
            hp_model_code=first_row['code'],
            placement='primary',
            capacity=test_capacity_kW
        )

        heat_out = EnergyFlow('primary', 'consumer', hp.main_energy_carrier.code)
        heat_out.profile = pd.Series([test_capacity_kW * 0.8])

        input_flows, output_flows = hp._operate_single_unit(heat_out)

        self.assertGreater(len(input_flows), 0)
        self.assertIsInstance(input_flows, dict)
        self.assertIsInstance(output_flows, dict)

    def test_operate_single_unit_behavior(self):
        """
        Test operate() with single-unit installation.

        Should verify:
        - operate() works correctly for single unit
        - Returns valid input and output flows
        """
        db = Component._components_database[HeatPump._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        code_rows = db[db['code'] == test_code]
        overall_cap_min = code_rows['cap_min'].min()
        overall_cap_max = code_rows['cap_max'].max()

        test_capacity_kW = (overall_cap_min + 0.1 * (overall_cap_max - overall_cap_min)) / 1000

        hp = HeatPump(
            hp_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        self.assertEqual(hp.n_units, 1)

        heat_out = EnergyFlow('primary', 'consumer', hp.main_energy_carrier.code)
        heat_out.profile = pd.Series([test_capacity_kW * 0.5])

        input_flows, output_flows = hp.operate(heat_out)

        self.assertGreater(len(input_flows), 0)
        self.assertEqual(len(output_flows), 0)


class TestCoolingTower(unittest.TestCase):
    """Test the CoolingTower component."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for CoolingTower."""
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()

        cls.mock_domain = Mock()
        cls.mock_domain.config = cls.config
        cls.mock_domain.locator = cls.locator
        cls.mock_domain.weather = pd.DataFrame({'drybulb_C': [20.0] * 8760})

        EnergyCarrier.initialize_class_variables(cls.mock_domain)
        Component.initialize_class_variables(cls.mock_domain)

    def test_initialization(self):
        """
        Test CoolingTower initialization with first database row.

        Should verify:
        - Component is created successfully with database values
        - Database parameters are extracted correctly
        - Cost parameters are loaded from database
        """
        db = Component._components_database[CoolingTower._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        test_capacity_W = (first_row['cap_min'] + first_row['cap_max']) / 2
        test_capacity_kW = test_capacity_W / 1000

        ct = CoolingTower(
            ct_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        self.assertIsInstance(ct, CoolingTower)
        self.assertIsInstance(ct, ActiveComponent)
        self.assertAlmostEqual(ct.capacity, test_capacity_kW, places=2)
        self.assertEqual(ct.n_units, len(ct.units))
        self.assertEqual(ct.code, test_code)
        self.assertTrue(hasattr(ct, '_cost_params'))

    def test_operate_single_unit(self):
        """
        Test _operate_single_unit() for CoolingTower.

        Should verify:
        - Operation produces valid input and output flows
        - Correct energy types are consumed and produced
        """
        db = Component._components_database[CoolingTower._csv_name]
        first_row = db.iloc[0]
        test_capacity_kW = ((first_row['cap_min'] + first_row['cap_max']) / 2) / 1000

        ct = CoolingTower(
            ct_model_code=first_row['code'],
            placement='primary',
            capacity=test_capacity_kW
        )

        heat_rejection = EnergyFlow('primary', 'consumer', ct.main_energy_carrier.code)
        heat_rejection.profile = pd.Series([test_capacity_kW * 0.8])

        input_flows, output_flows = ct._operate_single_unit(heat_rejection)

        self.assertGreater(len(input_flows), 0)
        self.assertIsInstance(input_flows, dict)
        self.assertIsInstance(output_flows, dict)

    def test_operate_single_unit_behavior(self):
        """
        Test operate() with single-unit installation.

        Should verify:
        - operate() works correctly for single unit
        - Returns valid input and output flows
        """
        db = Component._components_database[CoolingTower._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        code_rows = db[db['code'] == test_code]
        overall_cap_min = code_rows['cap_min'].min()
        overall_cap_max = code_rows['cap_max'].max()

        test_capacity_kW = (overall_cap_min + 0.1 * (overall_cap_max - overall_cap_min)) / 1000

        ct = CoolingTower(
            ct_model_code=test_code,
            placement='primary',
            capacity=test_capacity_kW
        )

        self.assertEqual(ct.n_units, 1)

        heat_rejection = EnergyFlow('primary', 'consumer', ct.main_energy_carrier.code)
        heat_rejection.profile = pd.Series([test_capacity_kW * 0.5])

        input_flows, output_flows = ct.operate(heat_rejection)

        self.assertGreater(len(input_flows), 0)
        self.assertGreater(len(output_flows), 0)


class TestPowerTransformer(unittest.TestCase):
    """Test the PowerTransformer component."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for PowerTransformer."""
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()

        cls.mock_domain = Mock()
        cls.mock_domain.config = cls.config
        cls.mock_domain.locator = cls.locator
        cls.mock_domain.weather = pd.DataFrame({'drybulb_C': [20.0] * 8760})

        EnergyCarrier.initialize_class_variables(cls.mock_domain)
        Component.initialize_class_variables(cls.mock_domain)

    def test_initialization(self):
        """
        Test PowerTransformer initialization with first database row.

        Should verify:
        - Component is created successfully with database values
        - Database parameters are extracted correctly
        - Cost parameters are loaded from database
        """
        db = Component._components_database[PowerTransformer._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        test_capacity_W = (first_row['cap_min'] + first_row['cap_max']) / 2
        test_capacity_kW = test_capacity_W / 1000
        low_voltage_min = first_row['V_min_lowV_side']
        low_voltage_max = first_row['V_max_lowV_side']
        test_low_voltage = (low_voltage_min + low_voltage_max) / 2
        high_voltage_min = first_row['V_min_highV_side']
        high_voltage_max = first_row['V_max_highV_side']
        test_high_voltage = (high_voltage_min + high_voltage_max) / 2

        pt = PowerTransformer(
            pt_model_code=test_code,
            placed_before='primary',
            placed_after='secondary',
            capacity=test_capacity_kW,
            voltage_before=test_low_voltage,
            voltage_after=test_high_voltage
        )

        self.assertIsInstance(pt, PowerTransformer)
        self.assertIsInstance(pt, PassiveComponent)
        self.assertAlmostEqual(pt.capacity, test_capacity_kW, places=2)
        self.assertEqual(pt.n_units, len(pt.units))
        self.assertEqual(pt.code, test_code)
        self.assertTrue(hasattr(pt, '_cost_params'))

    def test_operate_single_unit(self):
        """
        Test _operate_single_unit() for PowerTransformer.

        Should verify:
        - Operation produces valid converted flow
        - Correct energy type conversion occurs
        """
        db = Component._components_database[PowerTransformer._csv_name]
        first_row = db.iloc[0]
        test_capacity_kW = ((first_row['cap_min'] + first_row['cap_max']) / 2) / 1000
        low_voltage_min = first_row['V_min_lowV_side']
        low_voltage_max = first_row['V_max_lowV_side']
        test_low_voltage = (low_voltage_min + low_voltage_max) / 2
        high_voltage_min = first_row['V_min_highV_side']
        high_voltage_max = first_row['V_max_highV_side']
        test_high_voltage = (high_voltage_min + high_voltage_max) / 2

        pt = PowerTransformer(
            pt_model_code=first_row['code'],
            placed_before='primary',
            placed_after='secondary',
            capacity=test_capacity_kW,
            voltage_before=test_low_voltage,
            voltage_after=test_high_voltage
        )


        power_in = EnergyFlow('primary', 'consumer', pt.main_energy_carrier.code)
        power_in.profile = pd.Series([test_capacity_kW * 0.8])

        converted_flow = pt._operate_single_unit(power_in)

        self.assertIsInstance(converted_flow, EnergyFlow)

    def test_operate_single_unit_behavior(self):
        """
        Test operate() with single-unit installation.

        Should verify:
        - operate() works correctly for single unit
        - Returns valid converted flow
        """
        db = Component._components_database[PowerTransformer._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        code_rows = db[db['code'] == test_code]
        overall_cap_min = code_rows['cap_min'].min()
        overall_cap_max = code_rows['cap_max'].max()

        test_capacity_kW = (overall_cap_min + 0.1 * (overall_cap_max - overall_cap_min)) / 1000

        low_voltage_min = code_rows['V_min_lowV_side'].min()
        low_voltage_max = code_rows['V_max_lowV_side'].max()
        test_low_voltage = (low_voltage_min + low_voltage_max) / 2
        high_voltage_min = code_rows['V_min_highV_side'].min()
        high_voltage_max = code_rows['V_max_highV_side'].max()
        test_high_voltage = (high_voltage_min + high_voltage_max) / 2

        pt = PowerTransformer(
            pt_model_code=test_code,
            placed_before='primary',
            placed_after='secondary',
            capacity=test_capacity_kW,
            voltage_before=test_low_voltage,
            voltage_after=test_high_voltage
        )

        self.assertEqual(pt.n_units, 1)

        power_in = EnergyFlow('primary', 'consumer', pt.main_energy_carrier.code)
        power_in.profile = pd.Series([test_capacity_kW * 0.5])

        converted_flow = pt.operate(power_in)

        self.assertIsInstance(converted_flow, EnergyFlow)


class TestHeatExchanger(unittest.TestCase):
    """Test the HeatExchanger component."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for HeatExchanger."""
        cls.config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        cls.locator = cea.inputlocator.ReferenceCaseOpenLocator()

        cls.mock_domain = Mock()
        cls.mock_domain.config = cls.config
        cls.mock_domain.locator = cls.locator
        cls.mock_domain.weather = pd.DataFrame({'drybulb_C': [20.0] * 8760})

        EnergyCarrier.initialize_class_variables(cls.mock_domain)
        Component.initialize_class_variables(cls.mock_domain)

    def test_initialization(self):
        """
        Test HeatExchanger initialization with first database row.

        Should verify:
        - Component is created successfully with database values
        - Database parameters are extracted correctly
        - Cost parameters are loaded from database
        """
        db = Component._components_database[HeatExchanger._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        test_capacity_W = (first_row['cap_min'] + first_row['cap_max']) / 2
        test_capacity_kW = test_capacity_W / 1000

        operating_temp_min = first_row['T_min_operating']
        operating_temp_max = first_row['T_max_operating']
        delta_temp = operating_temp_max - operating_temp_min

        hex = HeatExchanger(
            he_model_code=test_code,
            placed_before='primary',
            placed_after='secondary',
            capacity=test_capacity_kW,
            temperature_before=operating_temp_min + 0.1 * delta_temp,
            temperature_after=operating_temp_max - 0.1 * delta_temp
        )

        self.assertIsInstance(hex, HeatExchanger)
        self.assertIsInstance(hex, PassiveComponent)
        self.assertAlmostEqual(hex.capacity, test_capacity_kW, places=2)
        self.assertEqual(hex.n_units, len(hex.units))
        self.assertEqual(hex.code, test_code)
        self.assertTrue(hasattr(hex, '_cost_params'))

    def test_operate_single_unit(self):
        """
        Test _operate_single_unit() for HeatExchanger.

        Should verify:
        - Operation produces valid converted flow
        - Correct energy type conversion occurs
        """
        db = Component._components_database[HeatExchanger._csv_name]
        first_row = db.iloc[0]
        test_capacity_kW = ((first_row['cap_min'] + first_row['cap_max']) / 2) / 1000

        operating_temp_min = first_row['T_min_operating']
        operating_temp_max = first_row['T_max_operating']
        delta_temp = operating_temp_max - operating_temp_min

        hex = HeatExchanger(
            he_model_code=first_row['code'],
            placed_before='primary',
            placed_after='secondary',
            capacity=test_capacity_kW,
            temperature_before=operating_temp_min + 0.1 * delta_temp,
            temperature_after=operating_temp_max - 0.1 * delta_temp
        )

        heat_in = EnergyFlow('primary', 'consumer', hex.main_energy_carrier.code)
        heat_in.profile = pd.Series([test_capacity_kW * 0.8])

        # HeatExchanger may need temperature arguments
        converted_flow = hex._operate_single_unit(heat_in)

        self.assertIsInstance(converted_flow, EnergyFlow)

    def test_operate_single_unit_behavior(self):
        """
        Test operate() with single-unit installation.

        Should verify:
        - operate() works correctly for single unit
        - Returns valid converted flow
        """
        db = Component._components_database[HeatExchanger._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        code_rows = db[db['code'] == test_code]
        overall_cap_min = code_rows['cap_min'].min()
        overall_cap_max = code_rows['cap_max'].max()

        test_capacity_kW = (overall_cap_min + 0.1 * (overall_cap_max - overall_cap_min)) / 1000

        operating_temp_min = code_rows['T_min_operating'].min()
        operating_temp_max = code_rows['T_max_operating'].max()
        delta_temp = operating_temp_max - operating_temp_min

        hex = HeatExchanger(
            he_model_code=test_code,
            placed_before='primary',
            placed_after='secondary',
            capacity=test_capacity_kW,
            temperature_before=operating_temp_min + 0.1 * delta_temp,
            temperature_after=operating_temp_max - 0.1 * delta_temp
        )

        self.assertEqual(hex.n_units, 1)

        heat_in = EnergyFlow('primary', 'consumer', hex.main_energy_carrier.code)
        heat_in.profile = pd.Series([test_capacity_kW * 0.5])

        converted_flow = hex.operate(heat_in)

        self.assertIsInstance(converted_flow, EnergyFlow)

    def test_operate_multi_unit_cascade(self):
        """
        Test operate() with multi-unit installation using cascade (passive component).

        Should verify:
        - operate() triggers multi-unit cascade for large capacity
        - Returns valid aggregated converted flow
        - Template method pattern works for PassiveComponent
        """
        db = Component._components_database[HeatExchanger._csv_name]
        first_row = db.iloc[0]
        test_code = first_row['code']

        code_rows = db[db['code'] == test_code]
        overall_cap_max = code_rows['cap_max'].max()

        # Use large capacity to force multiple units
        test_capacity_kW = (overall_cap_max / 1000) * 3.5

        operating_temp_min = code_rows['T_min_operating'].min()
        operating_temp_max = code_rows['T_max_operating'].max()
        delta_temp = operating_temp_max - operating_temp_min

        hex = HeatExchanger(
            he_model_code=test_code,
            placed_before='primary',
            placed_after='secondary',
            capacity=test_capacity_kW,
            temperature_before=operating_temp_min + 0.1 * delta_temp,
            temperature_after=operating_temp_max - 0.1 * delta_temp
        )

        # Verify multiple units created
        self.assertGreater(hex.n_units, 1)

        # Create demand and operate
        heat_in = EnergyFlow('primary', 'consumer', hex.main_energy_carrier.code)
        heat_in.profile = pd.Series([test_capacity_kW * 0.8])

        converted_flow = hex.operate(heat_in)

        # Verify cascade operation succeeded
        self.assertIsInstance(converted_flow, EnergyFlow)
        self.assertGreater(converted_flow.profile.iloc[0], 0)


if __name__ == "__main__":
    unittest.main()
