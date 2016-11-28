from . import write_gmlgeometry

class SurfaceMember(object):
    def __init__(self, pos_list):
        self.pos_list = pos_list
    def construct(self):
        surface = write_gmlgeometry.write_surface_member(self.pos_list)
        return surface

class LineString(object):
    def __init__(self, pos_list):
        self.pos_list = pos_list
    def construct(self):
        line = write_gmlgeometry.write_linestring(self.pos_list)
        return line
    
class Point(object):
    def __init__(self, pos):
        self.pos = pos
    def construct(self):
        pt = write_gmlgeometry.write_pt(self.pos)
        return pt