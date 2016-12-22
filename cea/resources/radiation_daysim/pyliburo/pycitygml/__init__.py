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

from lxml import etree
from lxml.etree import ElementTree, Element

import gmlgeometry
import write_gmlgeometry
import write_gml


class Writer(object):
    def __init__(self):
        self.et = write_gml.write_root()
        
    def create_cityobjectmember(self):
        cityObjectMember = Element('cityObjectMember')
        return cityObjectMember
            
    def add_landuse(self, lod, name, function, epsg, generic_attrib_dict, geometry_list):
        landuse = write_gml.write_landuse(lod, name, function, epsg, generic_attrib_dict, geometry_list)
        self.et.append(landuse)

    def add_transportation(self, trpt_type, lod, name, rd_class, function, epsg, generic_attrib_dict, geometry_list):
        transportation = write_gml.write_transportation(trpt_type, lod, name, rd_class, function, epsg, generic_attrib_dict, geometry_list)
        self.et.append(transportation)

    def add_building(self, lod, name, buildg_class, function, usage,yr_constr,rooftype,height,stry_abv_grd,
                   stry_blw_grd, epsg, generic_attrib_dict, geometry_list):
        
        bldg = write_gml.write_building(lod, name,buildg_class,function,usage,yr_constr,rooftype,height,stry_abv_grd,
                   stry_blw_grd, epsg, generic_attrib_dict, geometry_list)
        
        self.et.append(bldg)
        
    def add_cityfurniture(self,lod, name,furn_class,function, epsg, generic_attrib_dict, geometry_list ):
        city_frn = write_gml.write_cityfurniture(lod, name,furn_class,function, epsg, generic_attrib_dict, geometry_list)
        self.et.append(city_frn)
        
    def add_tin_relief(self, lod, name, geometry_list ):
        tin_relief = write_gml.write_tin_relief(lod,name,geometry_list)
        self.et.append(tin_relief)

    def write2string(self):
        print etree.tostring(self.et, pretty_print=True)
        
    def write(self, filepath):
        outFile = open(filepath, 'w')
        ElementTree(self.et).write(outFile,pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes")
        outFile.close()

class Reader(object):
    def __init__(self, filepath):
        self.tree = etree.parse(filepath)
        self.citymodelnode = self.tree.getroot()
        self.namespaces = {"citygml":write_gml.XMLNamespaces.citygml,
                           "core": write_gml.XMLNamespaces.core,
                           "xsi": write_gml.XMLNamespaces.xsi,
                           "trans": write_gml.XMLNamespaces.trans,
                           "wtr": write_gml.XMLNamespaces.wtr,
                           "gml": write_gml.XMLNamespaces.gml,
                           "smil20lang": write_gml.XMLNamespaces.smil20lang,
                           "xlink": write_gml.XMLNamespaces.xlink,
                           "grp": write_gml.XMLNamespaces.grp,
                           "luse": write_gml.XMLNamespaces.luse,
                           "frn": write_gml.XMLNamespaces.frn,
                           "app": write_gml.XMLNamespaces.app,
                           "tex": write_gml.XMLNamespaces.tex,
                           "smil20": write_gml.XMLNamespaces.smil20,
                           "xAL": write_gml.XMLNamespaces.xAL,
                           "bldg": write_gml.XMLNamespaces.bldg,
                           "dem": write_gml.XMLNamespaces.dem,
                           "veg": write_gml.XMLNamespaces.veg,
                           "gen": write_gml.XMLNamespaces.gen}
        
        self.cityobjectmembers = self.tree.findall("citygml:cityObjectMember", namespaces=self.namespaces)
        
    def get_buildings(self):
        buildings = []
        cityobjectmembers = self.cityobjectmembers
        for cityobject in cityobjectmembers:
            building = cityobject.find("bldg:Building", namespaces=self.namespaces)
            if building is not None:
                buildings.append(building)
        return buildings
        
    def get_building_height(self, building):
        return float(building.find("bldg:measuredHeight", namespaces=self.namespaces).text)
        
    def get_building_storey(self, building):
        return int(building.find("bldg:storeysAboveGround", namespaces=self.namespaces).text)
        
    def get_building_function(self,building):
        return building.find("bldg:function", namespaces=self.namespaces).text
        
    def get_building_usage(self, building):
        return building.find("bldg:usage", namespaces=self.namespaces).text
        
    def get_building_class(self,building):
        return building.find("bldg:class", namespaces=self.namespaces).text
    
    def get_building_yr_constr(self,building):
        return building.find("bldg:yearOfConstruction", namespaces=self.namespaces).text
        
    def get_building_rooftype(self, building):
        return building.find("bldg:roofType", namespaces=self.namespaces).text
        
    def get_building_epsg(self, building):
        envelope = building.find("gml:boundedBy//gml:Envelope", namespaces=self.namespaces)
        epsg = envelope.attrib["srsName"]
        return epsg
    
    def get_building_storey_blw_grd(self, building):
        return building.find("bldg:storeysBelowGround", namespaces=self.namespaces).text
        
    def get_generic_attribs(self, cityobject):
        generic_attrib_dict = {}
        string_attribs = cityobject.findall("gen:stringAttribute", namespaces=self.namespaces )
        if string_attribs:
            for s_att in string_attribs:
                name = s_att.attrib["name"]
                value = s_att.find("gen:value",namespaces=self.namespaces).text
                generic_attrib_dict[name] = value
                
        int_attribs = cityobject.findall("gen:intAttribute", namespaces=self.namespaces )
        if int_attribs:
            for i_att in int_attribs:
                name = i_att.attrib["name"]
                value = i_att.find("gen:value",namespaces=self.namespaces).text
                generic_attrib_dict[name] = int(value)
                
        double_attribs = cityobject.findall("gen:doubleAttribute", namespaces=self.namespaces )
        if double_attribs:
            for d_att in double_attribs:
                name = d_att.attrib["name"]
                value = d_att.find("gen:value",namespaces=self.namespaces).text
                generic_attrib_dict[name] = float(value)
                
        return generic_attrib_dict
                
    def get_landuses(self):
        landuses = []
        cityobjectmembers = self.cityobjectmembers
        for cityobject in cityobjectmembers:
            landuse = cityobject.find("luse:LandUse", namespaces=self.namespaces)
            if landuse is not None:
                landuses.append(landuse)
        return landuses
        
    def get_landuse_name(self, landuse):
        return landuse.find("gml:name", namespaces=self.namespaces).text
        
    def get_landuse_function(self, landuse):
        return landuse.find("luse:function", namespaces=self.namespaces).text
        
    def get_bus_stops(self):
        stops = []
        cityobjectmembers = self.cityobjectmembers
        for cityobject in cityobjectmembers:
            frn = cityobject.find("frn:CityFurniture", namespaces=self.namespaces)
            if frn is not None:
                fclass = frn.find("frn:class", namespaces=self.namespaces).text
                ffunction = frn.find("frn:function", namespaces=self.namespaces).text
                if fclass == "1000" and ffunction == "1110":
                    stops.append(frn)
        return stops
    
    def get_roads(self):
        roads = []
        cityobjectmembers = self.cityobjectmembers
        for cityobject in cityobjectmembers:
            road = cityobject.find("trans:Road", namespaces=self.namespaces)
            if road is not None:
                roads.append(road)
        return roads

    def get_railways(self):
        rails = []
        cityobjectmembers = self.cityobjectmembers
        for cityobject in cityobjectmembers:
            rail = cityobject.find("trans:Railway", namespaces=self.namespaces)
            if rail is not None:
                rails.append(rail)
        return rails
        
    def get_epsg(self, cityobject):
        envelope = cityobject.find("gml:boundedBy//gml:Envelope", namespaces=self.namespaces)
        epsg = envelope.attrib["srsName"]
        return epsg
        
    def get_gml_id(self, cityobject):
        name = cityobject.attrib["{%s}id"% self.namespaces['gml']]
        return name
    
    def get_polygons(self,cityobject):
        polygons = cityobject.findall(".//gml:Polygon", namespaces=self.namespaces)
        return polygons
        
    def get_pypolygon_list(self, cityobject):
        polygons = self.get_polygons(cityobject)
        pypolygon_list = []
        for polygon in polygons:
            pyptlist = self.polygon_2_pt_list(polygon)
            pypolygon_list.append(pyptlist)
        return pypolygon_list
        
    def get_poslist(self, polygon):
        rings = polygon.findall("gml:exterior//gml:LinearRing", namespaces=self.namespaces)
        poly_poslist = []
        if rings is not None:
            for ring in rings:
                poslist = ring.find("gml:posList", namespaces=self.namespaces)
                poly_poslist.append(poslist)
                
        return poly_poslist
        
    def get_linestring(self, cityobject):
        lod0networks = cityobject.findall("trans:lod0Network", namespaces=self.namespaces)
        polylines = []
        for lod0 in lod0networks:
            linestrings = lod0.findall(".//gml:GeometricComplex//gml:LineString", namespaces=self.namespaces)
            if linestrings is not None:
                for lstring in linestrings:
                    poslist = lstring.find("gml:posList", namespaces=self.namespaces)
                    polylines.append(poslist)
                    
        return polylines
        
    def polygon_2_pt_list(self, polygon):
        poslist = self.get_poslist(polygon)[0]
        pos_list_str = poslist.text
        splitted_pt_list_str = pos_list_str.split(" ")
        srsdim = int(poslist.attrib["srsDimension"])
        npts = len(splitted_pt_list_str)/srsdim
                
        pt_list = []
        for c_cnt in range(npts):
            x = float(splitted_pt_list_str[c_cnt*srsdim])
            y = float(splitted_pt_list_str[(c_cnt*srsdim) + 1])
            z = float(splitted_pt_list_str[(c_cnt*srsdim) + 2])
            pt = (x,y,z)
            pt_list.append(pt)
            
        return pt_list
#===============================================================================================================================================================
if __name__ == '__main__':

    '''
    citygml = Writer()
    
    generic_attrib_dict = {"plot ratio":3.5, "comment": "interesting plot", "id":5}
    geometry_list = []

    pos_list2 = [[458877, 5438353, 6.31769], [458889, 5438353, 6.31769], [458889, 5438363, 6.31769], [458877, 5438363, 6.31769], [458877, 5438353, 6.31769]]
    pos_list3 = [[458877, 5438353, -0.2], [458877, 5438353, 6.31769], [458877, 5438363, 6.31769], [458877, 5438363, -0.2], [458877, 5438353, -0.2]]
    pos_list4 = [[458877, 5438363, -0.2], [458877, 5438363, 6.31769], [458889, 5438363, 6.31769], [458889, 5438363, -0.2], [458877, 5438363, -0.2]]
    pos_list5 = [[458889, 5438363, -0.2], [458889, 5438363, 6.31769], [458889, 5438353, 6.31769], [458889, 5438353, -0.2], [458889, 5438363, -0.2]]
    pos_list6 = [[458889, 5438353, -0.2], [458889, 5438353, 6.31769], [458877, 5438353, 6.31769], [458877, 5438353, -0.2], [458889, 5438353, -0.2]]
    pos_list = [pos_list2,pos_list3,pos_list4,pos_list5,pos_list6 ]
    
    for p in pos_list:
        srf = geometry.SurfaceMember(p)
        geometry_list.append(srf)
        
    #citygml.add_building("lod1", "building_test","1000","1000","1000","2016","1000","6.52","2","1", 'urn:adv:crs:ETRS89_UTM32', generic_attrib_dict, geometry_list)
    citygml.add_cityfurniture("lod1", "bus_stop_test","1000","1110", 'urn:adv:crs:ETRS89_UTM32', generic_attrib_dict, geometry_list)
    citygml.add_building("lod1", "building_test","1000","1000","1000","2016","1000","6.52","2","1", 'urn:adv:crs:ETRS89_UTM32', generic_attrib_dict, geometry_list)
    pos_list = [[23312.293, 21059.261, 0.0],[23312.293, 20869.394, 0.0],[23543.693, 20869.394, 0.0]]
    geometry_list = []
    linestring = geometry.LineString(pos_list)
    geometry_list.append(linestring)
    citygml.add_transportation("Railway", "lod0", "test_road", "1", "0", "EPSG:21781", generic_attrib_dict, geometry_list)
    pos_list = [[23312.293, 21059.261, 0.0],[23312.293, 20869.394, 0.0],[23543.693, 20869.394, 0.0]]
    srf = geometry.SurfaceMember(pos_list)
    geometry_list.append(srf)
    citygml.add_landuse("lod1", "test_plot", "1010", "EPSG:21781", generic_attrib_dict, geometry_list)

    pos_list1 = [458877, 5438353, -0.2]
    ref_pt = geometry.Point(pos_list1)
    citygml.add_cityfurniture("lod1", "bus_stop_test","1000","1110", 'urn:adv:crs:ETRS89_UTM32', "application/dxf", ref_pt, generic_attrib_dict, "F:\\kianwee_work\\smart\\oct2015-apr2016\\computational_env_for_optimisation\\bus_stop.dxf")
    filepath = 'F:\\kianwee_work\\smart\\oct2015-apr2016\\computational_env_for_optimisation\\bus_stop_class.gml'

    outFile = open(filepath, 'w')
    ElementTree(citygml.et).write(outFile,pretty_print = True, xml_declaration = True, encoding="UTF-8", standalone="yes")
    outFile.close()
    print "done"
    #print lxml.etree.tostring(citygml.et, pretty_print=True)
    '''