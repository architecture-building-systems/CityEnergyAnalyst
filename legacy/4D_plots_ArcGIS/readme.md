Steps to make 4D visualization
1.	Check settings at the end of script demand_4D_plot.py and run it.
2.	Once finished, open up ArcScene.
3.	Go to your default.gdb located in the Home folder in the Catalog window.
4.	Do right click on the default.gdb and do import feature class single. Go there and import the  zone_geometry file (zone.shp). Give it a name of more than 5 characters.
5.	Do right click on the default.gdb and do import table single. Go there and import the  4D_plot database we generated from python. Give it a name of more than 5 characters.
6.	Drag the newly imported zone geometry file to the scene.
7.	Right click in the zone layer go and create a join to the newly imported table. Do the join on building name.
8.	Do right click in the zone layer and go to properties/time tab. Here enable time on this layer. Select time field as ‘date’. Select time step interval as 1.
9.	Go to symbology tab. Go to quantities. In the Fields/Value select the value you want to display. In the color ramp, select one you like..
10.	Go to the extrusion tab and extrude features in this layer to the Height of the buildings. And click ok.
11.	Go to time slider icon. And hit the bottom play. It should work!!
Tricks to add a chart on top of the visualization
1.	Go to the main menu View/Graphs/Create Graph
2.	The graph you create and the data you display will be also enable to time.
Tricks to make it look good.
1.	Add a context in a neutral color (white.)
2.	Add roads and a terrain (add base heights and the zone layer on top).
3.	In the option of rendering of the zone layer, click on ‘use smooth shading if possible.
4.	Go to view/sceneproperties/illumination, and select where the source of light should be ocated.

