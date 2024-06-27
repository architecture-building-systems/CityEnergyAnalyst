import pandas as pd
import matplotlib.pyplot as plt
from cea.utilities.dbf import dbf_to_dataframe

# Reading CSV files
embodied_results_fossil = pd.read_csv(r"C:\Users\mmeshkin\Documents\Speed2Zero\Trails Simulation\Altstetten_2060_R1\R1_2060_SIA380_S9\outputs\data\emissions\Total_LCA_embodied.csv")
embodied_results_uptake = pd.read_csv(r"C:\Users\mmeshkin\Documents\Speed2Zero\Trails Simulation\Altstetten_2060_R1\R1_2060_SIA380_S10\outputs\data\emissions\Total_LCA_embodied.csv")

# Reading Excel file
typology = dbf_to_dataframe(r"C:\Users\mmeshkin\Documents\Speed2Zero\Trails Simulation\Altstetten_2060_R1\R1_2060_SIA380_S10\inputs\building-properties\typology.dbf")

# Set the standard to filter based on that
standard = ['STANDARD10']

# Filter Retrofit function
def filter_retrofit(emission_type, typology, standard):
    # Assuming 'STANDARD' is the column in typology to filter on
    filter_mask = typology['STANDARD'].isin(standard)
    filtered_typology = typology[filter_mask]
    # Make sure the 'Name' column is correctly specified for merging
    filtered_emission = pd.merge(emission_type, filtered_typology, how='inner', on='Name')
    return filtered_emission

# Plot Data By Component function
def plot_data_by_component(uptake, fossil):
    ghg_wall = [uptake['Embodied_wall'].sum(), fossil['Embodied_wall'].sum(), 0]
    ghg_roof = [uptake['Embodied_roof'].sum(), fossil['Embodied_roof'].sum(), 0]
    ghg_base = [uptake['Embodied_base'].sum(), fossil['Embodied_base'].sum(), 0]
    zero_space = [0, 0, 0]

    breakdown_components = pd.DataFrame([ghg_base, zero_space, ghg_roof, zero_space, ghg_wall], columns=['Biogenic Carbon Uptake', 'Fossil Emissions', 'Padding'])
    return breakdown_components

# Applying filters
filtered_uptake = filter_retrofit(embodied_results_uptake, typology, standard)
filtered_fossil = filter_retrofit(embodied_results_fossil, typology, standard)

# Generating data for plot
breakdown_components = plot_data_by_component(filtered_uptake, filtered_fossil)

# Plotting
fig, ax = plt.subplots()
breakdown_components.div(1000).iloc[:, [0, 1]].plot(kind='bar', stacked=True, color=['blue', 'orange'], ax=ax)
ax.set_title('Breakdown Retrofitted Component ktonnCO2eq.')
ax.set_ylabel('ktonnCO2eq.')
ax.set_xticklabels(['Basement', '', 'Roof', '', 'Wall'], rotation=0)
ax.legend(['Biogenic Carbon Uptake', 'Fossil Emissions'])
plt.show()
