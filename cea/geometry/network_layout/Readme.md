
The steps to get a preliminary network layout.

1. Get as an input file a shapefile storing potential paths for the network. In most cases it is assumed as a street network.
2. store the file in locator.locator.get_street_network().
3. run substations_location.py
4. run connectivity potential.py
5. run minimum_spanning_tree.py
6. now you can modify the nodes and edges stored in the input/networks folder.

Limitations:
The minimum spanning tree consider all nodes, and a way around could not be found. The best is to edit the points
manually at the moment.

Steps to further modifying edge/node.shp:
1. Clean up the nodes.shp and edges.shp by deleting the nodes/edges that are connected to non-buildings.
2. Specify the plant locations by modifying nodes.shp (change the "Type" column to "PLANT" at the plant node.)
3. Make sure the node.cpg/edge.cpg files only contain "UTF-8"