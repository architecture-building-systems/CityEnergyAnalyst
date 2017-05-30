<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<CityModel xmlns="http://www.opengis.net/citygml/2.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:gml="http://www.opengis.net/gml"
xmlns:bldg="http://www.opengis.net/citygml/building/2.0"
xsi:schemaLocation="http://www.opengis.net/citygml/landuse/2.0
http://www.opengis.net/citygml/building/2.0
http://schemas.opengis.net/citygml/building/2.0/building.xsd
http://www.opengis.net/citygml/cityobjectgroup/2.0
http://schemas.opengis.net/citygml/cityobjectgroup/2.0/cityObjectGroup.xsd
http://www.opengis.net/citygml/generics/2.0
http://schemas.opengis.net/citygml/generics/2.0/generics.xsd">
<cityObjectMember>
<bldg:Building>
<gml:name> Building_1 </gml:name>
<gml:boundedBy>
<gml:Envelope srsDimension="3" srsName="urn:ogc:def:crs,crs:EPSG:6.12:3068,crs:EPSG:6.12:5783">
<gml:lowerCorner> 3.58837851716 3.58837851716 0.0 </gml:lowerCorner>
<gml:upperCorner> 76.4116214828 76.4116214828 30.0 </gml:upperCorner>
</gml:Envelope>
</gml:boundedBy>
<bldg:function
codeSpace="http://www.sig3d.org/codelists/standard/building/2.0/_AbstractBuilding_function.xml"> None </bldg:function>
<bldg:measuredHeight uom="#m"> 30.0 </bldg:measuredHeight>
<bldg:storeysAboveGround> 10 </bldg:storeysAboveGround>
<bldg:storeyHeightsAboveGround uom="#m"> 3.0 </bldg:storeyHeightsAboveGround>
<bldg:boundedBy>
<bldg:GroundSurface>
<gml:name> footprint_1_1 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 76.411621 0.0 76.411621 76.411621 0.0 76.411621 40.0 0.0 53.774977 40.0 0.0 53.774977 53.774977 0.0 26.225023 53.774977 0.0 26.225023 40.0 0.0 3.588379 40.0 0.0 3.588379 76.411621 0.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:GroundSurface>
<bldg:GroundSurface>
<gml:name> footprint_1_2 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 0.0 3.588379 40.0 0.0 26.225023 40.0 0.0 26.225023 26.225023 0.0 53.774977 26.225023 0.0 53.774977 40.0 0.0 76.411621 40.0 0.0 76.411621 3.588379 0.0 3.588379 3.588379 0.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:GroundSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_1 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 0.0 3.588379 3.588379 3.0 3.588379 76.411621 3.0 3.588379 76.411621 0.0 3.588379 3.588379 0.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_1 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 20.056534 0.678416 3.588379 20.056534 2.321584 3.588379 59.943466 2.321584 3.588379 59.943466 0.678416 3.588379 20.056534 0.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_2 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 0.0 26.225023 26.225023 3.0 26.225023 53.774977 3.0 26.225023 53.774977 0.0 26.225023 26.225023 0.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_2 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 35.64397 1.025658 26.225023 35.64397 1.974342 26.225023 44.35603 1.974342 26.225023 44.35603 1.025658 26.225023 35.64397 1.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_3 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 0.0 3.588379 107.588379 3.0 3.588379 180.411621 3.0 3.588379 180.411621 0.0 3.588379 107.588379 0.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_3 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 124.056534 0.678416 3.588379 124.056534 2.321584 3.588379 163.943466 2.321584 3.588379 163.943466 0.678416 3.588379 124.056534 0.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_4 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 0.0 26.225023 130.225023 3.0 26.225023 157.774977 3.0 26.225023 157.774977 0.0 26.225023 130.225023 0.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_4 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 139.64397 1.025658 26.225023 139.64397 1.974342 26.225023 148.35603 1.974342 26.225023 148.35603 1.025658 26.225023 139.64397 1.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_5 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 3.0 3.588379 3.588379 6.0 3.588379 76.411621 6.0 3.588379 76.411621 3.0 3.588379 3.588379 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_5 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 20.056534 3.678416 3.588379 20.056534 5.321584 3.588379 59.943466 5.321584 3.588379 59.943466 3.678416 3.588379 20.056534 3.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_6 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 3.0 26.225023 26.225023 6.0 26.225023 53.774977 6.0 26.225023 53.774977 3.0 26.225023 26.225023 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_6 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 35.64397 4.025658 26.225023 35.64397 4.974342 26.225023 44.35603 4.974342 26.225023 44.35603 4.025658 26.225023 35.64397 4.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_7 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 3.0 3.588379 107.588379 6.0 3.588379 180.411621 6.0 3.588379 180.411621 3.0 3.588379 107.588379 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_7 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 124.056534 3.678416 3.588379 124.056534 5.321584 3.588379 163.943466 5.321584 3.588379 163.943466 3.678416 3.588379 124.056534 3.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_8 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 3.0 26.225023 130.225023 6.0 26.225023 157.774977 6.0 26.225023 157.774977 3.0 26.225023 130.225023 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_8 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 139.64397 4.025658 26.225023 139.64397 4.974342 26.225023 148.35603 4.974342 26.225023 148.35603 4.025658 26.225023 139.64397 4.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_9 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 6.0 3.588379 3.588379 9.0 3.588379 76.411621 9.0 3.588379 76.411621 6.0 3.588379 3.588379 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_9 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 20.056534 6.678416 3.588379 20.056534 8.321584 3.588379 59.943466 8.321584 3.588379 59.943466 6.678416 3.588379 20.056534 6.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_10 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 6.0 26.225023 26.225023 9.0 26.225023 53.774977 9.0 26.225023 53.774977 6.0 26.225023 26.225023 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_10 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 35.64397 7.025658 26.225023 35.64397 7.974342 26.225023 44.35603 7.974342 26.225023 44.35603 7.025658 26.225023 35.64397 7.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_11 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 6.0 3.588379 107.588379 9.0 3.588379 180.411621 9.0 3.588379 180.411621 6.0 3.588379 107.588379 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_11 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 124.056534 6.678416 3.588379 124.056534 8.321584 3.588379 163.943466 8.321584 3.588379 163.943466 6.678416 3.588379 124.056534 6.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_12 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 6.0 26.225023 130.225023 9.0 26.225023 157.774977 9.0 26.225023 157.774977 6.0 26.225023 130.225023 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_12 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 139.64397 7.025658 26.225023 139.64397 7.974342 26.225023 148.35603 7.974342 26.225023 148.35603 7.025658 26.225023 139.64397 7.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_13 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 9.0 3.588379 3.588379 12.0 3.588379 76.411621 12.0 3.588379 76.411621 9.0 3.588379 3.588379 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_13 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 20.056534 9.678416 3.588379 20.056534 11.321584 3.588379 59.943466 11.321584 3.588379 59.943466 9.678416 3.588379 20.056534 9.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_14 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 9.0 26.225023 26.225023 12.0 26.225023 53.774977 12.0 26.225023 53.774977 9.0 26.225023 26.225023 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_14 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 35.64397 10.025658 26.225023 35.64397 10.974342 26.225023 44.35603 10.974342 26.225023 44.35603 10.025658 26.225023 35.64397 10.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_15 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 9.0 3.588379 107.588379 12.0 3.588379 180.411621 12.0 3.588379 180.411621 9.0 3.588379 107.588379 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_15 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 124.056534 9.678416 3.588379 124.056534 11.321584 3.588379 163.943466 11.321584 3.588379 163.943466 9.678416 3.588379 124.056534 9.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_16 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 9.0 26.225023 130.225023 12.0 26.225023 157.774977 12.0 26.225023 157.774977 9.0 26.225023 130.225023 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_16 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 139.64397 10.025658 26.225023 139.64397 10.974342 26.225023 148.35603 10.974342 26.225023 148.35603 10.025658 26.225023 139.64397 10.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_17 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 12.0 3.588379 3.588379 15.0 3.588379 76.411621 15.0 3.588379 76.411621 12.0 3.588379 3.588379 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_17 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 20.056534 12.678416 3.588379 20.056534 14.321584 3.588379 59.943466 14.321584 3.588379 59.943466 12.678416 3.588379 20.056534 12.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_18 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 12.0 26.225023 26.225023 15.0 26.225023 53.774977 15.0 26.225023 53.774977 12.0 26.225023 26.225023 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_18 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 35.64397 13.025658 26.225023 35.64397 13.974342 26.225023 44.35603 13.974342 26.225023 44.35603 13.025658 26.225023 35.64397 13.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_19 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 12.0 3.588379 107.588379 15.0 3.588379 180.411621 15.0 3.588379 180.411621 12.0 3.588379 107.588379 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_19 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 124.056534 12.678416 3.588379 124.056534 14.321584 3.588379 163.943466 14.321584 3.588379 163.943466 12.678416 3.588379 124.056534 12.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_20 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 12.0 26.225023 130.225023 15.0 26.225023 157.774977 15.0 26.225023 157.774977 12.0 26.225023 130.225023 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_20 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 139.64397 13.025658 26.225023 139.64397 13.974342 26.225023 148.35603 13.974342 26.225023 148.35603 13.025658 26.225023 139.64397 13.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_21 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 15.0 3.588379 3.588379 18.0 3.588379 76.411621 18.0 3.588379 76.411621 15.0 3.588379 3.588379 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_21 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 20.056534 15.678416 3.588379 20.056534 17.321584 3.588379 59.943466 17.321584 3.588379 59.943466 15.678416 3.588379 20.056534 15.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_22 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 15.0 26.225023 26.225023 18.0 26.225023 53.774977 18.0 26.225023 53.774977 15.0 26.225023 26.225023 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_22 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 35.64397 16.025658 26.225023 35.64397 16.974342 26.225023 44.35603 16.974342 26.225023 44.35603 16.025658 26.225023 35.64397 16.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_23 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 15.0 3.588379 107.588379 18.0 3.588379 180.411621 18.0 3.588379 180.411621 15.0 3.588379 107.588379 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_23 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 124.056534 15.678416 3.588379 124.056534 17.321584 3.588379 163.943466 17.321584 3.588379 163.943466 15.678416 3.588379 124.056534 15.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_24 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 15.0 26.225023 130.225023 18.0 26.225023 157.774977 18.0 26.225023 157.774977 15.0 26.225023 130.225023 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_24 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 139.64397 16.025658 26.225023 139.64397 16.974342 26.225023 148.35603 16.974342 26.225023 148.35603 16.025658 26.225023 139.64397 16.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_25 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 18.0 3.588379 3.588379 21.0 3.588379 76.411621 21.0 3.588379 76.411621 18.0 3.588379 3.588379 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_25 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 20.056534 18.678416 3.588379 20.056534 20.321584 3.588379 59.943466 20.321584 3.588379 59.943466 18.678416 3.588379 20.056534 18.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_26 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 18.0 26.225023 26.225023 21.0 26.225023 53.774977 21.0 26.225023 53.774977 18.0 26.225023 26.225023 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_26 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 35.64397 19.025658 26.225023 35.64397 19.974342 26.225023 44.35603 19.974342 26.225023 44.35603 19.025658 26.225023 35.64397 19.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_27 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 18.0 3.588379 107.588379 21.0 3.588379 180.411621 21.0 3.588379 180.411621 18.0 3.588379 107.588379 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_27 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 124.056534 18.678416 3.588379 124.056534 20.321584 3.588379 163.943466 20.321584 3.588379 163.943466 18.678416 3.588379 124.056534 18.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_28 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 18.0 26.225023 130.225023 21.0 26.225023 157.774977 21.0 26.225023 157.774977 18.0 26.225023 130.225023 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_28 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 139.64397 19.025658 26.225023 139.64397 19.974342 26.225023 148.35603 19.974342 26.225023 148.35603 19.025658 26.225023 139.64397 19.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_29 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 21.0 3.588379 3.588379 24.0 3.588379 76.411621 24.0 3.588379 76.411621 21.0 3.588379 3.588379 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_29 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 20.056534 21.678416 3.588379 20.056534 23.321584 3.588379 59.943466 23.321584 3.588379 59.943466 21.678416 3.588379 20.056534 21.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_30 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 21.0 26.225023 26.225023 24.0 26.225023 53.774977 24.0 26.225023 53.774977 21.0 26.225023 26.225023 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_30 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 35.64397 22.025658 26.225023 35.64397 22.974342 26.225023 44.35603 22.974342 26.225023 44.35603 22.025658 26.225023 35.64397 22.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_31 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 21.0 3.588379 107.588379 24.0 3.588379 180.411621 24.0 3.588379 180.411621 21.0 3.588379 107.588379 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_31 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 124.056534 21.678416 3.588379 124.056534 23.321584 3.588379 163.943466 23.321584 3.588379 163.943466 21.678416 3.588379 124.056534 21.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_32 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 21.0 26.225023 130.225023 24.0 26.225023 157.774977 24.0 26.225023 157.774977 21.0 26.225023 130.225023 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_32 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 139.64397 22.025658 26.225023 139.64397 22.974342 26.225023 148.35603 22.974342 26.225023 148.35603 22.025658 26.225023 139.64397 22.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_33 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 24.0 3.588379 3.588379 27.0 3.588379 76.411621 27.0 3.588379 76.411621 24.0 3.588379 3.588379 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_33 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 20.056534 24.678416 3.588379 20.056534 26.321584 3.588379 59.943466 26.321584 3.588379 59.943466 24.678416 3.588379 20.056534 24.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_34 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 24.0 26.225023 26.225023 27.0 26.225023 53.774977 27.0 26.225023 53.774977 24.0 26.225023 26.225023 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_34 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 35.64397 25.025658 26.225023 35.64397 25.974342 26.225023 44.35603 25.974342 26.225023 44.35603 25.025658 26.225023 35.64397 25.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_35 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 24.0 3.588379 107.588379 27.0 3.588379 180.411621 27.0 3.588379 180.411621 24.0 3.588379 107.588379 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_35 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 124.056534 24.678416 3.588379 124.056534 26.321584 3.588379 163.943466 26.321584 3.588379 163.943466 24.678416 3.588379 124.056534 24.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_36 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 24.0 26.225023 130.225023 27.0 26.225023 157.774977 27.0 26.225023 157.774977 24.0 26.225023 130.225023 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_36 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 139.64397 25.025658 26.225023 139.64397 25.974342 26.225023 148.35603 25.974342 26.225023 148.35603 25.025658 26.225023 139.64397 25.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_37 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 27.0 3.588379 3.588379 30.0 3.588379 76.411621 30.0 3.588379 76.411621 27.0 3.588379 3.588379 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_37 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 20.056534 27.678416 3.588379 20.056534 29.321584 3.588379 59.943466 29.321584 3.588379 59.943466 27.678416 3.588379 20.056534 27.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_38 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 27.0 26.225023 26.225023 30.0 26.225023 53.774977 30.0 26.225023 53.774977 27.0 26.225023 26.225023 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_38 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 35.64397 28.025658 26.225023 35.64397 28.974342 26.225023 44.35603 28.974342 26.225023 44.35603 28.025658 26.225023 35.64397 28.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_39 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 27.0 3.588379 107.588379 30.0 3.588379 180.411621 30.0 3.588379 180.411621 27.0 3.588379 107.588379 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_39 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 124.056534 27.678416 3.588379 124.056534 29.321584 3.588379 163.943466 29.321584 3.588379 163.943466 27.678416 3.588379 124.056534 27.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_40 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 27.0 26.225023 130.225023 30.0 26.225023 157.774977 30.0 26.225023 157.774977 27.0 26.225023 130.225023 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_40 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 139.64397 28.025658 26.225023 139.64397 28.974342 26.225023 148.35603 28.974342 26.225023 148.35603 28.025658 26.225023 139.64397 28.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_41 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 0.0 3.588379 3.588379 3.0 76.411621 3.588379 3.0 76.411621 3.588379 0.0 3.588379 3.588379 0.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_41 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 3.588379 0.678416 20.056534 3.588379 2.321584 59.943466 3.588379 2.321584 59.943466 3.588379 0.678416 20.056534 3.588379 0.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_42 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 0.0 26.225023 26.225023 3.0 53.774977 26.225023 3.0 53.774977 26.225023 0.0 26.225023 26.225023 0.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_42 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 26.225023 1.025658 35.64397 26.225023 1.974342 44.35603 26.225023 1.974342 44.35603 26.225023 1.025658 35.64397 26.225023 1.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_43 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 0.0 3.588379 107.588379 3.0 76.411621 107.588379 3.0 76.411621 107.588379 0.0 3.588379 107.588379 0.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_43 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 107.588379 0.678416 20.056534 107.588379 2.321584 59.943466 107.588379 2.321584 59.943466 107.588379 0.678416 20.056534 107.588379 0.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_44 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 0.0 26.225023 130.225023 3.0 53.774977 130.225023 3.0 53.774977 130.225023 0.0 26.225023 130.225023 0.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_44 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 130.225023 1.025658 35.64397 130.225023 1.974342 44.35603 130.225023 1.974342 44.35603 130.225023 1.025658 35.64397 130.225023 1.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_45 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 3.0 3.588379 3.588379 6.0 76.411621 3.588379 6.0 76.411621 3.588379 3.0 3.588379 3.588379 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_45 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 3.588379 3.678416 20.056534 3.588379 5.321584 59.943466 3.588379 5.321584 59.943466 3.588379 3.678416 20.056534 3.588379 3.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_46 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 3.0 26.225023 26.225023 6.0 53.774977 26.225023 6.0 53.774977 26.225023 3.0 26.225023 26.225023 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_46 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 26.225023 4.025658 35.64397 26.225023 4.974342 44.35603 26.225023 4.974342 44.35603 26.225023 4.025658 35.64397 26.225023 4.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_47 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 3.0 3.588379 107.588379 6.0 76.411621 107.588379 6.0 76.411621 107.588379 3.0 3.588379 107.588379 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_47 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 107.588379 3.678416 20.056534 107.588379 5.321584 59.943466 107.588379 5.321584 59.943466 107.588379 3.678416 20.056534 107.588379 3.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_48 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 3.0 26.225023 130.225023 6.0 53.774977 130.225023 6.0 53.774977 130.225023 3.0 26.225023 130.225023 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_48 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 130.225023 4.025658 35.64397 130.225023 4.974342 44.35603 130.225023 4.974342 44.35603 130.225023 4.025658 35.64397 130.225023 4.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_49 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 6.0 3.588379 3.588379 9.0 76.411621 3.588379 9.0 76.411621 3.588379 6.0 3.588379 3.588379 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_49 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 3.588379 6.678416 20.056534 3.588379 8.321584 59.943466 3.588379 8.321584 59.943466 3.588379 6.678416 20.056534 3.588379 6.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_50 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 6.0 26.225023 26.225023 9.0 53.774977 26.225023 9.0 53.774977 26.225023 6.0 26.225023 26.225023 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_50 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 26.225023 7.025658 35.64397 26.225023 7.974342 44.35603 26.225023 7.974342 44.35603 26.225023 7.025658 35.64397 26.225023 7.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_51 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 6.0 3.588379 107.588379 9.0 76.411621 107.588379 9.0 76.411621 107.588379 6.0 3.588379 107.588379 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_51 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 107.588379 6.678416 20.056534 107.588379 8.321584 59.943466 107.588379 8.321584 59.943466 107.588379 6.678416 20.056534 107.588379 6.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_52 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 6.0 26.225023 130.225023 9.0 53.774977 130.225023 9.0 53.774977 130.225023 6.0 26.225023 130.225023 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_52 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 130.225023 7.025658 35.64397 130.225023 7.974342 44.35603 130.225023 7.974342 44.35603 130.225023 7.025658 35.64397 130.225023 7.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_53 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 9.0 3.588379 3.588379 12.0 76.411621 3.588379 12.0 76.411621 3.588379 9.0 3.588379 3.588379 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_53 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 3.588379 9.678416 20.056534 3.588379 11.321584 59.943466 3.588379 11.321584 59.943466 3.588379 9.678416 20.056534 3.588379 9.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_54 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 9.0 26.225023 26.225023 12.0 53.774977 26.225023 12.0 53.774977 26.225023 9.0 26.225023 26.225023 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_54 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 26.225023 10.025658 35.64397 26.225023 10.974342 44.35603 26.225023 10.974342 44.35603 26.225023 10.025658 35.64397 26.225023 10.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_55 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 9.0 3.588379 107.588379 12.0 76.411621 107.588379 12.0 76.411621 107.588379 9.0 3.588379 107.588379 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_55 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 107.588379 9.678416 20.056534 107.588379 11.321584 59.943466 107.588379 11.321584 59.943466 107.588379 9.678416 20.056534 107.588379 9.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_56 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 9.0 26.225023 130.225023 12.0 53.774977 130.225023 12.0 53.774977 130.225023 9.0 26.225023 130.225023 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_56 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 130.225023 10.025658 35.64397 130.225023 10.974342 44.35603 130.225023 10.974342 44.35603 130.225023 10.025658 35.64397 130.225023 10.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_57 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 12.0 3.588379 3.588379 15.0 76.411621 3.588379 15.0 76.411621 3.588379 12.0 3.588379 3.588379 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_57 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 3.588379 12.678416 20.056534 3.588379 14.321584 59.943466 3.588379 14.321584 59.943466 3.588379 12.678416 20.056534 3.588379 12.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_58 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 12.0 26.225023 26.225023 15.0 53.774977 26.225023 15.0 53.774977 26.225023 12.0 26.225023 26.225023 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_58 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 26.225023 13.025658 35.64397 26.225023 13.974342 44.35603 26.225023 13.974342 44.35603 26.225023 13.025658 35.64397 26.225023 13.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_59 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 12.0 3.588379 107.588379 15.0 76.411621 107.588379 15.0 76.411621 107.588379 12.0 3.588379 107.588379 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_59 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 107.588379 12.678416 20.056534 107.588379 14.321584 59.943466 107.588379 14.321584 59.943466 107.588379 12.678416 20.056534 107.588379 12.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_60 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 12.0 26.225023 130.225023 15.0 53.774977 130.225023 15.0 53.774977 130.225023 12.0 26.225023 130.225023 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_60 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 130.225023 13.025658 35.64397 130.225023 13.974342 44.35603 130.225023 13.974342 44.35603 130.225023 13.025658 35.64397 130.225023 13.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_61 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 15.0 3.588379 3.588379 18.0 76.411621 3.588379 18.0 76.411621 3.588379 15.0 3.588379 3.588379 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_61 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 3.588379 15.678416 20.056534 3.588379 17.321584 59.943466 3.588379 17.321584 59.943466 3.588379 15.678416 20.056534 3.588379 15.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_62 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 15.0 26.225023 26.225023 18.0 53.774977 26.225023 18.0 53.774977 26.225023 15.0 26.225023 26.225023 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_62 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 26.225023 16.025658 35.64397 26.225023 16.974342 44.35603 26.225023 16.974342 44.35603 26.225023 16.025658 35.64397 26.225023 16.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_63 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 15.0 3.588379 107.588379 18.0 76.411621 107.588379 18.0 76.411621 107.588379 15.0 3.588379 107.588379 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_63 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 107.588379 15.678416 20.056534 107.588379 17.321584 59.943466 107.588379 17.321584 59.943466 107.588379 15.678416 20.056534 107.588379 15.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_64 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 15.0 26.225023 130.225023 18.0 53.774977 130.225023 18.0 53.774977 130.225023 15.0 26.225023 130.225023 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_64 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 130.225023 16.025658 35.64397 130.225023 16.974342 44.35603 130.225023 16.974342 44.35603 130.225023 16.025658 35.64397 130.225023 16.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_65 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 18.0 3.588379 3.588379 21.0 76.411621 3.588379 21.0 76.411621 3.588379 18.0 3.588379 3.588379 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_65 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 3.588379 18.678416 20.056534 3.588379 20.321584 59.943466 3.588379 20.321584 59.943466 3.588379 18.678416 20.056534 3.588379 18.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_66 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 18.0 26.225023 26.225023 21.0 53.774977 26.225023 21.0 53.774977 26.225023 18.0 26.225023 26.225023 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_66 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 26.225023 19.025658 35.64397 26.225023 19.974342 44.35603 26.225023 19.974342 44.35603 26.225023 19.025658 35.64397 26.225023 19.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_67 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 18.0 3.588379 107.588379 21.0 76.411621 107.588379 21.0 76.411621 107.588379 18.0 3.588379 107.588379 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_67 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 107.588379 18.678416 20.056534 107.588379 20.321584 59.943466 107.588379 20.321584 59.943466 107.588379 18.678416 20.056534 107.588379 18.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_68 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 18.0 26.225023 130.225023 21.0 53.774977 130.225023 21.0 53.774977 130.225023 18.0 26.225023 130.225023 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_68 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 130.225023 19.025658 35.64397 130.225023 19.974342 44.35603 130.225023 19.974342 44.35603 130.225023 19.025658 35.64397 130.225023 19.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_69 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 21.0 3.588379 3.588379 24.0 76.411621 3.588379 24.0 76.411621 3.588379 21.0 3.588379 3.588379 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_69 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 3.588379 21.678416 20.056534 3.588379 23.321584 59.943466 3.588379 23.321584 59.943466 3.588379 21.678416 20.056534 3.588379 21.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_70 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 21.0 26.225023 26.225023 24.0 53.774977 26.225023 24.0 53.774977 26.225023 21.0 26.225023 26.225023 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_70 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 26.225023 22.025658 35.64397 26.225023 22.974342 44.35603 26.225023 22.974342 44.35603 26.225023 22.025658 35.64397 26.225023 22.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_71 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 21.0 3.588379 107.588379 24.0 76.411621 107.588379 24.0 76.411621 107.588379 21.0 3.588379 107.588379 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_71 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 107.588379 21.678416 20.056534 107.588379 23.321584 59.943466 107.588379 23.321584 59.943466 107.588379 21.678416 20.056534 107.588379 21.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_72 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 21.0 26.225023 130.225023 24.0 53.774977 130.225023 24.0 53.774977 130.225023 21.0 26.225023 130.225023 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_72 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 130.225023 22.025658 35.64397 130.225023 22.974342 44.35603 130.225023 22.974342 44.35603 130.225023 22.025658 35.64397 130.225023 22.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_73 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 24.0 3.588379 3.588379 27.0 76.411621 3.588379 27.0 76.411621 3.588379 24.0 3.588379 3.588379 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_73 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 3.588379 24.678416 20.056534 3.588379 26.321584 59.943466 3.588379 26.321584 59.943466 3.588379 24.678416 20.056534 3.588379 24.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_74 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 24.0 26.225023 26.225023 27.0 53.774977 26.225023 27.0 53.774977 26.225023 24.0 26.225023 26.225023 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_74 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 26.225023 25.025658 35.64397 26.225023 25.974342 44.35603 26.225023 25.974342 44.35603 26.225023 25.025658 35.64397 26.225023 25.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_75 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 24.0 3.588379 107.588379 27.0 76.411621 107.588379 27.0 76.411621 107.588379 24.0 3.588379 107.588379 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_75 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 107.588379 24.678416 20.056534 107.588379 26.321584 59.943466 107.588379 26.321584 59.943466 107.588379 24.678416 20.056534 107.588379 24.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_76 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 24.0 26.225023 130.225023 27.0 53.774977 130.225023 27.0 53.774977 130.225023 24.0 26.225023 130.225023 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_76 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 130.225023 25.025658 35.64397 130.225023 25.974342 44.35603 130.225023 25.974342 44.35603 130.225023 25.025658 35.64397 130.225023 25.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_77 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 27.0 3.588379 3.588379 30.0 76.411621 3.588379 30.0 76.411621 3.588379 27.0 3.588379 3.588379 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_77 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 3.588379 27.678416 20.056534 3.588379 29.321584 59.943466 3.588379 29.321584 59.943466 3.588379 27.678416 20.056534 3.588379 27.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_78 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 26.225023 27.0 26.225023 26.225023 30.0 53.774977 26.225023 30.0 53.774977 26.225023 27.0 26.225023 26.225023 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_78 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 26.225023 28.025658 35.64397 26.225023 28.974342 44.35603 26.225023 28.974342 44.35603 26.225023 28.025658 35.64397 26.225023 28.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_79 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 27.0 3.588379 107.588379 30.0 76.411621 107.588379 30.0 76.411621 107.588379 27.0 3.588379 107.588379 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_79 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 107.588379 27.678416 20.056534 107.588379 29.321584 59.943466 107.588379 29.321584 59.943466 107.588379 27.678416 20.056534 107.588379 27.678416 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 130.225023 27.0 26.225023 130.225023 30.0 53.774977 130.225023 30.0 53.774977 130.225023 27.0 26.225023 130.225023 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 130.225023 28.025658 35.64397 130.225023 28.974342 44.35603 130.225023 28.974342 44.35603 130.225023 28.025658 35.64397 130.225023 28.025658 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:RoofSurface>
<gml:name> Roof_1_1 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 76.411621 30.0 76.411621 76.411621 30.0 76.411621 40.0 30.0 53.774977 40.0 30.0 53.774977 53.774977 30.0 26.225023 53.774977 30.0 26.225023 40.0 30.0 3.588379 40.0 30.0 3.588379 76.411621 30.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:RoofSurface>
<bldg:RoofSurface>
<gml:name> Roof_1_2 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 3.588379 30.0 3.588379 40.0 30.0 26.225023 40.0 30.0 26.225023 26.225023 30.0 53.774977 26.225023 30.0 53.774977 40.0 30.0 76.411621 40.0 30.0 76.411621 3.588379 30.0 3.588379 3.588379 30.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:RoofSurface>
</bldg:boundedBy>
<bldg:lod3Solid>
<gml:Solid>
<gml:exterior>
<gml:CompositeSurface>
</gml:CompositeSurface>
</gml:exterior>
</gml:Solid>
</bldg:lod3Solid>
</bldg:Building>
</cityObjectMember>
<cityObjectMember>
<bldg:Building>
<gml:name> Building_2 </gml:name>
<gml:boundedBy>
<gml:Envelope srsDimension="3" srsName="urn:ogc:def:crs,crs:EPSG:6.12:3068,crs:EPSG:6.12:5783">
<gml:lowerCorner> 3.58837851716 107.588378517 0.0 </gml:lowerCorner>
<gml:upperCorner> 76.4116214828 180.411621483 30.0 </gml:upperCorner>
</gml:Envelope>
</gml:boundedBy>
<bldg:function
codeSpace="http://www.sig3d.org/codelists/standard/building/2.0/_AbstractBuilding_function.xml"> None </bldg:function>
<bldg:measuredHeight uom="#m"> 30.0 </bldg:measuredHeight>
<bldg:storeysAboveGround> 10 </bldg:storeysAboveGround>
<bldg:storeyHeightsAboveGround uom="#m"> 3.0 </bldg:storeyHeightsAboveGround>
<bldg:boundedBy>
<bldg:GroundSurface>
<gml:name> footprint_2_1 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 180.411621 0.0 76.411621 180.411621 0.0 76.411621 144.0 0.0 53.774977 144.0 0.0 53.774977 157.774977 0.0 26.225023 157.774977 0.0 26.225023 144.0 0.0 3.588379 144.0 0.0 3.588379 180.411621 0.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:GroundSurface>
<bldg:GroundSurface>
<gml:name> footprint_2_2 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 0.0 3.588379 144.0 0.0 26.225023 144.0 0.0 26.225023 130.225023 0.0 53.774977 130.225023 0.0 53.774977 144.0 0.0 76.411621 144.0 0.0 76.411621 107.588379 0.0 3.588379 107.588379 0.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:GroundSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 76.411621 3.0 76.411621 3.588379 3.0 76.411621 3.588379 0.0 76.411621 76.411621 0.0 76.411621 76.411621 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 59.943466 2.321584 76.411621 20.056534 2.321584 76.411621 20.056534 0.678416 76.411621 59.943466 0.678416 76.411621 59.943466 2.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 53.774977 3.0 53.774977 26.225023 3.0 53.774977 26.225023 0.0 53.774977 53.774977 0.0 53.774977 53.774977 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 44.35603 1.974342 53.774977 35.64397 1.974342 53.774977 35.64397 1.025658 53.774977 44.35603 1.025658 53.774977 44.35603 1.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 180.411621 3.0 76.411621 107.588379 3.0 76.411621 107.588379 0.0 76.411621 180.411621 0.0 76.411621 180.411621 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 163.943466 2.321584 76.411621 124.056534 2.321584 76.411621 124.056534 0.678416 76.411621 163.943466 0.678416 76.411621 163.943466 2.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 157.774977 3.0 53.774977 130.225023 3.0 53.774977 130.225023 0.0 53.774977 157.774977 0.0 53.774977 157.774977 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 148.35603 1.974342 53.774977 139.64397 1.974342 53.774977 139.64397 1.025658 53.774977 148.35603 1.025658 53.774977 148.35603 1.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 76.411621 6.0 76.411621 3.588379 6.0 76.411621 3.588379 3.0 76.411621 76.411621 3.0 76.411621 76.411621 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 59.943466 5.321584 76.411621 20.056534 5.321584 76.411621 20.056534 3.678416 76.411621 59.943466 3.678416 76.411621 59.943466 5.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 53.774977 6.0 53.774977 26.225023 6.0 53.774977 26.225023 3.0 53.774977 53.774977 3.0 53.774977 53.774977 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 44.35603 4.974342 53.774977 35.64397 4.974342 53.774977 35.64397 4.025658 53.774977 44.35603 4.025658 53.774977 44.35603 4.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 180.411621 6.0 76.411621 107.588379 6.0 76.411621 107.588379 3.0 76.411621 180.411621 3.0 76.411621 180.411621 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 163.943466 5.321584 76.411621 124.056534 5.321584 76.411621 124.056534 3.678416 76.411621 163.943466 3.678416 76.411621 163.943466 5.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 157.774977 6.0 53.774977 130.225023 6.0 53.774977 130.225023 3.0 53.774977 157.774977 3.0 53.774977 157.774977 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 148.35603 4.974342 53.774977 139.64397 4.974342 53.774977 139.64397 4.025658 53.774977 148.35603 4.025658 53.774977 148.35603 4.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 76.411621 9.0 76.411621 3.588379 9.0 76.411621 3.588379 6.0 76.411621 76.411621 6.0 76.411621 76.411621 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 59.943466 8.321584 76.411621 20.056534 8.321584 76.411621 20.056534 6.678416 76.411621 59.943466 6.678416 76.411621 59.943466 8.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 53.774977 9.0 53.774977 26.225023 9.0 53.774977 26.225023 6.0 53.774977 53.774977 6.0 53.774977 53.774977 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 44.35603 7.974342 53.774977 35.64397 7.974342 53.774977 35.64397 7.025658 53.774977 44.35603 7.025658 53.774977 44.35603 7.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 180.411621 9.0 76.411621 107.588379 9.0 76.411621 107.588379 6.0 76.411621 180.411621 6.0 76.411621 180.411621 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 163.943466 8.321584 76.411621 124.056534 8.321584 76.411621 124.056534 6.678416 76.411621 163.943466 6.678416 76.411621 163.943466 8.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 157.774977 9.0 53.774977 130.225023 9.0 53.774977 130.225023 6.0 53.774977 157.774977 6.0 53.774977 157.774977 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 148.35603 7.974342 53.774977 139.64397 7.974342 53.774977 139.64397 7.025658 53.774977 148.35603 7.025658 53.774977 148.35603 7.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 76.411621 12.0 76.411621 3.588379 12.0 76.411621 3.588379 9.0 76.411621 76.411621 9.0 76.411621 76.411621 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 59.943466 11.321584 76.411621 20.056534 11.321584 76.411621 20.056534 9.678416 76.411621 59.943466 9.678416 76.411621 59.943466 11.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 53.774977 12.0 53.774977 26.225023 12.0 53.774977 26.225023 9.0 53.774977 53.774977 9.0 53.774977 53.774977 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 44.35603 10.974342 53.774977 35.64397 10.974342 53.774977 35.64397 10.025658 53.774977 44.35603 10.025658 53.774977 44.35603 10.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 180.411621 12.0 76.411621 107.588379 12.0 76.411621 107.588379 9.0 76.411621 180.411621 9.0 76.411621 180.411621 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 163.943466 11.321584 76.411621 124.056534 11.321584 76.411621 124.056534 9.678416 76.411621 163.943466 9.678416 76.411621 163.943466 11.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 157.774977 12.0 53.774977 130.225023 12.0 53.774977 130.225023 9.0 53.774977 157.774977 9.0 53.774977 157.774977 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 148.35603 10.974342 53.774977 139.64397 10.974342 53.774977 139.64397 10.025658 53.774977 148.35603 10.025658 53.774977 148.35603 10.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 76.411621 15.0 76.411621 3.588379 15.0 76.411621 3.588379 12.0 76.411621 76.411621 12.0 76.411621 76.411621 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 59.943466 14.321584 76.411621 20.056534 14.321584 76.411621 20.056534 12.678416 76.411621 59.943466 12.678416 76.411621 59.943466 14.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 53.774977 15.0 53.774977 26.225023 15.0 53.774977 26.225023 12.0 53.774977 53.774977 12.0 53.774977 53.774977 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 44.35603 13.974342 53.774977 35.64397 13.974342 53.774977 35.64397 13.025658 53.774977 44.35603 13.025658 53.774977 44.35603 13.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 180.411621 15.0 76.411621 107.588379 15.0 76.411621 107.588379 12.0 76.411621 180.411621 12.0 76.411621 180.411621 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 163.943466 14.321584 76.411621 124.056534 14.321584 76.411621 124.056534 12.678416 76.411621 163.943466 12.678416 76.411621 163.943466 14.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 157.774977 15.0 53.774977 130.225023 15.0 53.774977 130.225023 12.0 53.774977 157.774977 12.0 53.774977 157.774977 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 148.35603 13.974342 53.774977 139.64397 13.974342 53.774977 139.64397 13.025658 53.774977 148.35603 13.025658 53.774977 148.35603 13.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 76.411621 18.0 76.411621 3.588379 18.0 76.411621 3.588379 15.0 76.411621 76.411621 15.0 76.411621 76.411621 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 59.943466 17.321584 76.411621 20.056534 17.321584 76.411621 20.056534 15.678416 76.411621 59.943466 15.678416 76.411621 59.943466 17.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 53.774977 18.0 53.774977 26.225023 18.0 53.774977 26.225023 15.0 53.774977 53.774977 15.0 53.774977 53.774977 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 44.35603 16.974342 53.774977 35.64397 16.974342 53.774977 35.64397 16.025658 53.774977 44.35603 16.025658 53.774977 44.35603 16.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 180.411621 18.0 76.411621 107.588379 18.0 76.411621 107.588379 15.0 76.411621 180.411621 15.0 76.411621 180.411621 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 163.943466 17.321584 76.411621 124.056534 17.321584 76.411621 124.056534 15.678416 76.411621 163.943466 15.678416 76.411621 163.943466 17.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 157.774977 18.0 53.774977 130.225023 18.0 53.774977 130.225023 15.0 53.774977 157.774977 15.0 53.774977 157.774977 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 148.35603 16.974342 53.774977 139.64397 16.974342 53.774977 139.64397 16.025658 53.774977 148.35603 16.025658 53.774977 148.35603 16.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 76.411621 21.0 76.411621 3.588379 21.0 76.411621 3.588379 18.0 76.411621 76.411621 18.0 76.411621 76.411621 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 59.943466 20.321584 76.411621 20.056534 20.321584 76.411621 20.056534 18.678416 76.411621 59.943466 18.678416 76.411621 59.943466 20.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 53.774977 21.0 53.774977 26.225023 21.0 53.774977 26.225023 18.0 53.774977 53.774977 18.0 53.774977 53.774977 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 44.35603 19.974342 53.774977 35.64397 19.974342 53.774977 35.64397 19.025658 53.774977 44.35603 19.025658 53.774977 44.35603 19.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 180.411621 21.0 76.411621 107.588379 21.0 76.411621 107.588379 18.0 76.411621 180.411621 18.0 76.411621 180.411621 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 163.943466 20.321584 76.411621 124.056534 20.321584 76.411621 124.056534 18.678416 76.411621 163.943466 18.678416 76.411621 163.943466 20.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 157.774977 21.0 53.774977 130.225023 21.0 53.774977 130.225023 18.0 53.774977 157.774977 18.0 53.774977 157.774977 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 148.35603 19.974342 53.774977 139.64397 19.974342 53.774977 139.64397 19.025658 53.774977 148.35603 19.025658 53.774977 148.35603 19.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 76.411621 24.0 76.411621 3.588379 24.0 76.411621 3.588379 21.0 76.411621 76.411621 21.0 76.411621 76.411621 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 59.943466 23.321584 76.411621 20.056534 23.321584 76.411621 20.056534 21.678416 76.411621 59.943466 21.678416 76.411621 59.943466 23.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 53.774977 24.0 53.774977 26.225023 24.0 53.774977 26.225023 21.0 53.774977 53.774977 21.0 53.774977 53.774977 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 44.35603 22.974342 53.774977 35.64397 22.974342 53.774977 35.64397 22.025658 53.774977 44.35603 22.025658 53.774977 44.35603 22.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 180.411621 24.0 76.411621 107.588379 24.0 76.411621 107.588379 21.0 76.411621 180.411621 21.0 76.411621 180.411621 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 163.943466 23.321584 76.411621 124.056534 23.321584 76.411621 124.056534 21.678416 76.411621 163.943466 21.678416 76.411621 163.943466 23.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 157.774977 24.0 53.774977 130.225023 24.0 53.774977 130.225023 21.0 53.774977 157.774977 21.0 53.774977 157.774977 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 148.35603 22.974342 53.774977 139.64397 22.974342 53.774977 139.64397 22.025658 53.774977 148.35603 22.025658 53.774977 148.35603 22.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 76.411621 27.0 76.411621 3.588379 27.0 76.411621 3.588379 24.0 76.411621 76.411621 24.0 76.411621 76.411621 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 59.943466 26.321584 76.411621 20.056534 26.321584 76.411621 20.056534 24.678416 76.411621 59.943466 24.678416 76.411621 59.943466 26.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 53.774977 27.0 53.774977 26.225023 27.0 53.774977 26.225023 24.0 53.774977 53.774977 24.0 53.774977 53.774977 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 44.35603 25.974342 53.774977 35.64397 25.974342 53.774977 35.64397 25.025658 53.774977 44.35603 25.025658 53.774977 44.35603 25.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 180.411621 27.0 76.411621 107.588379 27.0 76.411621 107.588379 24.0 76.411621 180.411621 24.0 76.411621 180.411621 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 163.943466 26.321584 76.411621 124.056534 26.321584 76.411621 124.056534 24.678416 76.411621 163.943466 24.678416 76.411621 163.943466 26.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 157.774977 27.0 53.774977 130.225023 27.0 53.774977 130.225023 24.0 53.774977 157.774977 24.0 53.774977 157.774977 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 148.35603 25.974342 53.774977 139.64397 25.974342 53.774977 139.64397 25.025658 53.774977 148.35603 25.025658 53.774977 148.35603 25.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 76.411621 30.0 76.411621 3.588379 30.0 76.411621 3.588379 27.0 76.411621 76.411621 27.0 76.411621 76.411621 30.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 59.943466 29.321584 76.411621 20.056534 29.321584 76.411621 20.056534 27.678416 76.411621 59.943466 27.678416 76.411621 59.943466 29.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 53.774977 30.0 53.774977 26.225023 30.0 53.774977 26.225023 27.0 53.774977 53.774977 27.0 53.774977 53.774977 30.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 44.35603 28.974342 53.774977 35.64397 28.974342 53.774977 35.64397 28.025658 53.774977 44.35603 28.025658 53.774977 44.35603 28.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 180.411621 30.0 76.411621 107.588379 30.0 76.411621 107.588379 27.0 76.411621 180.411621 27.0 76.411621 180.411621 30.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 76.411621 163.943466 29.321584 76.411621 124.056534 29.321584 76.411621 124.056534 27.678416 76.411621 163.943466 27.678416 76.411621 163.943466 29.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 157.774977 30.0 53.774977 130.225023 30.0 53.774977 130.225023 27.0 53.774977 157.774977 27.0 53.774977 157.774977 30.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 53.774977 148.35603 28.974342 53.774977 139.64397 28.974342 53.774977 139.64397 28.025658 53.774977 148.35603 28.025658 53.774977 148.35603 28.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 76.411621 3.0 76.411621 76.411621 3.0 76.411621 76.411621 0.0 3.588379 76.411621 0.0 3.588379 76.411621 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 76.411621 2.321584 59.943466 76.411621 2.321584 59.943466 76.411621 0.678416 20.056534 76.411621 0.678416 20.056534 76.411621 2.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 53.774977 3.0 53.774977 53.774977 3.0 53.774977 53.774977 0.0 26.225023 53.774977 0.0 26.225023 53.774977 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 53.774977 1.974342 44.35603 53.774977 1.974342 44.35603 53.774977 1.025658 35.64397 53.774977 1.025658 35.64397 53.774977 1.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 180.411621 3.0 76.411621 180.411621 3.0 76.411621 180.411621 0.0 3.588379 180.411621 0.0 3.588379 180.411621 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 180.411621 2.321584 59.943466 180.411621 2.321584 59.943466 180.411621 0.678416 20.056534 180.411621 0.678416 20.056534 180.411621 2.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 157.774977 3.0 53.774977 157.774977 3.0 53.774977 157.774977 0.0 26.225023 157.774977 0.0 26.225023 157.774977 3.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 157.774977 1.974342 44.35603 157.774977 1.974342 44.35603 157.774977 1.025658 35.64397 157.774977 1.025658 35.64397 157.774977 1.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 76.411621 6.0 76.411621 76.411621 6.0 76.411621 76.411621 3.0 3.588379 76.411621 3.0 3.588379 76.411621 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 76.411621 5.321584 59.943466 76.411621 5.321584 59.943466 76.411621 3.678416 20.056534 76.411621 3.678416 20.056534 76.411621 5.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 53.774977 6.0 53.774977 53.774977 6.0 53.774977 53.774977 3.0 26.225023 53.774977 3.0 26.225023 53.774977 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 53.774977 4.974342 44.35603 53.774977 4.974342 44.35603 53.774977 4.025658 35.64397 53.774977 4.025658 35.64397 53.774977 4.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 180.411621 6.0 76.411621 180.411621 6.0 76.411621 180.411621 3.0 3.588379 180.411621 3.0 3.588379 180.411621 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 180.411621 5.321584 59.943466 180.411621 5.321584 59.943466 180.411621 3.678416 20.056534 180.411621 3.678416 20.056534 180.411621 5.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 157.774977 6.0 53.774977 157.774977 6.0 53.774977 157.774977 3.0 26.225023 157.774977 3.0 26.225023 157.774977 6.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 157.774977 4.974342 44.35603 157.774977 4.974342 44.35603 157.774977 4.025658 35.64397 157.774977 4.025658 35.64397 157.774977 4.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 76.411621 9.0 76.411621 76.411621 9.0 76.411621 76.411621 6.0 3.588379 76.411621 6.0 3.588379 76.411621 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 76.411621 8.321584 59.943466 76.411621 8.321584 59.943466 76.411621 6.678416 20.056534 76.411621 6.678416 20.056534 76.411621 8.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 53.774977 9.0 53.774977 53.774977 9.0 53.774977 53.774977 6.0 26.225023 53.774977 6.0 26.225023 53.774977 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 53.774977 7.974342 44.35603 53.774977 7.974342 44.35603 53.774977 7.025658 35.64397 53.774977 7.025658 35.64397 53.774977 7.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 180.411621 9.0 76.411621 180.411621 9.0 76.411621 180.411621 6.0 3.588379 180.411621 6.0 3.588379 180.411621 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 180.411621 8.321584 59.943466 180.411621 8.321584 59.943466 180.411621 6.678416 20.056534 180.411621 6.678416 20.056534 180.411621 8.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 157.774977 9.0 53.774977 157.774977 9.0 53.774977 157.774977 6.0 26.225023 157.774977 6.0 26.225023 157.774977 9.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 157.774977 7.974342 44.35603 157.774977 7.974342 44.35603 157.774977 7.025658 35.64397 157.774977 7.025658 35.64397 157.774977 7.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 76.411621 12.0 76.411621 76.411621 12.0 76.411621 76.411621 9.0 3.588379 76.411621 9.0 3.588379 76.411621 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 76.411621 11.321584 59.943466 76.411621 11.321584 59.943466 76.411621 9.678416 20.056534 76.411621 9.678416 20.056534 76.411621 11.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 53.774977 12.0 53.774977 53.774977 12.0 53.774977 53.774977 9.0 26.225023 53.774977 9.0 26.225023 53.774977 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 53.774977 10.974342 44.35603 53.774977 10.974342 44.35603 53.774977 10.025658 35.64397 53.774977 10.025658 35.64397 53.774977 10.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 180.411621 12.0 76.411621 180.411621 12.0 76.411621 180.411621 9.0 3.588379 180.411621 9.0 3.588379 180.411621 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 180.411621 11.321584 59.943466 180.411621 11.321584 59.943466 180.411621 9.678416 20.056534 180.411621 9.678416 20.056534 180.411621 11.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 157.774977 12.0 53.774977 157.774977 12.0 53.774977 157.774977 9.0 26.225023 157.774977 9.0 26.225023 157.774977 12.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 157.774977 10.974342 44.35603 157.774977 10.974342 44.35603 157.774977 10.025658 35.64397 157.774977 10.025658 35.64397 157.774977 10.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 76.411621 15.0 76.411621 76.411621 15.0 76.411621 76.411621 12.0 3.588379 76.411621 12.0 3.588379 76.411621 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 76.411621 14.321584 59.943466 76.411621 14.321584 59.943466 76.411621 12.678416 20.056534 76.411621 12.678416 20.056534 76.411621 14.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 53.774977 15.0 53.774977 53.774977 15.0 53.774977 53.774977 12.0 26.225023 53.774977 12.0 26.225023 53.774977 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 53.774977 13.974342 44.35603 53.774977 13.974342 44.35603 53.774977 13.025658 35.64397 53.774977 13.025658 35.64397 53.774977 13.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 180.411621 15.0 76.411621 180.411621 15.0 76.411621 180.411621 12.0 3.588379 180.411621 12.0 3.588379 180.411621 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 180.411621 14.321584 59.943466 180.411621 14.321584 59.943466 180.411621 12.678416 20.056534 180.411621 12.678416 20.056534 180.411621 14.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 157.774977 15.0 53.774977 157.774977 15.0 53.774977 157.774977 12.0 26.225023 157.774977 12.0 26.225023 157.774977 15.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 157.774977 13.974342 44.35603 157.774977 13.974342 44.35603 157.774977 13.025658 35.64397 157.774977 13.025658 35.64397 157.774977 13.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 76.411621 18.0 76.411621 76.411621 18.0 76.411621 76.411621 15.0 3.588379 76.411621 15.0 3.588379 76.411621 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 76.411621 17.321584 59.943466 76.411621 17.321584 59.943466 76.411621 15.678416 20.056534 76.411621 15.678416 20.056534 76.411621 17.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 53.774977 18.0 53.774977 53.774977 18.0 53.774977 53.774977 15.0 26.225023 53.774977 15.0 26.225023 53.774977 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 53.774977 16.974342 44.35603 53.774977 16.974342 44.35603 53.774977 16.025658 35.64397 53.774977 16.025658 35.64397 53.774977 16.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 180.411621 18.0 76.411621 180.411621 18.0 76.411621 180.411621 15.0 3.588379 180.411621 15.0 3.588379 180.411621 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 180.411621 17.321584 59.943466 180.411621 17.321584 59.943466 180.411621 15.678416 20.056534 180.411621 15.678416 20.056534 180.411621 17.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 157.774977 18.0 53.774977 157.774977 18.0 53.774977 157.774977 15.0 26.225023 157.774977 15.0 26.225023 157.774977 18.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 157.774977 16.974342 44.35603 157.774977 16.974342 44.35603 157.774977 16.025658 35.64397 157.774977 16.025658 35.64397 157.774977 16.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 76.411621 21.0 76.411621 76.411621 21.0 76.411621 76.411621 18.0 3.588379 76.411621 18.0 3.588379 76.411621 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 76.411621 20.321584 59.943466 76.411621 20.321584 59.943466 76.411621 18.678416 20.056534 76.411621 18.678416 20.056534 76.411621 20.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 53.774977 21.0 53.774977 53.774977 21.0 53.774977 53.774977 18.0 26.225023 53.774977 18.0 26.225023 53.774977 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 53.774977 19.974342 44.35603 53.774977 19.974342 44.35603 53.774977 19.025658 35.64397 53.774977 19.025658 35.64397 53.774977 19.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 180.411621 21.0 76.411621 180.411621 21.0 76.411621 180.411621 18.0 3.588379 180.411621 18.0 3.588379 180.411621 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 180.411621 20.321584 59.943466 180.411621 20.321584 59.943466 180.411621 18.678416 20.056534 180.411621 18.678416 20.056534 180.411621 20.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 157.774977 21.0 53.774977 157.774977 21.0 53.774977 157.774977 18.0 26.225023 157.774977 18.0 26.225023 157.774977 21.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 157.774977 19.974342 44.35603 157.774977 19.974342 44.35603 157.774977 19.025658 35.64397 157.774977 19.025658 35.64397 157.774977 19.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 76.411621 24.0 76.411621 76.411621 24.0 76.411621 76.411621 21.0 3.588379 76.411621 21.0 3.588379 76.411621 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 76.411621 23.321584 59.943466 76.411621 23.321584 59.943466 76.411621 21.678416 20.056534 76.411621 21.678416 20.056534 76.411621 23.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 53.774977 24.0 53.774977 53.774977 24.0 53.774977 53.774977 21.0 26.225023 53.774977 21.0 26.225023 53.774977 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 53.774977 22.974342 44.35603 53.774977 22.974342 44.35603 53.774977 22.025658 35.64397 53.774977 22.025658 35.64397 53.774977 22.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 180.411621 24.0 76.411621 180.411621 24.0 76.411621 180.411621 21.0 3.588379 180.411621 21.0 3.588379 180.411621 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 180.411621 23.321584 59.943466 180.411621 23.321584 59.943466 180.411621 21.678416 20.056534 180.411621 21.678416 20.056534 180.411621 23.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 157.774977 24.0 53.774977 157.774977 24.0 53.774977 157.774977 21.0 26.225023 157.774977 21.0 26.225023 157.774977 24.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 157.774977 22.974342 44.35603 157.774977 22.974342 44.35603 157.774977 22.025658 35.64397 157.774977 22.025658 35.64397 157.774977 22.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 76.411621 27.0 76.411621 76.411621 27.0 76.411621 76.411621 24.0 3.588379 76.411621 24.0 3.588379 76.411621 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 76.411621 26.321584 59.943466 76.411621 26.321584 59.943466 76.411621 24.678416 20.056534 76.411621 24.678416 20.056534 76.411621 26.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 53.774977 27.0 53.774977 53.774977 27.0 53.774977 53.774977 24.0 26.225023 53.774977 24.0 26.225023 53.774977 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 53.774977 25.974342 44.35603 53.774977 25.974342 44.35603 53.774977 25.025658 35.64397 53.774977 25.025658 35.64397 53.774977 25.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 180.411621 27.0 76.411621 180.411621 27.0 76.411621 180.411621 24.0 3.588379 180.411621 24.0 3.588379 180.411621 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 180.411621 26.321584 59.943466 180.411621 26.321584 59.943466 180.411621 24.678416 20.056534 180.411621 24.678416 20.056534 180.411621 26.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 157.774977 27.0 53.774977 157.774977 27.0 53.774977 157.774977 24.0 26.225023 157.774977 24.0 26.225023 157.774977 27.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 157.774977 25.974342 44.35603 157.774977 25.974342 44.35603 157.774977 25.025658 35.64397 157.774977 25.025658 35.64397 157.774977 25.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 76.411621 30.0 76.411621 76.411621 30.0 76.411621 76.411621 27.0 3.588379 76.411621 27.0 3.588379 76.411621 30.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 76.411621 29.321584 59.943466 76.411621 29.321584 59.943466 76.411621 27.678416 20.056534 76.411621 27.678416 20.056534 76.411621 29.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 53.774977 30.0 53.774977 53.774977 30.0 53.774977 53.774977 27.0 26.225023 53.774977 27.0 26.225023 53.774977 30.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 53.774977 28.974342 44.35603 53.774977 28.974342 44.35603 53.774977 28.025658 35.64397 53.774977 28.025658 35.64397 53.774977 28.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 180.411621 30.0 76.411621 180.411621 30.0 76.411621 180.411621 27.0 3.588379 180.411621 27.0 3.588379 180.411621 30.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 20.056534 180.411621 29.321584 59.943466 180.411621 29.321584 59.943466 180.411621 27.678416 20.056534 180.411621 27.678416 20.056534 180.411621 29.321584 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:WallSurface>
<gml:name> Facade_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:CompositeSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 26.225023 157.774977 30.0 53.774977 157.774977 30.0 53.774977 157.774977 27.0 26.225023 157.774977 27.0 26.225023 157.774977 30.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:CompositeSurface>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
<bldg:opening>
<bldg:Window>
<gml:name> Window_80 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 35.64397 157.774977 28.974342 44.35603 157.774977 28.974342 44.35603 157.774977 28.025658 35.64397 157.774977 28.025658 35.64397 157.774977 28.974342 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:Window>
</bldg:opening>
</bldg:WallSurface>
</bldg:boundedBy>
<bldg:boundedBy>
<bldg:RoofSurface>
<gml:name> Roof_2_1 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 180.411621 30.0 76.411621 180.411621 30.0 76.411621 144.0 30.0 53.774977 144.0 30.0 53.774977 157.774977 30.0 26.225023 157.774977 30.0 26.225023 144.0 30.0 3.588379 144.0 30.0 3.588379 180.411621 30.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:RoofSurface>
<bldg:RoofSurface>
<gml:name> Roof_2_2 </gml:name>
<bldg:lod3MultiSurface>
<gml:MultiSurface>
<gml:surfaceMember>
<gml:Polygon>
<gml:exterior>
<gml:LinearRing>
<gml:posList srsDimension="3"> 3.588379 107.588379 30.0 3.588379 144.0 30.0 26.225023 144.0 30.0 26.225023 130.225023 30.0 53.774977 130.225023 30.0 53.774977 144.0 30.0 76.411621 144.0 30.0 76.411621 107.588379 30.0 3.588379 107.588379 30.0 </gml:posList>
</gml:LinearRing>
</gml:exterior>
</gml:Polygon>
</gml:surfaceMember>
</gml:MultiSurface>
</bldg:lod3MultiSurface>
</bldg:RoofSurface>
</bldg:boundedBy>
<bldg:lod3Solid>
<gml:Solid>
<gml:exterior>
<gml:CompositeSurface>
</gml:CompositeSurface>
</gml:exterior>
</gml:Solid>
</bldg:lod3Solid>
</bldg:Building>
</cityObjectMember>
</CityModel>
