# ==================================================================================================
#
#    Copyright (c) 2016, Chen Kian Wee (chenkianwee@gmail.com)
#
#    This file is part of pyliburo
#
#    pyliburo is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    pyliburo is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Dexen.  If not, see <http://www.gnu.org/licenses/>.
#
# ==================================================================================================
import os

import pycitygml
import py3dmodel
import gml3dmodel
import urbanformeval
import threedmodel

class Evals(object):
    def __init__(self, citygmlfile):
        self.citygml = pycitygml.Reader(citygmlfile)
        self.citygmlfilepath = citygmlfile
        self.buildings = self.citygml.get_buildings()
        self.landuses = self.citygml.get_landuses()
        self.stops = self.citygml.get_bus_stops()
        self.roads = self.citygml.get_roads()
        self.railways = self.citygml.get_railways()
        #occ geometries
        self.building_occsolids = None
        self.roof_occfaces = None
        self.facade_occfaces = None
        self.footprint_occfaces = None
        self.building_dictlist = None
        self.buildings_on_plot_2dlist = None #2d list of building dictlist according to the plot they belong to 
        self.landuse_occpolygons = None
        #radiance parameters
        self.rad_base_filepath = os.path.join(os.path.dirname(__file__),'py2radiance','base.rad')
        self.shgfavi_folderpath = os.path.join(os.path.dirname(self.citygmlfilepath), 'shgfavi_data')
        self.dfavi_folderpath = os.path.join(os.path.dirname(self.citygmlfilepath), 'dfavi_data')
        self.pvavi_folderpath = os.path.join(os.path.dirname(self.citygmlfilepath), 'pvavi_data')
        self.daysim_folderpath = os.path.join(os.path.dirname(self.citygmlfilepath), 'daysim_data')
        self.solarxdim = None
        self.solarydim = None
        self.rad = None
        #rad results 
        self.irrad_results = None
        self.illum_results = None
        self.facade_grid_srfs = None
        self.roof_grid_srfs = None
        
    def initialise_occgeom(self):
        buildings = self.buildings
        bsolid_list = []
        roof_list = []
        facade_list = []
        footprint_list = []
        building_dictlist = []
        for building in buildings:
            building_dict ={}
            #get all the polygons from the building 
            pypolygonlist = self.citygml.get_pypolygon_list(building) 
            bsolid = threedmodel.pypolygons2occsolid(pypolygonlist)
            #extract the polygons from the building and separate them into facade, roof, footprint
            facades, roofs, footprints = gml3dmodel.identify_building_surfaces(bsolid)
            building_dict["facade"] = facades
            building_dict["footprint"] = footprints[0]
            building_dict["roof"] = roofs
            building_dict["solid"] = bsolid
            building_dictlist.append(building_dict)
            bsolid_list.append(bsolid)
            facade_list.extend(facades)
            roof_list.extend(roofs)
            footprint_list.extend(footprints)
            
        self.building_dictlist = building_dictlist
        self.building_occsolids = bsolid_list
        self.facade_occfaces = facade_list
        self.roof_occfaces = roof_list
        self.footprint_occfaces = footprint_list
        
    def shgfavi(self, irrad_threshold, epwweatherfile, xdim, ydim, shgfavi_threshold=None):
        """
        Solar Heat Gain Facade Area to Volume Index (SHGFAVI) calculates the ratio of facade area that 
        receives irradiation above a specified level over the building volume. 
        """
        bsolid_list = self.building_occsolids
        avg_shgfavi, shgfavi_percent, shgfai, topo_list, irrad_ress = urbanformeval.shgfavi(bsolid_list, irrad_threshold, 
                                                                                            epwweatherfile, xdim, ydim, 
                                                                                            self.shgfavi_folderpath, 
                                                                                            shgfavi_threshold = shgfavi_threshold)
        
        self.irrad_results = irrad_ress
        return avg_shgfavi, shgfavi_percent, shgfai, topo_list, irrad_ress
        
    def dfavi(self, illum_threshold, epwweatherfile, xdim, ydim, dfavi_threshold=None):
        """
        Daylighting Facade Area to Volume Index (DFAI) calculates the ratio of facade area that 
        receives daylighting above a specified level, 
        over the building volume. 
        """            
        bsolid_list = self.building_occsolids
        avg_dfavi, dfavi_percent, dfai, topo_list, illum_ress = urbanformeval.dfavi(bsolid_list, illum_threshold, 
                                                                                     epwweatherfile, xdim,ydim, 
                                                                                     self.dfavi_folderpath, 
                                                                                     self.daysim_folderpath,
                                                                                     dfavi_threshold = dfavi_threshold)
                                                                                     
        
        self.illum_results = illum_ress
        return avg_dfavi, dfavi_percent, dfai, topo_list, illum_ress
        
   
        
    def pvavi(self, irrad_threshold, epwweatherfile, xdim, ydim, surface = "roof", pvavi_threshold = None):
        '''
        epv calculates the potential electricity 
        that can be generated on the roof of buildings annually.
        epv is represented in kWh/yr.
        
        PV Area to Volume Index (PVAVI) calculates the ratio of roof area that 
        receives irradiation above a specified level, 
        over the building volume. 
        '''
        bsolid_list = self.building_occsolids
        avg_pvavi, pvavi_percent, pvai, epv, topo_list, irrad_ress = urbanformeval.pvavi(bsolid_list, 
                                                                                           irrad_threshold, 
                                                                                           epwweatherfile, xdim, ydim, 
                                                                                           self.pvavi_folderpath, 
                                                                                           mode = surface,
                                                                                           pvavi_threshold = pvavi_threshold)
        
        return avg_pvavi, pvavi_percent, pvai, epv, topo_list, irrad_ress
    
    def pveavi(self, roof_irrad_threshold, facade_irrad_threshold, epwweatherfile, xdim, ydim, 
               surface = "roof", pvravi_threshold = None, pvfavi_threshold = None, pveavi_threshold = None):
        '''
        epv calculates the potential electricity 
        that can be generated on the roof of buildings annually.
        epv is represented in kWh/yr.
        
        PV Envelope Area to Volume Index (PVEAVI) calculates the ratio of roof area that 
        receives irradiation above a specified level, 
        over the building volume. 
        
        Same as PVAVI but runs it for the whole envelope 
        '''
        bsolid_list = self.building_occsolids
        avg_pvfavi, pvavi_percent, pvfai, epv, topo_list, irrad_ress = urbanformeval.pveavi(bsolid_list, 
                                                                                             roof_irrad_threshold, 
                                                                                             facade_irrad_threshold, 
                                                                                             epwweatherfile, xdim, ydim, 
                                                                                             self.pvavi_folderpath, 
                                                                                             pvravi_threshold = pvravi_threshold, 
                                                                                             pvfavi_threshold = pvfavi_threshold, 
                                                                                             pveavi_threshold = pveavi_threshold)
        return avg_pvfavi, pvavi_percent, pvfai, epv, topo_list, irrad_ress
        
    def initialise_fai(self):
        
        if self.building_dictlist == None:
            self.initialise_occgeom()
            
        landuses = self.landuses
        building_dictlist = self.building_dictlist
        building_dictlist2 = building_dictlist[:]
        landuse_occpolygons = []
        buildings_on_plot_2dlist = []
        
        for landuse in landuses:
            pypolygonlist = self.citygml.get_pypolygon_list(landuse)
            for pypolygon in pypolygonlist:    
                landuse_occpolygon = py3dmodel.construct.make_polygon(pypolygon)
                if building_dictlist2:
                    buildings_on_plot = gml3dmodel.buildings_on_landuse(landuse_occpolygon, building_dictlist2)
                    
                    if buildings_on_plot:
                        buildings_on_plot_2dlist.append(buildings_on_plot)
                        landuse_occpolygons.append(landuse_occpolygon)
                        for abuilding in buildings_on_plot:
                            building_dictlist2.remove(abuilding)
        
        self.buildings_on_plot_2dlist = buildings_on_plot_2dlist
        self.landuse_occpolygons = landuse_occpolygons

    def fai(self, wind_dir):
        """
        Frontal Area Index (FAI)
        """
        if self.buildings_on_plot_2dlist == None:
            self.initialise_fai()
            
        print "DONE WITH INITIALISATION"
        landuse_occpolygons = self.landuse_occpolygons
        buidlings_on_plot_2dlist = self.buildings_on_plot_2dlist
        fai_list = []
        fuse_psrfs_list = []
        surfaces_projected_list = []
        lcnt = 0
        for landuse_occpolygon in landuse_occpolygons:
            facade_occpolygons = []
            for building in buidlings_on_plot_2dlist[lcnt]:
                occfacades = building["facade"]
                facade_occpolygons.extend(occfacades)
                        
            fai,fuse_psrfs, projected_faces, windplane, surfaces_projected = urbanformeval.frontal_area_index(facade_occpolygons, landuse_occpolygon, wind_dir)
            fai_list.append(fai)
            fuse_psrfs_list.extend(fuse_psrfs)
            surfaces_projected_list.extend(surfaces_projected)
            lcnt+=1
            
        avg_fai = sum(fai_list)/float(len(fai_list))
        return avg_fai, fuse_psrfs_list, surfaces_projected_list
        
    def rdi(self):
        """
        Route Directness Index
        """
        pass


#===================================================================================================================================================