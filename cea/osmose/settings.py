def get_start_t(timesteps):
    if timesteps == 168:
        start_t = 5064  # Average Annual 7/30-8/5: 5040-5207, 4872(SAT)
    elif timesteps == 24:
        start_t = 3240  # 5/16: 3240,
    return start_t

# import from config # TODO: add to config
TECHS = ['HCS_coil', 'HCS_ER0', 'HCS_3for2', 'HCS_LD']
# TECHS = ['HCS_ER0']
specified_buildings = ["B001","B002","B006"]
#specified_buildings = ["B001","B002","B003","B004","B005","B006","B007","B008","B009","B010"]
timesteps = 168  # 168 (week)
season = 'Winter'
start_t = get_start_t(timesteps)
osmose_project_path = "C:\\Users\\Zhongming\\Documents\\hcs_windows_ABU_Winter\\Projects"
ampl_lic_path = "C:\\Users\\Zhongming\\Desktop\\SH\\ampl"
result_destination = "C:\\Users\\Zhongming\\Documents\\WP1_results"
new_calculation = False


