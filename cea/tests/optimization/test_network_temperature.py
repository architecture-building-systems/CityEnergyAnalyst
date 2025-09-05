import unittest

class TestNetworkTemperature(unittest.TestCase):
    """Unit tests for the target functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up resources shared across all test cases."""
        # Example: Load shared test data or initialize configurations
        cls.shared_resource = "some_shared_resource"

    def setUp(self):
        """Set up resources specific to each individual test."""
        # Example: Reinitialize a variable or mock dependencies
        self.test_data = {"key": "value"}
        self.some_variable = 0

    def test_temperature_edge_cases(self):
        """Test temperatures around the admitted network temperature range."""
        # Test the lower bound
        self.assertEqual(set_network_temperature('DC', 0), 0,
                         msg="The set_network_temperature function did not return the expected value for the lower "
                             "bound of 0°C.")
        # Test the upper bound
        self.assertEqual(set_network_temperature('DH', 150), 150,
                         msg="The set_network_temperature function did not return the expected value for the upper "
                             "bound of 150°C.")


    def test_function_with_invalid_input(self):
        """Test the function with invalid input."""
        input_data = "invalid"  # Example invalid input
        with self.assertRaises(TypeError, msg="Invalid input did not raise expected TypeError"):
            set_network_temperature(input_data, "temperature")

    def tearDown(self):
        """Clean up resources specific to each individual test."""
        # Example: Reset or release resources
        self.test_data = None
        self.some_variable = None

    @classmethod
    def tearDownClass(cls):
        """Clean up shared resources."""
        cls.shared_resource = None


# Example function being tested
def set_network_temperature(network_type, temperature):
    """Example function for testing."""
    standard_dh_temperature = 60 #°C
    standard_dc_temperature = 10 #°C
    min_network_temperature = 0 #°C
    max_network_temperature = 150 #°C
    yearly_average_temperature = 20 # TODO: change to something like self.weather['drybulb_C'].mean()

    if temperature is None:
        if network_type == "DH":
            temperature = standard_dh_temperature
        elif network_type == "DC":
            temperature = standard_dc_temperature

    if not isinstance(temperature, (float, int)):
        raise TypeError("The network temperature needs to be a numerical value in °C.")

    if network_type == "DH":
        if not yearly_average_temperature <= temperature <= max_network_temperature:
            raise ValueError("For district heating networks, the network temperature needs to fall between the"
                             f"average outdoor temperature {yearly_average_temperature}°C and "
                             f"{max_network_temperature}°C. Please adjust your configurations accordingly.")
    elif network_type == "DC":
        if not min_network_temperature <= temperature <= yearly_average_temperature:
            raise ValueError("For district cooling networks, the network temperature needs to fall between the"
                             f"{min_network_temperature}°C and the average outdoor temperature "
                             f"{yearly_average_temperature}°C. Please adjust your configurations accordingly.")

    return temperature





# Run the tests
if __name__ == "__main__":
    unittest.main()

