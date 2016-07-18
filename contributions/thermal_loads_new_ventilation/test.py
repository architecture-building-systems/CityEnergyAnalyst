from cea import globalvar, thermal_loads, demand
from cea import inputlocator
from cea.demand import demand, thermal_loads


def test_thermal_loads_new_ventilation():
    """
    script to test modified thermal loads calculation with new natural ventilation and improved mechanical ventilation
     simulation

    Returns
    -------

    """

    # create globalvars
    gv = globalvar.GlobalVariables()

    locator = inputlocator.InputLocator(scenario_path=r'C:\reference-case\baseline')
    # for the interface, the user should pick a file out of of those in ...DB/Weather/...
    weather_path = locator.get_default_weather()

    # plug in new thermal loads calculation
    gv.models['calc-thermal-loads'] = thermal_loads.calc_thermal_loads_new_ventilation

    # run demand
    demand.demand_calculation(locator=locator, weather_path=weather_path, gv=gv)
    print "test_thermal_loads_new_ventilation() succeeded"


if __name__ == '__main__':
    test_thermal_loads_new_ventilation()
