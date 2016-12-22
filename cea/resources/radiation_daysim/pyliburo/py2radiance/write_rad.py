#==================================================================================================
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
#   Authors: Patrick Janssen <patrick@janssen.name>
#           Chen Kian Wee <chenkianwee@gmail.com>
# ==================================================================================================


def surface(name, material, points):
    surface = material + " polygon " + name + "\n"+\
    "0\n"+\
    "0\n"+\
    str(len(points) * 3) + "\n"
    for point in points:
        surface = surface + "    " + str(point[0]) + "  " + str(point[1]) + "  " + str(point[2]) + "\n"
    surface = surface + "\n"
    return surface

def glow(name, colour):
    glow = "skyfunc glow " + name + "\n"+\
    "0\n"+\
    "0\n"+\
    "4 " +\
    str(colour[0])+ " "  +\
    str(colour[1]) + " " +\
    str(colour[2]) + " 0\n"
    glow = glow + "\n"
    return glow 

def source(name, material, direction):
    source = material + " source " + name + "\n"+\
    "0\n"+\
    "0\n"+\
    "4 " +\
    str(direction[0])+ " "  +\
    str(direction[1]) + " " +\
    str(direction[2]) + " 180\n"
    source = source + "\n"
    return source

def brightfunc(cal_name):
    brightfunc = "void brightfunc skyfunc\n" +\
                 "2 skybright " + cal_name + "\n"+\
                 "0\n"+\
                 "0\n\n"
    return brightfunc


def material_glass(name, transmission):
    material_glass = "# Glass material\n"+\
    "void glass " + name + "\n"+\
    "0\n"+\
    "0\n"+\
    "3 " +\
    str(transmission[0])+ " "  +\
    str(transmission[1]) + " " +\
    str(transmission[2]) + "\n\n"
    return material_glass


def material_plastic(name, colour, spec, rough):
    material_plastic = "# Plastic material\n"+\
    "void plastic " + name + "\n"+\
    "0\n"+\
    "0\n"+\
    "5 " +\
    str(colour[0])+ " "  +\
    str(colour[1]) + " " +\
    str(colour[2]) + " " +\
    str(spec) + " " +\
    str(rough) + "\n\n"
    return material_plastic

def sensor_file(positions, normals):
    if not positions or not normals:
        raise Exception
    if len(positions) != len(normals):
        raise Exception
    sensors = ""
    for i in range(len(positions)):
        pos = positions[i]
        nor = normals[i]
        sensors = sensors + str(pos[0]) + " " + str(pos[1]) + " " + str(pos[2]) + " " + str(nor[0]) + " " + str(nor[1]) + " " + str(nor[2]) + "\n"
    return sensors 
