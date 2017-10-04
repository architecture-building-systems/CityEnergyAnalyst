# -*- coding: utf-8 -*-
"""
Demand model of thermal loads
"""
from __future__ import division

import os

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as Gdf
from cea.utilities.dbfreader import dbf_to_dataframe

from cea.demand import occupancy_model, rc_model_crank_nicholson_procedure, ventilation_air_flows_simple
from cea.demand import ventilation_air_flows_detailed
from cea.demand import sensible_loads, electrical_loads, hotwater_loads, refrigeration_loads, datacenter_loads
from cea.technologies import controllers
from cea.utilities import helpers


# demand model of thermal and electrical loads

def calc_thermal_loads(building_name, bpr, weather_data, usage_schedules, date, gv, locator,
                       use_dynamic_infiltration_calculation=False):
    """
    Calculate thermal loads of a single building with mechanical or natural ventilation.
    Calculation procedure follows the methodology of ISO 13790

    The structure of ``usage_schedules`` is:

    .. code-block:: python
        :emphasize-lines: 3,5

        {
            'list_uses': ['ADMIN', 'GYM', ...],
            'schedules': [ ([...], [...], [...], [...]), (), (), () ]
        }

    * each element of the 'list_uses' entry represents a building occupancy type.
    * each element of the 'schedules' entry represents the schedules for a building occupancy type.
    * the schedules for a building occupancy type are a 4-tuple (occupancy, electricity, domestic hot water,
      probability of use), with each element of the 4-tuple being a list of hourly values (8760 values).


    Side effect include a number of files in two folders:

    * ``scenario/outputs/data/demand``

      * ``${Name}.csv`` for each building

    * temporary folder (as returned by ``tempfile.gettempdir()``)

      * ``${Name}T.csv`` for each building

    daren-thomas: as far as I can tell, these are the only side-effects.

    :param building_name: name of building
    :type building_name: str

    :param bpr: a collection of building properties for the building used for thermal loads calculation
    :type bpr: BuildingPropertiesRow

    :param weather_data: data from the .epw weather file. Each row represents an hour of the year. The columns are:
        ``drybulb_C``, ``relhum_percent``, and ``windspd_ms``
    :type weather_data: pandas.DataFrame

    :param usage_schedules: dict containing schedules and function names of buildings.
    :type usage_schedules: dict

    :param date: the dates (hours) of the year (8760)
    :type date: pandas.tseries.index.DatetimeIndex

    :param gv: global variables / context
    :type gv: GlobalVariables

    :returns: This function does not return anything
    :rtype: NoneType
"""
    tsd = initialize_timestep_data(bpr, weather_data)

    # get schedules
    list_uses = usage_schedules['list_uses']
    archetype_schedules = usage_schedules['archetype_schedules']
    archetype_values = usage_schedules['archetype_values']
    schedules = occupancy_model.calc_schedules(list_uses, archetype_schedules, bpr.occupancy, archetype_values)

    # calculate occupancy schedule and occupant-related parameters
    tsd['people'] = schedules['people'] * bpr.rc_model['Af']
    tsd['ve'] = schedules['ve'] * (bpr.comfort['Ve_lps'] * 3.6) * bpr.rc_model['Af']  # in m3/h
    tsd['Qs'] = schedules['Qs'] * bpr.internal_loads['Qs_Wp'] * bpr.rc_model['Af']  # in W

    # get electrical loads (no auxiliary loads)
    tsd = electrical_loads.calc_Eint(tsd, bpr, schedules)

    # get refrigeration loads
    tsd['Qcref'], tsd['mcpref'], \
    tsd['Tcref_re'], tsd['Tcref_sup'] = np.vectorize(refrigeration_loads.calc_Qcref)(tsd['Eref'])

    # get server loads
    tsd['Qcdataf'], tsd['mcpdataf'], \
    tsd['Tcdataf_re'], tsd['Tcdataf_sup'] = np.vectorize(datacenter_loads.calc_Qcdataf)(tsd['Edataf'])

    # ground water temperature in C during heating season (winter) according to norm
    tsd['Twwf_re'][:] = bpr.building_systems['Tww_re_0']

    # ground water temperature in C during non-heating season (summer) according to norm  -  FIXME: which norm?
    tsd['Twwf_re'][gv.seasonhours[0] + 1:gv.seasonhours[1] - 1] = 14

    if bpr.rc_model['Af'] > 0:  # building has conditioned area

        ventilation_air_flows_simple.calc_m_ve_required(bpr, tsd)
        ventilation_air_flows_simple.calc_m_ve_leakage_simple(bpr, tsd, gv)

        # get internal comfort properties
        tsd = controllers.calc_simple_temp_control(tsd, bpr.comfort, gv.seasonhours[0] + 1, gv.seasonhours[1],
                                                   date.dayofweek)

        # # latent heat gains
        tsd['w_int'] = sensible_loads.calc_Qgain_lat(schedules, bpr.internal_loads['X_ghp'], bpr.rc_model['Af'],
                                                     bpr.hvac['type_cs'], bpr.hvac['type_hs'])

        # end-use demand calculation
        for t in range(-720, 8760):
            hoy = helpers.seasonhour_2_hoy(t, gv)

            # heat flows in [W]
            # sensible heat gains
            tsd = sensible_loads.calc_Qgain_sen(hoy, tsd, bpr, gv)

            if use_dynamic_infiltration_calculation:
                # OVERWRITE STATIC INFILTRATION WITH DYNAMIC INFILTRATION RATE
                dict_props_nat_vent = ventilation_air_flows_detailed.get_properties_natural_ventilation(bpr, gv)
                qm_sum_in, qm_sum_out = ventilation_air_flows_detailed.calc_air_flows(
                    tsd['theta_a'][hoy - 1] if not np.isnan(tsd['theta_a'][hoy - 1]) else tsd['T_ext'][hoy - 1],
                    tsd['u_wind'][hoy], tsd['T_ext'][hoy], dict_props_nat_vent)
                # INFILTRATION IS FORCED NOT TO REACH ZERO IN ORDER TO AVOID THE RC MODEL TO FAIL
                tsd['m_ve_inf'][hoy] = max(qm_sum_in / 3600, 1 / 3600)

            # ventilation air flows [kg/s]
            ventilation_air_flows_simple.calc_air_mass_flow_mechanical_ventilation(bpr, tsd, hoy)
            ventilation_air_flows_simple.calc_air_mass_flow_window_ventilation(bpr, tsd, hoy)

            # ventilation air temperature
            ventilation_air_flows_simple.calc_theta_ve_mech(bpr, tsd, hoy, gv)

            # heating / cooling demand of building
            rc_model_crank_nicholson_procedure.calc_rc_model_demand_heating_cooling(bpr, tsd, hoy, gv)

            # END OF FOR LOOP

        # add emission losses to heating / cooling demand
        tsd['Qhs_sen_incl_em_ls'] = tsd['Qhs_sen_sys'] + tsd['Qhs_em_ls']
        tsd['Qcs_sen_incl_em_ls'] = tsd['Qcs_sen_sys'] + tsd['Qcs_em_ls']

        # Calc of Qhs_dis_ls/Qcs_dis_ls - losses due to distribution of heating/cooling coils
        Qhs_d_ls, Qcs_d_ls = np.vectorize(sensible_loads.calc_Qhs_Qcs_dis_ls)(tsd['theta_a'], tsd['T_ext'],
                                                                              tsd['Qhs_sen_incl_em_ls'],
                                                                              tsd['Qcs_sen_incl_em_ls'],
                                                                              bpr.building_systems['Ths_sup_0'],
                                                                              bpr.building_systems['Ths_re_0'],
                                                                              bpr.building_systems['Tcs_sup_0'],
                                                                              bpr.building_systems['Tcs_re_0'],
                                                                              np.nanmax(tsd['Qhs_sen_incl_em_ls']),
                                                                              np.nanmin(tsd['Qcs_sen_incl_em_ls']),
                                                                              gv.D, bpr.building_systems['Y'][0],
                                                                              bpr.hvac['type_hs'],
                                                                              bpr.hvac['type_cs'], gv.Bf,
                                                                              bpr.building_systems['Lv'])

        tsd['Qcsf_lat'] = tsd['Qcs_lat_sys']
        tsd['Qhsf_lat'] = tsd['Qhs_lat_sys']

        # Calc requirements of generation systems (both cooling and heating do not have a storage):
        tsd['Qhs'] = tsd['Qhs_sen_sys']
        tsd['Qhsf'] = tsd['Qhs'] + tsd['Qhs_em_ls'] + Qhs_d_ls  # no latent is considered because it is already added a
        # s electricity from the adiabatic system.
        tsd['Qcs'] = tsd['Qcs_sen_sys'] + tsd['Qcsf_lat']
        tsd['Qcsf'] = tsd['Qcs'] + tsd['Qcs_em_ls'] + Qcs_d_ls
        # Calc nominal temperatures of systems
        Qhsf_0 = np.nanmax(tsd['Qhsf'])  # in W
        Qcsf_0 = np.nanmin(tsd['Qcsf'])  # in W in negative

        # Cal temperatures of all systems
        tsd['Tcsf_re'], tsd['Tcsf_sup'], tsd['Thsf_re'], \
        tsd['Thsf_sup'], tsd['mcpcsf'], tsd['mcphsf'] = sensible_loads.calc_temperatures_emission_systems(tsd, bpr,
                                                                                                          Qcsf_0,
                                                                                                          Qhsf_0,
                                                                                                          gv)

        # calc hot water load
        Mww, tsd['Qww'], Qww_ls_st, tsd['Qwwf'], Qwwf_0, Tww_st, Vww, Vw, tsd['mcpwwf'] = hotwater_loads.calc_Qwwf(
            bpr.building_systems['Lcww_dis'], bpr.building_systems['Lsww_dis'], bpr.building_systems['Lvww_c'],
            bpr.building_systems['Lvww_dis'], tsd['T_ext'], tsd['theta_a'], tsd['Twwf_re'],
            bpr.building_systems['Tww_sup_0'], bpr.building_systems['Y'], gv, schedules,
            bpr)

        # calc auxiliary loads
        tsd['Eauxf'], tsd['Eauxf_hs'], tsd['Eauxf_cs'], \
        tsd['Eauxf_ve'], tsd['Eauxf_ww'], tsd['Eauxf_fw'] = electrical_loads.calc_Eauxf(bpr.geometry['Blength'],
                                                                                        bpr.geometry['Bwidth'],
                                                                                        Mww, tsd['Qcsf'], Qcsf_0,
                                                                                        tsd['Qhsf'], Qhsf_0,
                                                                                        tsd['Qww'],
                                                                                        tsd['Qwwf'], Qwwf_0,
                                                                                        tsd['Tcsf_re'],
                                                                                        tsd['Tcsf_sup'],
                                                                                        tsd['Thsf_re'],
                                                                                        tsd['Thsf_sup'],
                                                                                        Vw,
                                                                                        bpr.age['built'],
                                                                                        bpr.building_systems[
                                                                                            'fforma'],
                                                                                        gv,
                                                                                        bpr.geometry['floors_ag'],
                                                                                        bpr.occupancy['PFloor'],
                                                                                        bpr.hvac['type_cs'],
                                                                                        bpr.hvac['type_hs'],
                                                                                        tsd['Ehs_lat_aux'],
                                                                                        tsd)

    elif bpr.rc_model['Af'] == 0:  # if building does not have conditioned area

        tsd = update_timestep_data_no_conditioned_area(tsd)

    else:
        raise

    tsd['Qhprof'][:] = schedules['Qhpro'] * bpr.internal_loads['Qhpro_Wm2'] * bpr.rc_model['Af']  # in kWh

    # calculate other quantities
    tsd['Qcsf_lat'] = abs(tsd['Qcsf_lat'])
    tsd['Qcsf'] = abs(tsd['Qcsf'])
    tsd['Qcs'] = abs(tsd['Qcs'])
    tsd['people'] = np.floor(tsd['people'])
    tsd['QHf'] = tsd['Qhsf'] + tsd['Qwwf'] + tsd['Qhprof']
    tsd['QCf'] = tsd['Qcsf'] + tsd['Qcdataf'] + tsd['Qcref']
    tsd['Ef'] = tsd['Ealf'] + tsd['Edataf'] + tsd['Eprof'] + tsd['Ecaf'] + tsd['Eauxf'] + tsd['Eref']
    tsd['QEf'] = tsd['QHf'] + tsd['QCf'] + tsd['Ef']

    # write results to csv
    gv.demand_writer.results_to_csv(tsd, bpr, locator, date, building_name)
    # write report
    gv.report(tsd, locator.get_demand_results_folder(), building_name)

    return


def initialize_timestep_data(bpr, weather_data):
    """
    initializes the time step data with the weather data and the minimum set of variables needed for computation.
    :param bpr:
    :param weather_data:
    :return: returns the `tsd` variable, a dictionary of time step data mapping variable names to ndarrays for each
    hour of the year.
    """
    # Initialize dict with weather variables
    tsd = {'Twwf_sup': bpr.building_systems['Tww_sup_0'],
           'T_ext': weather_data.drybulb_C.values,
           'rh_ext': weather_data.relhum_percent.values,
           'T_sky': weather_data.skytemp_C.values,
           'u_wind': weather_data.windspd_ms}
    # fill data with nan values
    nan_fields = ['Qhs_lat_sys', 'Qhs_sen_sys', 'Qcs_lat_sys', 'Qcs_sen_sys', 'theta_a', 'theta_m', 'theta_c',
                  'theta_o', 'Qhs_sen', 'Qcs_sen', 'Ehs_lat_aux', 'Qhs_em_ls', 'Qcs_em_ls', 'ma_sup_hs', 'ma_sup_cs',
                  'Ta_sup_hs', 'Ta_sup_cs', 'Ta_re_hs', 'Ta_re_cs', 'I_sol', 'w_int', 'I_rad', 'QEf', 'QHf', 'QCf',
                  'Ef', 'Qhsf', 'Qhs', 'Qhsf_lat',
                  'Qwwf', 'Qww', 'Qcsf', 'Qcs', 'Qcsf_lat', 'Qhprof', 'Eauxf', 'Eauxf_ve', 'Eauxf_hs', 'Eauxf_cs',
                  'Eauxf_ww', 'Eauxf_fw', 'mcphsf', 'mcpcsf', 'mcpwwf', 'Twwf_re', 'Thsf_sup', 'Thsf_re', 'Tcsf_sup',
                  'Tcsf_re', 'Tcdataf_re', 'Tcdataf_sup', 'Tcref_re', 'Tcref_sup', 'theta_ve_mech', 'm_ve_window',
                  'm_ve_mech', 'm_ve_recirculation', 'm_ve_inf']
    tsd.update(dict((x, np.zeros(8760) * np.nan) for x in nan_fields))

    # initialize system status log
    tsd['system_status'] = np.chararray(8760, itemsize=20)
    tsd['system_status'][:] = 'unknown'

    # TODO: add detailed infiltration air flows
    # tsd['qm_sum_in'] = np.zeros(8760) * np.nan
    # tsd['qm_sum_out'] = np.zeros(8760) * np.nan

    return tsd


def update_timestep_data_no_conditioned_area(tsd):
    """
    Update time step data with zeros for buildings without conditioned area

    Author: Gabriel Happle
    Date: 01/2017

    :param tsd: time series data dict
    :return: update tsd
    """

    zero_fields = ['Qhs_lat_sys', 'Qhs_sen_sys', 'Qcs_lat_sys', 'Qcs_sen_sys', 'Qhs_sen', 'Qcs_sen', 'Ehs_lat_aux',
                   'Qhs_em_ls', 'Qcs_em_ls', 'ma_sup_hs', 'ma_sup_cs', 'Ta_sup_hs', 'Ta_sup_cs', 'Ta_re_hs', 'Ta_re_cs',
                   'Qhsf', 'Qhs', 'Qhsf_lat', 'Qcsf', 'Qcs', 'Qcsf_lat', 'Qcsf', 'Qcs', 'Qhsf', 'Qhs', 'Eauxf',
                   'Eauxf_hs', 'Eauxf_cs', 'Eauxf_ve', 'Eauxf_ww', 'Eauxf_fw', 'mcphsf', 'mcpcsf', 'mcpwwf', 'mcpdataf',
                   'mcpref', 'Twwf_sup', 'Twwf_re', 'Thsf_sup', 'Thsf_re', 'Tcsf_sup', 'Tcsf_re', 'Tcdataf_re',
                   'Tcdataf_sup', 'Tcref_re', 'Tcref_sup', 'Qwwf', 'Qww']

    tsd.update(dict((x, np.zeros(8760)) for x in zero_fields))

    return tsd


class BuildingProperties(object):
    """
    Groups building properties used for the calc-thermal-loads functions. Stores the full DataFrame for each of the
    building properties and provides methods for indexing them by name.

    G. Happle   BuildingPropsThermalLoads   27.05.2016
    """

    def __init__(self, locator, gv):
        """
        Read building properties from input shape files and construct a new BuildingProperties object.

        :param locator: an InputLocator for locating the input files
        :type locator: cea.inputlocator.InputLocator

        :param gv: contains the context (constants and models) for the calculation
        :type gv: cea.globalvar.GlobalVariables

        :returns: object of type BuildingProperties
        :rtype: BuildingProperties

        - get_radiation: C:\reference-case\baseline\outputs\data\solar-radiation\radiation.csv
        - get_surface_properties: C:\reference-case\baseline\outputs\data\solar-radiation\properties_surfaces.csv
        - get_zone_geometry: C:\reference-case\baseline\inputs\building-geometry\zone.shp
        - get_building_hvac: C:\reference-case\baseline\inputs\building-properties\technical_systems.shp
        - get_building_thermal: C:\reference-case\baseline\inputs\building-properties\thermal_properties.shp
        - get_building_occupancy: C:\reference-case\baseline\inputs\building-properties\occupancy.shp
        - get_building_architecture: C:\reference-case\baseline\inputs\building-properties\architecture.shp
        - get_building_age: C:\reference-case\baseline\inputs\building-properties\age.shp
        - get_building_comfort: C:\reference-case\baseline\inputs\building-properties\indoor_comfort.shp
        - get_building_internal: C:\reference-case\baseline\inputs\building-properties\internal_loads.shp
        """

        from cea.geometry import geometry_reader
        self.gv = gv
        gv.log("read input files")
        surface_properties = pd.read_csv(locator.get_surface_properties())
        prop_geometry = Gdf.from_file(locator.get_zone_geometry())
        prop_geometry['footprint'] = prop_geometry.area
        prop_geometry['perimeter'] = prop_geometry.length
        prop_geometry['Blength'], prop_geometry['Bwidth'] = self.calc_bounding_box_geom(locator.get_zone_geometry())
        prop_geometry = prop_geometry.drop('geometry', axis=1).set_index('Name')
        prop_hvac = dbf_to_dataframe(locator.get_building_hvac())
        prop_occupancy_df = dbf_to_dataframe(locator.get_building_occupancy()).set_index('Name')
        prop_occupancy_df.fillna(value=0.0, inplace=True)  # fix badly formatted occupancy file...
        prop_occupancy = prop_occupancy_df.loc[:, (prop_occupancy_df != 0).any(axis=0)]
        prop_architectures = dbf_to_dataframe(locator.get_building_architecture())
        prop_age = dbf_to_dataframe(locator.get_building_age()).set_index('Name')
        prop_comfort = dbf_to_dataframe(locator.get_building_comfort()).set_index('Name')
        prop_internal_loads = dbf_to_dataframe(locator.get_building_internal()).set_index('Name')

        # get solar properties
        solar = get_prop_solar(locator).set_index('Name')

        # get temperatures of operation
        prop_HVAC_result = get_properties_technical_systems(locator, prop_hvac).set_index('Name')

        # get envelope properties
        prop_envelope = get_envelope_properties(locator, prop_architectures).set_index('Name')

        # apply overrides
        if os.path.exists(locator.get_building_overrides()):
            self._overrides = pd.read_csv(locator.get_building_overrides()).set_index('Name')
            prop_envelope = self.apply_overrides(prop_envelope)
            prop_internal_loads = self.apply_overrides(prop_internal_loads)
            prop_comfort = self.apply_overrides(prop_comfort)

        # get properties of rc demand model
        prop_rc_model = self.calc_prop_rc_model(prop_occupancy, prop_envelope,
                                                prop_geometry, prop_HVAC_result, surface_properties,
                                                gv)

        # df_windows = geometry_reader.create_windows(surface_properties, prop_envelope)
        # TODO: to check if the Win_op and height of window is necessary.
        # TODO: maybe mergin branch i9 with CItyGML could help with this
        gv.log("done")

        # save resulting data
        self._prop_surface = surface_properties
        self._prop_geometry = prop_geometry
        self._prop_envelope = prop_envelope
        self._prop_occupancy = prop_occupancy
        self._prop_HVAC_result = prop_HVAC_result
        self._prop_comfort = prop_comfort
        self._prop_internal_loads = prop_internal_loads
        self._prop_age = prop_age
        self._solar = solar
        self._prop_RC_model = prop_rc_model

    def calc_bounding_box_geom(self, geometry_shapefile):
        import shapefile
        sf = shapefile.Reader(geometry_shapefile)
        shapes = sf.shapes()
        len_shapes = len(shapes)
        bwidth = []
        blength = []
        for shape in range(len_shapes):
            bbox = shapes[shape].bbox
            coords_bbox = [coord for coord in bbox]
            delta1 = abs(coords_bbox[0] - coords_bbox[2])
            delta2 = abs(coords_bbox[1] - coords_bbox[3])
            if delta1 >= delta2:
                bwidth.append(delta2)
                blength.append(delta1)
            else:
                bwidth.append(delta1)
                blength.append(delta2)

        return blength, bwidth

    def apply_overrides(self, df):
        """Apply the overrides to `df`. This works by checking each column in the `self._overrides` dataframe
        and overwriting any columns in `df` with the same name.
        `self._overrides` and `df` are assumed to have the same index.
        """
        shared_columns = set(self._overrides.columns) & set(df.columns)
        for column in shared_columns:
            df[column] = self._overrides[column]
        return df

    def __len__(self):
        return len(self.list_building_names())

    def list_building_names(self):
        """get list of all building names"""
        return self._prop_RC_model.index

    def list_uses(self):
        """get list of all uses (occupancy types)"""
        return list(self._prop_occupancy.drop('PFloor', axis=1).columns)

    def get_prop_geometry(self, name_building):
        """get geometry of a building by name"""
        return self._prop_geometry.ix[name_building].to_dict()

    def get_prop_envelope(self, name_building):
        """get the architecture and thermal properties of a building by name"""
        return self._prop_envelope.ix[name_building].to_dict()

    def get_prop_occupancy(self, name_building):
        """get the occupancy properties of a building by name"""
        return self._prop_occupancy.ix[name_building].to_dict()

    def get_prop_hvac(self, name_building):
        """get HVAC properties of a building by name"""
        return self._prop_HVAC_result.ix[name_building].to_dict()

    def get_prop_rc_model(self, name_building):
        """get RC-model properties of a building by name"""
        return self._prop_RC_model.ix[name_building].to_dict()

    def get_prop_comfort(self, name_building):
        """get comfort properties of a building by name"""
        return self._prop_comfort.ix[name_building].to_dict()

    def get_prop_internal_loads(self, name_building):
        """get internal loads properties of a building by name"""
        return self._prop_internal_loads.ix[name_building].to_dict()

    def get_prop_age(self, name_building):
        """get age properties of a building by name"""
        return self._prop_age.ix[name_building].to_dict()

    def get_solar(self, name_building):
        """get solar properties of a building by name"""
        return self._solar.ix[name_building]

    def get_prop_windows(self, name_building):
        """get windows and their properties of a building by name"""
        return self._prop_windows.loc[self._prop_windows['name_building'] == name_building].to_dict('list')

    def calc_prop_rc_model(self, occupancy, envelope, geometry, hvac_temperatures,
                           surface_properties,
                           gv):
        """
        Return the RC model properties for all buildings. The RC model used is described in ISO 13790:2008, Annex C (Full
        set of equations for simple hourly method).

        :param occupancy: The contents of the `occupancy.shp` file, indexed by building name. Each column is the name of an
            occupancy type (GYM, HOSPITAL, HOTEL, INDUSTRIAL, MULTI_RES, OFFICE, PARKING, etc.) except for the
            "PFloor" column which is a fraction of heated floor area.
            The occupancy types must add up to 1.0.
        :type occupancy: Gdf

        :param envelope: The contents of the `architecture.shp` file, indexed by building name. It contains the
            following fields: n50, type_shade, win_op, win_wall. Only `win_wall` (window to wall ratio) is
            used. Hs, U_base, U_roof, U_wall, U_win, Cm_Af.
            - Hs: fraction of gross floor area that is heated/cooled {0 <= Hs <= 1}
            - Cm_Af: iternal heat capacity per unit of area J/K.m2
        :type envelope: Gdf

        :type thermal_properties: Gdf

        :param geometry: The contents of the `zone.shp` file indexed by building name - the list of buildings, their floor
            counts, heights etc.
            Includes additional fields "footprint" and "perimeter" as calculated in `read_building_properties`.
        :type geometry: Gdf

        :param hvac_temperatures: The return value of `get_properties_technical_systems`.
        :type hvac_temperatures: DataFrame

        :param surface_properties: The contents of the `properties_surfaces.csv` file generated by the radiation script.
            It contains the fields Name, Freeheight, FactorShade, height_ag and Shape_Leng.
            This data is used to calculate the wall and window areas
        :type surface_properties: DataFrame

        :param gv: An instance of the GlobalVariables context.
        :type gv: GlobalVariables

        :returns: RC model properties per building
        :rtype: DataFrame

        Sample result data:
        Awall_all    1.131753e+03   (total wall surface exposed to outside conditions in [m2])
        Atot         4.564827e+03   (total area of the building envelope in [m2], the roof is considered to be flat)
        Aw           4.527014e+02   (area of windows in [m2])
        Am           6.947967e+03   (effective mass area in [m2])
        Aef          2.171240e+03   (floor area with electricity in [m2])
        Af           2.171240e+03   (conditioned floor area (heated/cooled) in [m2])
        Cm           6.513719e+08   (internal heat capacity in [J/K])
        Htr_is       1.574865e+04   (thermal transmission coefficient between air and surface nodes in RC-model in [W/K])
        Htr_em       5.829963e+02   (thermal transmission coefficient between exterior and thermal mass nodes in RC-model in [W/K])
        Htr_ms       6.322650e+04   (thermal transmission coefficient between surface and thermal mass nodes in RC-model in [W/K])
        Htr_op       5.776698e+02   (thermal transmission coefficient for opaque surfaces in [W/K])
        Hg           2.857637e+02   (steady-state thermal transmission coefficient to the ground in [W/K])
        HD           2.919060e+02   (direct thermal transmission coefficient to the external environment in [W/K])
        Htr_w        1.403374e+03   (thermal transmission coefficient for windows and glazing in [W/K])
        GFA_m2       2.412489e+03   (gross floor area [m2])
        Name: B153767, dtype: float64

        FIXME: finish documenting the result data...
        FIXME: rename Awall_all to something more sane...
        """

        # Areas above ground
        # get the area of each wall in the buildings
        surface_properties['Awall'] = (surface_properties['Shape_Leng'] * surface_properties['Freeheight'] *
                                       surface_properties['FactorShade'])
        df = pd.DataFrame({'Name': surface_properties['Name'],
                           'Awall_all': surface_properties['Awall']}).groupby(by='Name').sum()

        df = df.merge(envelope, left_index=True, right_index=True).merge(occupancy, left_index=True,
                                                                         right_index=True)

        # area of windows
        # TODO: wwe_south replaces wil_wall this is temporary it should not be need it anymore with the new geometry files of Daysim
        df['Aw'] = df['Awall_all'] * df['wwr_south'] * df['PFloor']

        # opaque areas (PFloor represents a factor according to the amount of floors heated)
        df['Aop_sup'] = df['Awall_all'] * df['PFloor'] - df['Aw']

        # Areas below ground
        df = df.merge(geometry, left_index=True, right_index=True)
        df = df.merge(hvac_temperatures, left_index=True, right_index=True)
        df['floors'] = df['floors_bg'] + df['floors_ag']

        # opague areas in [m2] below ground including floor
        df['Aop_bel'] = df['height_bg'] * df['perimeter'] + df['footprint']

        # total area of the building envelope in [m2], the roof is considered to be flat
        df['Aroof'] = df['footprint']
        df['Atot'] = df[['Aw', 'Aop_sup', 'footprint', 'Aop_bel']].sum(axis=1) + (df['Aroof'] * (df['floors'] - 1))

        df['GFA_m2'] = df['footprint'] * df['floors']  # gross floor area

        for building in df.index.values:
            if hvac_temperatures.loc[building, 'type_hs'] == 'T0' and \
                            hvac_temperatures.loc[building, 'type_cs'] == 'T0' and df.loc[building, 'Hs'] > 0:
                df.loc[building, 'Hs'] = 0
                print 'Building %s has no heating and cooling system, Hs corrected to 0.' % building
        df['Af'] = df['GFA_m2'] * df['Hs']  # conditioned area - areas not heated/cooled
        df['Aef'] = df['GFA_m2'] * gv.Es  # conditioned area only those for electricity

        if 'Cm' in self.get_overrides_columns():
            # Internal heat capacity is not part of input, calculate [J/K]
            df['Cm'] = self._overrides['Cm_Af'] * df['Af']
        else:
            df['Cm'] = df['Cm_Af'] * df['Af']

        df['Am'] = df['Cm_Af'].apply(self.lookup_effective_mass_area_factor) * df['Af']  # Effective mass area in [m2]

        # Steady-state Thermal transmittance coefficients and Internal heat Capacity
        df['Htr_w'] = df['Aw'] * df['U_win']  # Thermal transmission coefficient for windows and glazing in [W/K]

        # direct thermal transmission coefficient to the external environment in [W/K]
        df['HD'] = df['Aop_sup'] * df['U_wall'] + df['footprint'] * df['U_roof']

        df['Hg'] = gv.Bf * df['Aop_bel'] * df[
            'U_base']  # steady-state Thermal transmission coefficient to the ground. in W/K
        df['Htr_op'] = df['Hg'] + df['HD']
        df['Htr_ms'] = gv.hms * df['Am']  # Coupling conductance 1 in W/K
        df['Htr_em'] = 1 / (1 / df['Htr_op'] - 1 / df['Htr_ms'])  # Coupling conductance 2 in W/K
        df['Htr_is'] = gv.his * df['Atot']

        fields = ['Awall_all', 'Atot', 'Aw', 'Am', 'Aef', 'Af', 'Cm', 'Htr_is', 'Htr_em', 'Htr_ms', 'Htr_op', 'Hg',
                  'HD', 'Aroof', 'U_wall', 'U_roof', 'U_win', 'Htr_w', 'GFA_m2']
        result = df[fields]
        return result

    def lookup_effective_mass_area_factor(self, cm):
        """
        Look up the factor to multiply the conditioned floor area by to get the effective mass area by building construction
        type. This is used for the calculation of the effective mass area "Am" in `get_prop_RC_model`.
        Standard values can be found in the Annex G of ISO EN13790

        :param Cm_Af: The internal heat capacity per unit of area.
        :return: effective mass area factor
        """
        if cm == 0:
            return 0
        elif 0 < cm <= 165000.0:
            return 2.5
        else:
            return 3.2

    def __getitem__(self, building_name):
        """return a (read-only) BuildingPropertiesRow for the building"""
        return BuildingPropertiesRow(geometry=self.get_prop_geometry(building_name),
                                     envelope=self.get_prop_envelope(building_name),
                                     occupancy=self.get_prop_occupancy(building_name),
                                     hvac=self.get_prop_hvac(building_name),
                                     rc_model=self.get_prop_rc_model(building_name),
                                     comfort=self.get_prop_comfort(building_name),
                                     internal_loads=self.get_prop_internal_loads(building_name),
                                     age=self.get_prop_age(building_name),
                                     solar=self.get_solar(building_name), gv=self.gv)

    def get_overrides_columns(self):
        """Return the list of column names in the `overrides.csv` file or an empty list if no such file
        is present."""
        if hasattr(self, '_overrides'):
            return list(self._overrides.columns)
        return []


class BuildingPropertiesRow(object):
    """Encapsulate the data of a single row in the DataSets of BuildingProperties. This class meant to be
    read-only."""

    def __init__(self, geometry, envelope, occupancy, hvac,
                 rc_model, comfort, internal_loads, age, solar, gv):
        """Create a new instance of BuildingPropertiesRow - meant to be called by BuildingProperties[building_name].
        Each of the arguments is a pandas Series object representing a row in the corresponding DataFrame."""
        self.geometry = geometry
        self.architecture = EnvelopeProperties(envelope)
        self.occupancy = occupancy  # FIXME: rename to uses!
        self.hvac = hvac
        self.rc_model = rc_model
        self.comfort = comfort
        self.internal_loads = internal_loads
        self.age = age
        self.solar = SolarProperties(solar)
        self.building_systems = self._get_properties_building_systems(gv)

    def _get_properties_building_systems(self, gv):
        # TODO: Documentation
        # Refactored from CalcThermalLoads

        # gemoetry properties.

        Ll = self.geometry['Blength']
        Lw = self.geometry['Bwidth']
        nf_ag = self.geometry['floors_ag']
        nf_bg = self.geometry['floors_bg']
        nfp = self.occupancy['PFloor']
        phi_pipes = self._calculate_pipe_transmittance_values()

        # nominal temperatures
        Ths_sup_0 = float(self.hvac['Tshs0_C'])
        Ths_re_0 = float(Ths_sup_0 - self.hvac['dThs0_C'])
        Tcs_sup_0 = self.hvac['Tscs0_C']
        Tcs_re_0 = Tcs_sup_0 + self.hvac['dTcs0_C']
        Tww_sup_0 = self.hvac['Tsww0_C']
        Tww_re_0 = Tww_sup_0 - self.hvac[
            'dTww0_C']  # Ground water temperature in heating(winter) season, according to norm #TODO: check norm
        # Identification of equivalent lenghts
        fforma = self._calc_form()  # factor form comparison real surface and rectangular
        Lv = (2 * Ll + 0.0325 * Ll * Lw + 6) * fforma  # length vertical lines
        if nf_ag < 2 and nf_bg < 2:  # it is assumed that building with less than a floor and less than 2 floors udnerground do not have
            Lcww_dis = 0
            Lvww_c = 0
        else:
            Lcww_dis = 2 * (Ll + 2.5 + nf_ag * nfp * gv.hf) * fforma  # length hot water piping circulation circuit
            Lvww_c = (2 * Ll + 0.0125 * Ll * Lw) * fforma  # length piping heating system circulation circuit

        Lsww_dis = 0.038 * Ll * Lw * nf_ag * nfp * gv.hf * fforma  # length hot water piping distribution circuit
        Lvww_dis = (Ll + 0.0625 * Ll * Lw) * fforma  # length piping heating system distribution circuit

        building_systems = pd.Series({'Lcww_dis': Lcww_dis,
                                      'Lsww_dis': Lsww_dis,
                                      'Lv': Lv,
                                      'Lvww_c': Lvww_c,
                                      'Lvww_dis': Lvww_dis,
                                      'Tcs_re_0': Tcs_re_0,
                                      'Tcs_sup_0': Tcs_sup_0,
                                      'Ths_re_0': Ths_re_0,
                                      'Ths_sup_0': Ths_sup_0,
                                      'Tww_re_0': Tww_re_0,
                                      'Tww_sup_0': Tww_sup_0,
                                      'Y': phi_pipes,
                                      'fforma': fforma})
        return building_systems

    def _calculate_pipe_transmittance_values(self):
        """linear trasmissivity coefficients of piping W/(m.K)"""
        if self.age['built'] >= 1995 or self.age['HVAC'] > 1995:
            phi_pipes = [0.2, 0.3, 0.3]
        # elif 1985 <= self.age['built'] < 1995 and self.age['HVAC'] == 0:
        elif 1985 <= self.age['built'] < 1995:
            phi_pipes = [0.3, 0.4, 0.4]
            if self.age['HVAC'] == self.age['built']:
                print 'Incorrect HVAC renovation year: if HVAC has not been renovated, the year should be set to 0'
        else:
            phi_pipes = [0.4, 0.4, 0.4]
        return phi_pipes

    def _calc_form(self):
        factor = self.geometry['footprint'] / (self.geometry['Bwidth'] * self.geometry['Blength'])
        return factor


class EnvelopeProperties(object):
    """Encapsulate a single row of the architecture input file for a building"""
    __slots__ = [u'a_roof', u'f_cros', u'n50', u'win_op', u'win_wall',
                 u'a_wall', u'rf_sh', u'e_wall', u'e_roof', u'G_win', u'e_win',
                 u'U_roof', u'Hs', u'Cm_Af', u'U_wall', u'U_base', u'U_win']

    def __init__(self, envelope):
        self.a_roof = envelope['a_roof']
        self.n50 = envelope['n50']
        self.win_wall = envelope['wwr_south']
        self.a_wall = envelope['a_wall']
        self.rf_sh = envelope['rf_sh']
        self.e_wall = envelope['e_wall']
        self.e_roof = envelope['e_roof']
        self.G_win = envelope['G_win']
        self.e_win = envelope['e_win']
        self.U_roof = envelope['U_roof']
        self.Hs = envelope['Hs']
        self.Cm_Af = envelope['Cm_Af']
        self.U_wall = envelope['U_wall']
        self.U_base = envelope['U_base']
        self.U_win = envelope['U_win']


class SolarProperties(object):
    """Encapsulates the solar properties of a building"""
    __slots__ = ['I_roof', 'I_wall', 'I_win']

    def __init__(self, solar):
        self.I_roof = solar['I_roof']
        self.I_wall = solar['I_wall']
        self.I_win = solar['I_win']


def get_properties_technical_systems(locator, prop_HVAC):
    """
    Return temperature data per building based on the HVAC systems of the building. Uses the `emission_systems.xls`
    file to look up properties

    :param locator:
    :type locator: cea.inputlocator.InputLocator

    :param prop_HVAC: HVAC properties for each building (type of cooling system, control system, domestic hot water
                      system and heating system.
                      The values can be looked up in the contributors manual:
                      https://architecture-building-systems.gitbooks.io/cea-toolbox-for-arcgis-manual/content/building_properties.html#mechanical-systems
    :type prop_HVAC: geopandas.GeoDataFrame
        Sample data (first 5 rows)::

                     Name type_cs type_ctrl type_dhw type_hs type_vent
            0     B154862      T0        T1       T1      T1       T0
            1     B153604      T0        T1       T1      T1       T0
            2     B153831      T0        T1       T1      T1       T0
            3  B302022960      T0        T0       T0      T0       T0
            4  B302034063      T0        T0       T0      T0       T0

    :returns: A DataFrame containing temperature data for each building in the scenario. More information can be
              found in the contributors manual:
              https://architecture-building-systems.gitbooks.io/cea-toolbox-for-arcgis-manual/content/delivery_technologies.html
    :rtype: DataFrame

    Each row contains the following fields:

    ==========    =======   ===========================================================================
    Column           e.g.   Description
    ==========    =======   ===========================================================================
    Name          B154862   (building name)
    type_hs            T1   (copied from input, code for type of heating system)
    type_cs            T0   (copied from input, code for type of cooling system)
    type_dhw           T1   (copied from input, code for type of hot water system)
    type_ctrl          T1   (copied from input, code for type of controller for heating and cooling system)
    type_vent          T1   (copied from input, code for type of ventilation system)
    Tshs0_C            90   (heating system supply temperature at nominal conditions [C])
    dThs0_C            20   (delta of heating system temperature at nominal conditions [C])
    Qhsmax_Wm2        500   (maximum heating system power capacity per unit of gross built area [W/m2])
    dThs_C           0.15   (correction temperature of emission losses due to type of heating system [C])
    Tscs0_C             0   (cooling system supply temperature at nominal conditions [C])
    dTcs0_C             0   (delta of cooling system temperature at nominal conditions [C])
    Qcsmax_Wm2          0   (maximum cooling system power capacity per unit of gross built area [W/m2])
    dTcs_C            0.5   (correction temperature of emission losses due to type of cooling system [C])
    dT_Qhs            1.2   (correction temperature of emission losses due to control system of heating [C])
    dT_Qcs           -1.2   (correction temperature of emission losses due to control system of cooling[C])
    Tsww0_C            60   (dhw system supply temperature at nominal conditions [C])
    dTww0_C            50   (delta of dwh system temperature at nominal conditions [C])
    Qwwmax_Wm2        500   (maximum dwh system power capacity per unit of gross built area [W/m2])
    MECH_VENT        True   (copied from input, ventilation system configuration)
    WIN_VENT        False   (copied from input, ventilation system configuration)
    HEAT_REC         True   (copied from input, ventilation system configuration)
    NIGHT_FLSH       True   (copied from input, ventilation system control strategy)
    ECONOMIZER      False   (copied from input, ventilation system control strategy)
    ==========    =======   ===========================================================================

    Data is read from :py:meth:`cea.inputlocator.InputLocator.get_technical_emission_systems` (e.g.
    ``db/Systems/emission_systems.csv``)
    """
    prop_emission_heating = pd.read_excel(locator.get_technical_emission_systems(), 'heating')
    prop_emission_cooling = pd.read_excel(locator.get_technical_emission_systems(), 'cooling')
    prop_emission_dhw = pd.read_excel(locator.get_technical_emission_systems(), 'dhw')
    prop_emission_control_heating_and_cooling = pd.read_excel(locator.get_technical_emission_systems(), 'controller')
    prop_ventilation_system_and_control = pd.read_excel(locator.get_technical_emission_systems(), 'ventilation')

    df_emission_heating = prop_HVAC.merge(prop_emission_heating, left_on='type_hs', right_on='code')
    df_emission_cooling = prop_HVAC.merge(prop_emission_cooling, left_on='type_cs', right_on='code')
    df_emission_control_heating_and_cooling = prop_HVAC.merge(prop_emission_control_heating_and_cooling,
                                                              left_on='type_ctrl', right_on='code')
    df_emission_dhw = prop_HVAC.merge(prop_emission_dhw, left_on='type_dhw', right_on='code')
    df_ventilation_system_and_control = prop_HVAC.merge(prop_ventilation_system_and_control, left_on='type_vent',
                                                        right_on='code')

    fields_emission_heating = ['Name', 'type_hs', 'type_cs', 'type_dhw', 'type_ctrl', 'type_vent', 'Tshs0_C', 'dThs0_C',
                               'Qhsmax_Wm2', 'dThs_C']
    fields_emission_cooling = ['Name', 'Tscs0_C', 'dTcs0_C', 'Qcsmax_Wm2', 'dTcs_C']
    fields_emission_control_heating_and_cooling = ['Name', 'dT_Qhs', 'dT_Qcs']
    fields_emission_dhw = ['Name', 'Tsww0_C', 'dTww0_C', 'Qwwmax_Wm2']
    fields_system_ctrl_vent = ['Name', 'MECH_VENT', 'WIN_VENT', 'HEAT_REC', 'NIGHT_FLSH', 'ECONOMIZER']

    result = df_emission_heating[fields_emission_heating].merge(df_emission_cooling[fields_emission_cooling],
                                                                on='Name').merge(
        df_emission_control_heating_and_cooling[fields_emission_control_heating_and_cooling],
        on='Name').merge(df_emission_dhw[fields_emission_dhw],
                         on='Name').merge(df_ventilation_system_and_control[fields_system_ctrl_vent], on='Name')
    return result


def get_envelope_properties(locator, prop_architecture):
    prop_roof = pd.read_excel(locator.get_envelope_systems(), 'ROOF')
    prop_wall = pd.read_excel(locator.get_envelope_systems(), 'WALL')
    prop_win = pd.read_excel(locator.get_envelope_systems(), 'WINDOW')
    prop_shading = pd.read_excel(locator.get_envelope_systems(), 'SHADING')
    prop_construction = pd.read_excel(locator.get_envelope_systems(), 'CONSTRUCTION')
    prop_leakage = pd.read_excel(locator.get_envelope_systems(), 'LEAKAGE')

    df_construction = prop_architecture.merge(prop_construction, left_on='type_cons', right_on='code')
    df_leakage = prop_architecture.merge(prop_leakage, left_on='type_leak', right_on='code')
    df_roof = prop_architecture.merge(prop_roof, left_on='type_roof', right_on='code')
    df_wall = prop_architecture.merge(prop_wall, left_on='type_wall', right_on='code')
    df_win = prop_architecture.merge(prop_win, left_on='type_win', right_on='code')
    df_shading = prop_architecture.merge(prop_shading, left_on='type_shade', right_on='code')

    fields_construction = ['Name', 'Cm_Af']
    fields_leakage = ['Name', 'n50']
    fields_roof = ['Name', 'e_roof', 'a_roof', 'U_roof', 'Hs']
    fields_wall = ['Name', 'wwr_north', 'wwr_west', 'wwr_east', 'wwr_south',
                   'e_wall', 'a_wall', 'U_wall', 'U_base']
    fields_win = ['Name', 'e_win', 'G_win', 'U_win']
    fields_shading = ['Name', 'rf_sh']

    envelope_prop = df_roof[fields_roof].merge(df_wall[fields_wall],
                                               on='Name').merge(df_win[fields_win],
                                                                on='Name').merge(df_shading[fields_shading],
                                                                                 on='Name').merge(
        df_construction[fields_construction],
        on='Name').merge(df_leakage[fields_leakage],
                         on='Name')

    return envelope_prop


def get_prop_solar(locator):
    solar = pd.read_csv(locator.get_radiation()).set_index('Name')
    solar_list = solar.values.tolist()
    surface_properties = pd.read_csv(locator.get_surface_properties())
    surface_properties['Awall'] = (
        surface_properties['Shape_Leng'] * surface_properties['FactorShade'] * surface_properties['Freeheight'])
    sum_surface = surface_properties[['Awall', 'Name']].groupby(['Name']).sum().values

    I_sol = I_roof = I_win = [a / b for a, b in zip(solar_list, sum_surface)]

    result = pd.DataFrame({'Name': solar.index, 'I_win': I_sol, 'I_roof': I_roof, 'I_wall': I_win})

    return result
