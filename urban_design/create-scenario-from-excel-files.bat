set SCENARIO=c:\Users\darthoma\Documents\GitHub\CityEnergyAnalyst\urban_design\scenario
set INPUT=c:\Users\darthoma\Documents\GitHub\CityEnergyAnalyst\urban_design\cea_excel
mkdir %SCENARIO%\inputs
mkdir %SCENARIO%\inputs\building-geometry
mkdir %SCENARIO%\inputs\building-properties
cea excel-to-shapefile --excel-file %INPUT%\zone.xlsx --shapefile %SCENARIO%\inputs\building-geometry\zone.shp
cea excel-to-shapefile --excel-file %INPUT%\district.xlsx --shapefile %SCENARIO%\inputs\building-geometry\district.shp
cea excel-to-dbf --excel-file %INPUT%\age.xlsx --dbf-file %SCENARIO%\inputs\building-properties\age.dbf
cea excel-to-dbf --excel-file %INPUT%\architecture.xlsx --dbf-file %SCENARIO%\inputs\building-properties\architecture.dbf
cea excel-to-dbf --excel-file %INPUT%\occupancy.xlsx --dbf-file %SCENARIO%\inputs\building-properties\occupancy.dbf
cea excel-to-dbf --excel-file %INPUT%\supply_systems.xlsx --dbf-file %SCENARIO%\inputs\building-properties\supply_systems.dbf