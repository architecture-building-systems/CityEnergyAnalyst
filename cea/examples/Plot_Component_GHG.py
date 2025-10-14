import pandas as pd
import matplotlib.pyplot as plt
from cea.utilities.dbf import dbf_to_dataframe

# Reading the CSV file that contains both fossil emissions and uptake
embodied_results_fossil = pd.read_csv(r"C:\Users\mmeshkin\Documents\Speed2Zero\SecondYear\CEA_simulations\NewBuiling_Zurich4D\Tes_embodied_Aocc\outputs\data\emissions\Total_LCA_embodied.csv")

# Reading the typology data
typology = dbf_to_dataframe(r"C:\Users\mmeshkin\Documents\Speed2Zero\SecondYear\CEA_simulations\NewBuiling_Zurich4D\Tes_embodied_Aocc\inputs\building-properties\typology.dbf")

# Set the standard to filter based on that
standard = ['STANDARD12']

# Filter Retrofit function
def filter_retrofit(emission_type, typology, standard):
    # Filter based on 'STANDARD' column in typology
    filter_mask = typology['STANDARD'].isin(standard)
    filtered_typology = typology[filter_mask]
    # Merge emissions data with typology based on the 'Name' column
    filtered_emission = pd.merge(emission_type, filtered_typology, how='inner', on='Name')
    return filtered_emission

# Plot Data By Component function
def plot_data_by_component(filtered_fossil):
    # Summing the fossil and uptake values for each building component
    ghg_wall = [filtered_fossil['UPTAKE_WALL_tonCO2'].sum(), filtered_fossil['GWP_WALL_tonCO2'].sum(), 0]
    ghg_roof = [filtered_fossil['UPTAKE_ROOF_tonCO2'].sum(), filtered_fossil['GWP_ROOF_tonCO2'].sum(), 0]
    ghg_floor = [filtered_fossil['UPTAKE_FLOOR_tonCO2'].sum(), filtered_fossil['GWP_FLOOR_tonCO2'].sum(), 0]
    zero_space = [0, 0, 0]

    # Creating a DataFrame for the stacked bar plot
    breakdown_components = pd.DataFrame([ghg_floor, zero_space, ghg_roof, zero_space, ghg_wall],
                                        columns=['Biogenic Carbon Uptake', 'Fossil Emissions', 'Padding'])
    return breakdown_components

# Applying filters
filtered_fossil = filter_retrofit(embodied_results_fossil, typology, standard)

# Generating data for plot
breakdown_components = plot_data_by_component(filtered_fossil)

# Plotting the data
fig, ax = plt.subplots()
breakdown_components.iloc[:, [0, 1]].plot(kind='bar', stacked=True, color=['blue', 'orange'], ax=ax)
ax.set_title('Breakdown Retrofitted Component tonCO2eq.')
ax.set_ylabel('tonCO2eq.')
ax.set_xticklabels(['Basement', '', 'Roof', '', 'Wall'], rotation=0)
ax.legend(['Biogenic Carbon Uptake', 'Fossil Emissions'])
plt.show()
