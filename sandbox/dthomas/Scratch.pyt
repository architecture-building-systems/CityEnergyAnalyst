class ScratchTool(object):
    """Test some arcpy stuff"""

    def __init__(self):
        self.label = 'Scratch'
        self.description = 'Just messing around with arcpy'
        self.canRunInBackground = False

    def getParameterInfo(self):
        return []

    def execute(self, parameters, messages):
        building_geometry = r"C:\reference-case\baseline\1-inputs\1-buildings\building_geometry.shp"
        import arcpy
        import fiona
        with fiona.open(building_geometry) as shp:
            longitude = shp.crs['lon_0']
            latitude = shp.crs['lat_0']
        arcpy.AddMessage('longitude: %s' % longitude)
        arcpy.AddMessage('latitude: %s' % latitude)

class Toolbox(object):
    def __init__(self):
        self.label = 'Scratch-Toolbox for messing around'
        self.alias = 'dthomas'
        self.tools = [ScratchTool]
