"""
Building model main function definitions
"""

from building_model.building import Building
from building_model.utils import *


def connect_database(data_path="../data/"):
    # Create database, if none
    if not os.path.isfile(data_path + "data.sqlite"):
        create_database(
            sqlite_path=data_path + "data.sqlite",
            sql_path=data_path + "data.sqlite.schema.sql",
            csv_path=data_path
        )

    conn = sqlite3.connect(data_path + "data.sqlite")
    return conn


def get_building_model(scenario_name="scenario_default", conn=connect_database()):
    building = Building(conn, scenario_name)
    return building


def example():
    """
    Example script
    """
    building = get_building_model()

    print("-----------------------------------------------------------------------------------------------------------")
    print('building.state_matrix=')
    print(building.state_matrix)
    print("-----------------------------------------------------------------------------------------------------------")
    print('building.control_matrix=')
    print(building.control_matrix)
    print("-----------------------------------------------------------------------------------------------------------")
    print('building.disturbance_matrix=')
    print(building.disturbance_matrix)
    print("-----------------------------------------------------------------------------------------------------------")
    print('building.state_output_matrix=')
    print(building.state_output_matrix)
    print("-----------------------------------------------------------------------------------------------------------")
    print('building.control_output_matrix=')
    print(building.control_output_matrix)
    print("-----------------------------------------------------------------------------------------------------------")
    print('building.disturbance_output_matrix=')
    print(building.disturbance_output_matrix)
    print("-----------------------------------------------------------------------------------------------------------")


if __name__ == "__main__":
    example()
