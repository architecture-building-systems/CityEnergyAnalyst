
# import from config # TODO: add to config

## GENERAL ##
T_b_CDD = 25.0
# TECHS = ['HCS_LD', 'HCS_coil', 'HCS_ER0', 'HCS_3for2', 'HCS_IEHX']
# TECHS = ['HCS_base_LD', 'HCS_base_coil', 'HCS_base_3for2', 'HCS_base_ER0', 'HCS_base_IEHX',  'HCS_base']
# TECHS = ['HCS_base_LD', 'HCS_base_IEHX', 'HCS_base_ER0']
TECHS = ['N_3for2'] # ONLY one tech if running moga via wp3
# timesteps = [5136, 5144, 5145, 5147, 5148]  # 168 (week) [5389]
# timesteps = [5145]  # 168 (week) [5389]
timesteps = "typical hours"  # 168 (week) [5389]
number_of_typical_hours = 46
# timesteps = "typical days"  # 168 (week)
# timesteps = 'dtw hours'

## cluster evaluation ##
cluster_type = 'hour'  # 'day' or 'hour'

## district to evaluate ##
path_to_district_folder = 'C:\\SG_cases\\SDC_small'
osmose_outMsg_path = "\\s_001\\opt\\hc_outmsg.txt"

## post processing ##
PLOTS = ['electricity_usages','air_flow','OAU_T_w_supply','exergy_usages', 'humidity_balance', 'humidity_storage', 'heat_balance']
post_process_json = True    # True to extract information from out.json
remove_json = True          # True to remove out.json after extracting information
remove_jpg = False          # True to remove the plot files and only keep txt
post_process_osmose = True
new_calculation = False

# GENERAL INPUTS
season = 'Summer'
specified_buildings = ["B005"]
# specified_buildings = ["B001","B002","B005","B006","B009"]
# specified_buildings = ["B003","B008"]
# specified_buildings = ["B001","B002","B003","B004","B005","B006","B007","B008","B009","B010"]
cases = ['WTP_CBD_m_WP1_RET'] # ONLY relevant for wp1.py
# cases = ['WTP_CBD_m_WP1_HOT']

## LAPTOP ##
ampl_lic_path = "C:\\Users\\Shanshan\\Desktop\\ampl"
# Branch mk
osmose_project_path = "E:\\OSMOSE_projects\\HCS_mk\\Projects"
osmose_project_data_path = osmose_project_path + '\\data'
result_destination = "E:\\HCS_results_1015"
# cluster evaluation
# typical_days_path = "E:\\WP2\\Typical_hours"
typical_hours_path = "E:\\WP2\\Typical_hours"


# osmose_project_path = "C:\\Users\\Zhongming\\Documents\\HCS_mk\\Projects\\"
# osmose_project_path = "E:\\ipese_new\\osmose_mk\\Projects"
# Branch master
# osmose_project_path = "E:\\OSMOSE_projects\\HCS\\Projects"
# osmose_outMsg_path = "\\scenario_1\\tmp\\OutMsg.txt"

## end ##


## WORK STATION ##
# ampl_lic_path = "C:\\Users\\Zhongming\\Desktop\\SH\\ampl"
# osmose_project_path = "C:\\Users\\Zhongming\\Documents\\HCS_mk\\Projects"
# osmose_project_data_path = osmose_project_path + '\\data'
# result_destination = "D:\\SH\\WP3_results"
# # cluster evaluation
# typical_hours_path = "D:\\SH\\WP3_results\\Typical_hours"
## end ##

# == HKG Summer ==
# season = 'Summer'
# cases = ['HKG_CBD_m_WP1_OFF', 'HKG_CBD_m_WP1_HOT', 'HKG_CBD_m_WP1_RET']
# specified_buildings = ["B001","B002","B003","B004","B005","B006","B007","B008","B009","B010"]
# osmose_project_path = "C:\\Users\\Zhongming\\Documents\\HCS\\Projects"
# result_destination = "D:\\SH\\Google Drive\\WP2\\HKG_Summer"
# ==============================================================================================

# == HKG Spring ==
# season = 'Spring'
# cases = ['HKG_CBD_m_WP1_OFF', 'HKG_CBD_m_WP1_HOT', 'HKG_CBD_m_WP1_RET']
# specified_buildings = ["B001","B002","B003","B004","B005","B006","B007","B008","B009","B010"]
# osmose_project_path = "C:\\Users\\Zhongming\\Documents\\HCS\\Projects"
# result_destination = "D:\\SH\\Google Drive\\WP2\\HKG_Spring"
# ==============================================================================================

# == HKG Autumn ==
# season = 'Autumn'
# cases = ['HKG_CBD_m_WP1_OFF', 'HKG_CBD_m_WP1_HOT', 'HKG_CBD_m_WP1_RET']
# specified_buildings = ["B001","B002","B003","B004","B005","B006","B007","B008","B009","B010"]
# osmose_project_path = "C:\\Users\\Zhongming\\Documents\\HCS\\Projects"
# result_destination = "D:\\SH\\Google Drive\\WP2\\HKG_Autumn"
# ==============================================================================================

# == ABU Summer ==
# season = 'Summer'
# cases = ['ABU_CBD_m_WP1_OFF','ABU_CBD_m_WP1_HOT','ABU_CBD_m_WP1_RET']
# specified_buildings = ["B001","B002","B003","B004","B005","B006","B007","B008","B009","B010"]
# osmose_project_path = "C:\\Users\\Zhongming\\Documents\\HCS\\Projects"
# result_destination = "D:\\SH\\Google Drive\\WP2\\ABU_Summer"
# ==============================================================================================

# == ABU Spring ==
# season = 'Spring'
# cases = ['ABU_CBD_m_WP1_OFF','ABU_CBD_m_WP1_HOT','ABU_CBD_m_WP1_RET']
# specified_buildings = ["B001","B002","B003","B004","B005","B006","B007","B008","B009","B010"]
# osmose_project_path = "C:\\Users\\Zhongming\\Documents\\HCS\\Projects"
# result_destination = "D:\\SH\\Google Drive\\WP2\\ABU_Spring"
# ==============================================================================================

# == ABU Autumn ==
# season = 'Autumn'
# cases = ['ABU_CBD_m_WP1_HOT']
# specified_buildings = ["B006","B002"]
# # cases = ['ABU_CBD_m_WP1_OFF','ABU_CBD_m_WP1_HOT','ABU_CBD_m_WP1_RET']
# # specified_buildings = ["B001","B002","B003","B004","B005","B006","B007","B008","B009","B010"]
# osmose_project_path = "C:\\Users\\Zhongming\\Documents\\HCS\\Projects"
# result_destination = "D:\\SH\\WP2\\ABU_Autumn"
# ==============================================================================================



