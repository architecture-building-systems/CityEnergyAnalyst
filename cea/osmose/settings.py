# import from config # TODO: add to config

## GENERAL ##
# TECHS = ['HCS_coil', 'HCS_ER0', 'HCS_3for2', 'HCS_LD', 'HCS_IEHX']
TECHS = ['HCS_coil']
timesteps = 168  # 168 (week)
PLOTS = ['electricity_usages','air_flow','OAU_T_w_supply','exergy_usages', 'humidity_balance', 'humidity_storage', 'heat_balance']
new_calculation = False

# GENERAL INPUTS
season = 'Autumn'
specified_buildings = ["B001"]
#specified_buildings = ["B001","B002","B003","B004","B005","B006","B007","B008","B009","B010"]
cases = ['ABU_CBD_m_WP1_HOT']

## LAPTOP ##
# ampl_lic_path = "C:\\Users\\Shanshan\\Desktop\\ampl"
# osmose_project_path = "D:\\SH\\HCS\\Projects"
# result_destination = "D:\\test_0805"

## WORK STATION ##
ampl_lic_path = "C:\\Users\\Zhongming\\Desktop\\SH\\ampl"
# osmose_project_path = "C:\\Users\\Zhongming\\Documents\\HCS\\Projects"
# result_destination = "D:\\SH\\test_0805"


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
season = 'Autumn'
cases = ['ABU_CBD_m_WP1_HOT']
specified_buildings = ["B006","B002"]
# cases = ['ABU_CBD_m_WP1_OFF','ABU_CBD_m_WP1_HOT','ABU_CBD_m_WP1_RET']
# specified_buildings = ["B001","B002","B003","B004","B005","B006","B007","B008","B009","B010"]
osmose_project_path = "C:\\Users\\Zhongming\\Documents\\HCS\\Projects"
result_destination = "D:\\SH\\WP2\\ABU_Autumn"
# ==============================================================================================



