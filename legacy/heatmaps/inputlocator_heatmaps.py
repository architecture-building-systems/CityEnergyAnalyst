# these methods have been removed from the inputlocator due to the heatmaps script being retired to legacy.


# HEATMAPS
def get_heatmaps_demand_folder(self):
    """scenario/outputs/plots/heatmaps"""
    return self._ensure_folder(self.get_plots_folder('heatmaps'))

def get_heatmaps_emission_folder(self):
    """scenario/outputs/plots/heatmaps"""
    return self._ensure_folder(self.get_plots_folder('heatmaps'))