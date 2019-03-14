This folder stores Features of CEA that we no longer support.

1. Radiation_argis: it contains a series of scripts that would allow you to use the ArcGIS solar engine to calcualte solar
insolation for every hour of the year in buildings in CEA. It was great, but it did not consider reflections of the terrain
and it was quite slow. The feature was replaced for Radiation_Daysim, which is more powerful and detailed.

2. citygml_converter: it contans a series of functions that allow to translate CEA shapefiles into CityGML files. We had the thought on 
using CityGML as a main format for data exchange. But the format is just heavy and cumbersome to use for the moment.

3. retrofit: it contains a series of functions that helps users to define which buildings have a high retrofit potential.
The method is quite limited. It is just based on a threshold of consumption, but it does not include any notion of costs or
emissions. It was created as a requirement by a partner company. The use of the tool was never used again.

4. heatmaps: it contains a script to create a heatmap of energy consumption with the results of CEA. It turns out that these
heatmaps can be strongly misleading when we talk about energy consumption at the building and district scales.
We do not recommend their use anymore, beyond a cool visualziation method. Heatmaps can be created in ArcGIS or QGIS, we recommend
people interested in them, to use CEA outputs and those tools for this. But please handle with care.

5. Arcgis_interface: It contains scripts to the old interface of CEA in ArcGIS.  We do not offer more support to this interface.

6. Network_layout: It contains scripts to generate the layout of a thermal network with ArcGIS. A new script was developed in python.
   the network layout was the last step for CEA to become full open source
   
7. config_editor: This was an initial interface to CEA. It is not anymore supported.