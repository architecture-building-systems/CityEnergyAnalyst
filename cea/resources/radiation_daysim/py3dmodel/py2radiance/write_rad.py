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
