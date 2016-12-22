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
import py3dmodel

#==============================================================================================================================
#general functions
#==============================================================================================================================   
def pypolygons2occsolid(pypolygon_list):
    face_list = []
    for polygon_pts in pypolygon_list:
        face = py3dmodel.construct.make_polygon(polygon_pts)
        face_list.append(face)

    #make shell
    shell = py3dmodel.construct.make_shell_frm_faces(face_list)[0]
    shell = py3dmodel.modify.fix_shell_orientation(shell)
    
    solid = py3dmodel.construct.make_solid(shell)
    solid = py3dmodel.modify.fix_shape(solid)
    return solid
    
#function to round the points
def round_points(pyptlist):
    rounded =  []
    for point in pyptlist:
        rounded_pt = round_pt(point, 5)
        rounded.append(rounded_pt)
    return rounded
    
def round_pt(pypt, ndecimal):
    rounded_pt = (round(pypt[0],ndecimal) + 0, round(pypt[1],ndecimal)+0, round(pypt[2],ndecimal)+0)
    return rounded_pt