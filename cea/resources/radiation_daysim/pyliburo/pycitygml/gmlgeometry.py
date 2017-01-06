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
import write_gmlgeometry

class SurfaceMember(object):
    def __init__(self, pos_list):
        self.pos_list = pos_list
    def construct(self):
        surface = write_gmlgeometry.write_surface_member(self.pos_list)
        return surface
        
class Triangle(object):
    def __init__(self, pos_list):
        self.pos_list = pos_list
    def construct(self):
        triangle = write_gmlgeometry.write_triangle(self.pos_list)
        return triangle

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