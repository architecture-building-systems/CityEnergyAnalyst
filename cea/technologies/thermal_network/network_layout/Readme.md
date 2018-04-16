
The steps to get a preliminary network layout.

1. Get as an input file a shapefile storing potential paths for the network. In most cases it is assumed as a street network.
2. store the file in locator.locator.get_street_network().
3. run main.py
4. now you can modify the nodes and edges stored in the input/networks folder.


Steps to further modifying edge/node.shp:
1. Specify the plant locations by modifying nodes.shp (change the "Type" column to "PLANT" at the plant node.)
2. Make sure the node.cpg/edge.cpg files only contain "UTF-8"