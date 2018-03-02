These folders contain shape files of network nodes and edges for reference-case-open. 
Each file represents one network configuration.
Please refer to the .png file or open the .shp files in ArcGIS for the network layout.

To run simulation of `network1`:
1. copy all files in `network1` folder to `DC` or `DH` folder.
2. set scenario reference to `reference-case-open`
3. run `cea/demand/demand_main.py` 
4. open `cea/technologies/thermal_network_matrix.py`, set `network_type` for `thermal_network_main` 
5. run  `cea/technologies/thermal_network_matrix.py`