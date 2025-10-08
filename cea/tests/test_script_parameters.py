"""Test for duplicate parameters in script definitions"""

import unittest
import cea.scripts
import cea.config


class TestScriptParameters(unittest.TestCase):
    """Test that script parameters are correctly defined in scripts.yml"""

    def test_no_duplicate_parameters_in_scripts(self):
        """
        Check that each script doesn't have duplicate parameters in its parameter list.
        This test goes through each script defined in scripts.yml and verifies that
        no parameter is listed more than once, by expanding each section and checking for duplicates.
        """
        config = cea.config.Configuration()
        scripts_with_duplicates = {} # script name -> dict of duplicate param -> section names

        for script in cea.scripts.list_scripts(config.plugins):
            # Parse and check all parameters for duplicates
            seen_params = dict() # param name -> section name
            duplicate_params = dict()
            for section, parameter in config.matching_parameters(script.parameters):
                if parameter.name in seen_params:
                    if parameter.name in duplicate_params:
                        duplicate_params[parameter.name].append(section.name)
                    else:
                        duplicate_params[parameter.name] = [seen_params[parameter.name], section.name]
                else:
                    seen_params[parameter.name] = section.name

            if duplicate_params:
                scripts_with_duplicates[script.name] = duplicate_params

        # Build error message if there are duplicates
        if scripts_with_duplicates:
            error_msg = "\nFound scripts with duplicate parameters:\n"
            for script_name, info in scripts_with_duplicates.items():
                error_msg += f"\nScript: {script_name}\n"
                for param, sections in info.items():
                    error_msg += f"  - '{param}' appears in sections: {' '.join(sections)}\n"
            self.fail(error_msg)


if __name__ == "__main__":
    unittest.main()
