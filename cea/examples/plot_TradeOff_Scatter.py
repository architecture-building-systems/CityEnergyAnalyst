
import pandas as pd
import matplotlib.pyplot as plt
from cea.utilities.dbf import dbf_to_dataframe

# Reading CSV files
embodied_results_fossil = pd.read_csv(r"C:\Users\mmeshkin\Documents\Speed2Zero\Trails Simulation\Altstetten_2060_R1\R1_2060_SIA380_S9\outputs\data\emissions\Total_LCA_embodied.csv")
embodied_results_uptake = pd.read_csv(r"C:\Users\mmeshkin\Documents\Speed2Zero\Trails Simulation\Altstetten_2060_R1\R1_2060_SIA380_S10\outputs\data\emissions\Total_LCA_embodied.csv")
operational_results = pd.read_csv(r"C:\Users\mmeshkin\Documents\Speed2Zero\Trails Simulation\Altstetten_2060_R1\R1_2060_SIA380_S12\outputs\data\emissions\Total_LCA_operation.csv")

# Reading Excel file
typology = dbf_to_dataframe(r"C:\Users\mmeshkin\Documents\Speed2Zero\Trails Simulation\Altstetten_2060_R1\R1_2060_SIA380_S10\inputs\building-properties\typology.dbf")

# Set the standard to filter based on that
standard = ['STANDARD10']

# Filtering function
def filter_retrofit(emission_type, typology, standard):
    # Filter based on standard
    filtered_typology = typology[typology['STANDARD'] == standard]
    # Joining tables
    return pd.merge(emission_type, filtered_typology, how='inner')

# Applying filter function
standard = 'STANDARD10'
filtered_uptake = filter_retrofit(embodied_results_uptake, typology, standard)
filtered_fossil = filter_retrofit(embodied_results_fossil, typology, standard)

# Calculating values
emb_uptake = filtered_uptake['GHG_sys_embodied_kgCO2m2yr'] * filtered_uptake['GFA_m2']
emb_fossil = filtered_fossil['GHG_sys_embodied_kgCO2m2yr'] * filtered_fossil['GFA_m2']

gfa_filter = filtered_fossil['GFA_m2'].sum()

fossil_filter_total = emb_fossil.sum() / gfa_filter
uptake_filter_total = emb_uptake.sum() / gfa_filter

operation_total = (operational_results['GHG_sys_tonCO2'] * 1000).sum() / operational_results['GFA_m2'].sum()

total_emission_fossil = fossil_filter_total + operation_total
share_embodied_fossil = (fossil_filter_total / total_emission_fossil) * 100

# Plotting
fig, ax = plt.subplots()
sc = ax.scatter(share_embodied_fossil, total_emission_fossil, c=uptake_filter_total, cmap='cool', s=250)
plt.colorbar(sc, label='Carbon uptake (KgCO2eq./m2y)')
ax.set_xlabel('Share of embodied (%)')
ax.set_ylabel('Total emission(KgCO2eq./m^2y)')
ax.set_xlim([0, 100])
ax.set_ylim([0, total_emission_fossil + 2])
plt.title('Trade-off: Embodied fossil to total emission and biogenic carbon uptake')
plt.grid(True)
plt.show()
