import uuid

from lxml.etree import Element, SubElement
from . import write_gml

def pos_list2text(pos_list):
    pos_text = ""
    num_pos = len(pos_list)
    pos_cnt = 0
    for pos in pos_list:
        if pos_cnt == num_pos-1:
            pos_text = pos_text + str(pos[0]) + " " + str(pos[1]) + " " + str(pos[2])
        else:
            pos_text = pos_text + str(pos[0]) + " " + str(pos[1]) + " " + str(pos[2]) + " "
        pos_cnt += 1

    return pos_text

def write_surface_member(pos_list):
    gml_surfaceMember = Element("{" + write_gml.XMLNamespaces.gml+ "}" + 'surfaceMember')
    gml_Polygon = SubElement(gml_surfaceMember,"{" + write_gml.XMLNamespaces.gml+ "}" + 'Polygon')
    gml_Polygon.attrib["{" + write_gml.XMLNamespaces.gml+ "}" +'id'] = 'UUID_' + str(uuid.uuid1())

    gml_exterior = SubElement(gml_Polygon, "{" + write_gml.XMLNamespaces.gml+ "}" + 'exterior')

    gml_LinearRing = SubElement(gml_exterior, "{" + write_gml.XMLNamespaces.gml+ "}" + 'LinearRing')
    gml_LinearRing.attrib["{" + write_gml.XMLNamespaces.gml+ "}" +'id'] = 'UUID_' + str(uuid.uuid1())

    gml_posList = SubElement(gml_LinearRing, "{" + write_gml.XMLNamespaces.gml+ "}" + 'posList')
    gml_posList.attrib['srsDimension'] = '3'
    
    gml_posList.text = pos_list2text(pos_list)

    return gml_surfaceMember

def write_linestring(pos_list):
    gml_LineString = Element("{" + write_gml.XMLNamespaces.gml+ "}" + 'LineString')
    gml_posList = SubElement(gml_LineString, "{" + write_gml.XMLNamespaces.gml+ "}" + 'posList')
    gml_posList.attrib['srsDimension'] = '3'
    gml_posList.text = pos_list2text(pos_list)
    return gml_LineString

def write_pt(pos):
    gml_Point = Element("{" + write_gml.XMLNamespaces.gml+ "}" + 'Point')
    gml_pos = SubElement(gml_Point,"{" + write_gml.XMLNamespaces.gml+ "}" + 'pos')
    gml_pos.attrib['srsDimension'] = "3"
    gml_pos.text = str(pos[0]) + " " + str(pos[1]) + " " + str(pos[2])
    return gml_pos
    
#===============================================================================================================================================================
if __name__ == '__main__':
    import lxml
    pos_list = [[23312.293, 21059.261, 0.0],[23312.293, 20869.394, 0.0],[23543.693, 20869.394, 0.0]]
    #print pos_list2text(pos_list)
    print lxml.etree.tostring(write_surface_member(pos_list), pretty_print = True)
