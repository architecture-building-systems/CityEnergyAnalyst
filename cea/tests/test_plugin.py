"""Test the cea.plugin module"""

import unittest
import cea.config
import cea.plots.cache
import cea.plugin


class TestPlugin(unittest.TestCase):
    def test_plugin_plot_functionality(self):
        """Test the plugin plot functionality that was in the main block"""
        config = cea.config.Configuration()
        cache = cea.plots.cache.NullPlotCache()
        
        # Only test if plugins are available
        if config.plugins:
            plugin = config.plugins[0]

            self.assertTrue(hasattr(plugin, 'scripts'))
            self.assertTrue(hasattr(plugin, 'plot_categories'))
            self.assertTrue(hasattr(plugin, 'schemas'))
            self.assertTrue(hasattr(plugin, 'config'))

            # Test that plugin has plot_categories
            plot_categories = list(plugin.plot_categories)
            if plot_categories:
                category = plot_categories[0]
                
                # Test that category has plots
                plots = list(category.plots)
                if plots:
                    plot_class = plots[0]
                    
                    # Test plot class attributes
                    self.assertTrue(hasattr(plot_class, 'expected_parameters'))
                    self.assertTrue(hasattr(plot_class, 'name'))
                    self.assertTrue(hasattr(plot_class, 'category_path'))
                    
                    # Test plot instantiation
                    plot = plot_class(config.project, {"scenario-name": config.scenario_name}, cache)
                    self.assertIsNotNone(plot.category_path)

    def test_instantiate_plugin(self):
        """Test the instantiate_plugin function"""
        # Test with invalid plugin name
        with self.assertWarns(UserWarning):
            result = cea.plugin.instantiate_plugin("invalid.plugin.name")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()