# coding=utf-8
"""
Create shapefile from Rhino
"""
from __future__ import division
import geopandas as gpd
from shapely.geometry import Polygon
from geopandas import GeoDataFrame as gdf


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT ??"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


dataframe_with_gis_info = gdf.from_file(r'F:\cea-reference-case\reference-case-zug\baseline\inputs\building-geometry/district.shp')



# Create an empty geopandas GeoDataFrame
district = gpd.GeoDataFrame()

# Create columns called 'geometry', 'height_ag', and 'height_bg" to the GeoDataFrame
district['NAME'] = None
district['FLOORS_AG'] = None
district['FLOORS_BG'] = None
district['HEIGHT_AG'] = None
district['HEIGHT_BG'] = None

Coordinate_0 = [ (-90.3145561862,-195.926410910), (-114.255966219,-261.704894365), (-174.664777555,-239.717885151), (-150.723367522,-173.939401696) ]
Coordinate_1 = [ (-124.516570519,-289.895672988), (-148.457980552,-355.674156443), (-208.866791888,-333.687147229), (-184.925381855,-267.908663774) ]
Coordinate_2 = [ (-158.718584851,-383.864935067), (-182.659994884,-449.643418522), (-243.068806220,-427.656409308), (-219.127396188,-361.877925853) ]
Coordinate_3 = [ (-192.920599184,-477.834197145), (-216.862009217,-543.612680600), (-277.270820553,-521.625671387), (-253.329410520,-455.847187932) ]
Coordinate_4 = [ (-150.081803932,-67.7551344984), (-174.023213965,-133.533617953), (-234.432025301,-111.546608740), (-210.490615268,-45.7681252846) ]
Coordinate_5 = [ (-184.283818265,-161.724396577), (-208.225228298,-227.502880032), (-268.634039634,-205.515870818), (-244.692629601,-139.737387363) ]
Coordinate_6 = [ (-218.485832597,-255.693658656), (-242.427242630,-321.472142111), (-302.836053966,-299.485132897), (-278.894643934,-233.706649442) ]
Coordinate_7 = [ (-252.687846930,-349.662920734), (-276.629256963,-415.441404189), (-337.038068299,-393.454394975), (-313.096658266,-327.675911520) ]
Coordinate_8 = [ (-286.889861262,-443.632182813), (-310.831271295,-509.410666268), (-371.240082632,-487.423657054), (-347.298672599,-421.645173599) ]
Coordinate_9 = [ (-321.091875595,-537.601444891), (-345.033285628,-603.379928346), (-405.442096964,-581.392919133), (-381.500686931,-515.614435678) ]
Coordinate_10 = [ (-209.849051678,60.4161419127), (-233.790461711,-5.36234154228), (-294.199273047,16.6246676715), (-270.257863014,82.4031511265) ]
Coordinate_11 = [ (-244.051066011,-33.5531201659), (-267.992476044,-99.3316036209), (-328.401287380,-77.3445944071), (-304.459877347,-11.5661109521) ]
Coordinate_12 = [ (-278.253080343,-127.522382244), (-302.194490376,-193.300865699), (-362.603301712,-171.313856486), (-338.661891680,-105.535373031) ]
Coordinate_13 = [ (-312.455094676,-221.491644323), (-336.396504709,-287.270127778), (-396.805316045,-265.283118564), (-372.863906012,-199.504635109) ]
Coordinate_14 = [ (-346.657109009,-315.460906402), (-370.598519041,-381.239389857), (-431.007330378,-359.252380643), (-407.065920345,-293.473897188) ]
Coordinate_15 = [ (-380.859123341,-409.430168480), (-404.800533374,-475.208651935), (-465.209344710,-453.221642721), (-441.267934677,-387.443159266) ]
Coordinate_16 = [ (-415.061137674,-503.399430559), (-439.002547706,-569.177914014), (-499.411359043,-547.190904800), (-475.469949010,-481.412421345) ]
Coordinate_17 = [ (-449.263152006,-597.368692637), (-473.204562039,-663.147176092), (-533.613373375,-641.160166879), (-509.671963342,-575.381683424) ]
Coordinate_18 = [ (-303.818313757,94.6181562453), (-327.759723790,28.8396727903), (-388.168535126,50.8266820041), (-364.227125093,116.605165459) ]
Coordinate_19 = [ (-338.020328089,0.648894166708), (-361.961738122,-65.1295892883), (-422.370549458,-43.1425800745), (-398.429139426,22.6359033805) ]
Coordinate_20 = [ (-372.222342422,-93.3203679119), (-396.163752455,-159.098851367), (-456.572563791,-137.111842153), (-432.631153758,-71.3333586981) ]
Coordinate_21 = [ (-406.424356755,-187.289629990), (-430.365766787,-253.068113445), (-490.774578124,-231.081104232), (-466.833168091,-165.302620777) ]
Coordinate_22 = [ (-440.626371087,-281.258892069), (-464.567781120,-347.037375524), (-524.976592456,-325.050366310), (-501.035182423,-259.271882855) ]
Coordinate_23 = [ (-474.828385420,-375.228154148), (-498.769795452,-441.006637603), (-559.178606789,-419.019628389), (-535.237196756,-353.241144934) ]
Coordinate_24 = [ (-509.030399752,-469.197416226), (-532.971809785,-534.975899681), (-593.380621121,-512.988890467), (-569.439211088,-447.210407012) ]
Coordinate_25 = [ (-543.232414085,-563.166678305), (-567.173824118,-628.945161760), (-627.582635454,-606.958152546), (-603.641225421,-541.179669091) ]
Coordinate_26 = [ (-397.787575835,128.820170578), (-421.728985868,63.0416871229), (-482.137797204,85.0286963366), (-458.196387172,150.807179792) ]
Coordinate_27 = [ (-431.989590168,34.8509084993), (-455.931000201,-30.9275749557), (-516.339811537,-8.94056574195), (-492.398401504,56.8379177131) ]
Coordinate_28 = [ (-466.191604501,-59.1183535793), (-490.133014533,-124.896837034), (-550.541825870,-102.909827821), (-526.600415837,-37.1313443655) ]
Coordinate_29 = [ (-500.393618833,-153.087615658), (-524.335028866,-218.866099113), (-584.743840202,-196.879089899), (-560.802430169,-131.100606444) ]
Coordinate_30 = [ (-534.595633166,-247.056877736), (-558.537043198,-312.835361192), (-618.945854535,-290.848351978), (-595.004444502,-225.069868523) ]
Coordinate_31 = [ (-568.797647498,-341.026139815), (-592.739057531,-406.804623270), (-653.147868867,-384.817614056), (-629.206458834,-319.039130601) ]
Coordinate_32 = [ (-602.999661831,-434.995401894), (-626.941071864,-500.773885349), (-687.349883200,-478.786876135), (-663.408473167,-413.008392680) ]
Coordinate_33 = [ (-637.201676163,-528.964663972), (-661.143086196,-594.743147427), (-721.551897532,-572.756138213), (-697.610487500,-506.977654758) ]
Coordinate_34 = [ (-491.756837914,163.022184910), (-515.698247947,97.2437014554), (-576.107059283,119.230710669), (-552.165649250,185.009194124) ]
Coordinate_35 = [ (-525.958852247,69.0529228318), (-549.900262279,3.27443937683), (-610.309073616,25.2614485906), (-586.367663583,91.0399320456) ]
Coordinate_36 = [ (-560.160866579,-24.9163392467), (-584.102276612,-90.6948227018), (-644.511087948,-68.7078134880), (-620.569677915,-2.92933003296) ]
Coordinate_37 = [ (-594.362880912,-118.885601325), (-618.304290945,-184.664084780), (-678.713102281,-162.677075567), (-654.771692248,-96.8985921115) ]
Coordinate_38 = [ (-628.564895244,-212.854863404), (-652.506305277,-278.633346859), (-712.915116613,-256.646337645), (-688.973706581,-190.867854190) ]
Coordinate_39 = [ (-662.766909577,-306.824125483), (-686.708319610,-372.602608938), (-747.117130946,-350.615599724), (-723.175720913,-284.837116269) ]
Coordinate_40 = [ (-696.968923909,-400.793387561), (-720.910333942,-466.571871016), (-781.319145278,-444.584861802), (-757.377735246,-378.806378347) ]
Coordinate_41 = [ (-731.170938242,-494.762649640), (-755.112348275,-560.541133095), (-815.521159611,-538.554123881), (-791.579749578,-472.775640426) ]
Coordinate_42 = [ (-619.928114325,103.254937164), (-643.869524358,37.4764537094), (-704.278335694,59.4634629232), (-680.336925661,125.241946378) ]
Coordinate_43 = [ (-654.130128658,9.28567508582), (-678.071538691,-56.4928083692), (-738.480350027,-34.5057991554), (-714.538939994,31.2726842996) ]
Coordinate_44 = [ (-688.332142990,-84.6835869928), (-712.273553023,-150.462070448), (-772.682364359,-128.475061234), (-748.740954327,-62.6965777790) ]
Coordinate_45 = [ (-722.534157323,-178.652849071), (-746.475567356,-244.431332526), (-806.884378692,-222.444323313), (-782.942968659,-156.665839858) ]
Coordinate_46 = [ (-756.736171655,-272.622111150), (-780.677581688,-338.400594605), (-841.086393024,-316.413585391), (-817.144982992,-250.635101936) ]
Coordinate_47 = [ (-790.938185988,-366.591373229), (-814.879596021,-432.369856684), (-875.288407357,-410.382847470), (-851.346997324,-344.604364015) ]
Coordinate_48 = [ (-748.099390736,43.4876894184), (-772.040800769,-22.2907940366), (-832.449612105,-0.303784822836), (-808.508202073,65.4746986322) ]
Coordinate_49 = [ (-782.301405069,-50.4815726602), (-806.242815102,-116.260056115), (-866.651626438,-94.2730469014), (-842.710216405,-28.4945634464) ]
Coordinate_50 = [ (-816.503419401,-144.450834739), (-840.444829434,-210.229318194), (-900.853640770,-188.242308980), (-876.912230738,-122.463825525) ]
Coordinate_51 = [ (-850.705433734,-238.420096817), (-874.646843767,-304.198580272), (-935.055655103,-282.211571059), (-911.114245070,-216.433087604) ]
Poly_0 = Polygon( Coordinate_0 )
Poly_1 = Polygon( Coordinate_1 )
Poly_2 = Polygon( Coordinate_2 )
Poly_3 = Polygon( Coordinate_3 )
Poly_4 = Polygon( Coordinate_4 )
Poly_5 = Polygon( Coordinate_5 )
Poly_6 = Polygon( Coordinate_6 )
Poly_7 = Polygon( Coordinate_7 )
Poly_8 = Polygon( Coordinate_8 )
Poly_9 = Polygon( Coordinate_9 )
Poly_10 = Polygon( Coordinate_10 )
Poly_11 = Polygon( Coordinate_11 )
Poly_12 = Polygon( Coordinate_12 )
Poly_13 = Polygon( Coordinate_13 )
Poly_14 = Polygon( Coordinate_14 )
Poly_15 = Polygon( Coordinate_15 )
Poly_16 = Polygon( Coordinate_16 )
Poly_17 = Polygon( Coordinate_17 )
Poly_18 = Polygon( Coordinate_18 )
Poly_19 = Polygon( Coordinate_19 )
Poly_20 = Polygon( Coordinate_20 )
Poly_21 = Polygon( Coordinate_21 )
Poly_22 = Polygon( Coordinate_22 )
Poly_23 = Polygon( Coordinate_23 )
Poly_24 = Polygon( Coordinate_24 )
Poly_25 = Polygon( Coordinate_25 )
Poly_26 = Polygon( Coordinate_26 )
Poly_27 = Polygon( Coordinate_27 )
Poly_28 = Polygon( Coordinate_28 )
Poly_29 = Polygon( Coordinate_29 )
Poly_30 = Polygon( Coordinate_30 )
Poly_31 = Polygon( Coordinate_31 )
Poly_32 = Polygon( Coordinate_32 )
Poly_33 = Polygon( Coordinate_33 )
Poly_34 = Polygon( Coordinate_34 )
Poly_35 = Polygon( Coordinate_35 )
Poly_36 = Polygon( Coordinate_36 )
Poly_37 = Polygon( Coordinate_37 )
Poly_38 = Polygon( Coordinate_38 )
Poly_39 = Polygon( Coordinate_39 )
Poly_40 = Polygon( Coordinate_40 )
Poly_41 = Polygon( Coordinate_41 )
Poly_42 = Polygon( Coordinate_42 )
Poly_43 = Polygon( Coordinate_43 )
Poly_44 = Polygon( Coordinate_44 )
Poly_45 = Polygon( Coordinate_45 )
Poly_46 = Polygon( Coordinate_46 )
Poly_47 = Polygon( Coordinate_47 )
Poly_48 = Polygon( Coordinate_48 )
Poly_49 = Polygon( Coordinate_49 )
Poly_50 = Polygon( Coordinate_50 )
Poly_51 = Polygon( Coordinate_51 )
district.loc[ 0 , 'NAME' ] = 'Bldg_0'
district.loc[ 1 , 'NAME' ] = 'Bldg_1'
district.loc[ 2 , 'NAME' ] = 'Bldg_2'
district.loc[ 3 , 'NAME' ] = 'Bldg_3'
district.loc[ 4 , 'NAME' ] = 'Bldg_4'
district.loc[ 5 , 'NAME' ] = 'Bldg_5'
district.loc[ 6 , 'NAME' ] = 'Bldg_6'
district.loc[ 7 , 'NAME' ] = 'Bldg_7'
district.loc[ 8 , 'NAME' ] = 'Bldg_8'
district.loc[ 9 , 'NAME' ] = 'Bldg_9'
district.loc[ 10 , 'NAME' ] = 'Bldg_10'
district.loc[ 11 , 'NAME' ] = 'Bldg_11'
district.loc[ 12 , 'NAME' ] = 'Bldg_12'
district.loc[ 13 , 'NAME' ] = 'Bldg_13'
district.loc[ 14 , 'NAME' ] = 'Bldg_14'
district.loc[ 15 , 'NAME' ] = 'Bldg_15'
district.loc[ 16 , 'NAME' ] = 'Bldg_16'
district.loc[ 17 , 'NAME' ] = 'Bldg_17'
district.loc[ 18 , 'NAME' ] = 'Bldg_18'
district.loc[ 19 , 'NAME' ] = 'Bldg_19'
district.loc[ 20 , 'NAME' ] = 'Bldg_20'
district.loc[ 21 , 'NAME' ] = 'Bldg_21'
district.loc[ 22 , 'NAME' ] = 'Bldg_22'
district.loc[ 23 , 'NAME' ] = 'Bldg_23'
district.loc[ 24 , 'NAME' ] = 'Bldg_24'
district.loc[ 25 , 'NAME' ] = 'Bldg_25'
district.loc[ 26 , 'NAME' ] = 'Bldg_26'
district.loc[ 27 , 'NAME' ] = 'Bldg_27'
district.loc[ 28 , 'NAME' ] = 'Bldg_28'
district.loc[ 29 , 'NAME' ] = 'Bldg_29'
district.loc[ 30 , 'NAME' ] = 'Bldg_30'
district.loc[ 31 , 'NAME' ] = 'Bldg_31'
district.loc[ 32 , 'NAME' ] = 'Bldg_32'
district.loc[ 33 , 'NAME' ] = 'Bldg_33'
district.loc[ 34 , 'NAME' ] = 'Bldg_34'
district.loc[ 35 , 'NAME' ] = 'Bldg_35'
district.loc[ 36 , 'NAME' ] = 'Bldg_36'
district.loc[ 37 , 'NAME' ] = 'Bldg_37'
district.loc[ 38 , 'NAME' ] = 'Bldg_38'
district.loc[ 39 , 'NAME' ] = 'Bldg_39'
district.loc[ 40 , 'NAME' ] = 'Bldg_40'
district.loc[ 41 , 'NAME' ] = 'Bldg_41'
district.loc[ 42 , 'NAME' ] = 'Bldg_42'
district.loc[ 43 , 'NAME' ] = 'Bldg_43'
district.loc[ 44 , 'NAME' ] = 'Bldg_44'
district.loc[ 45 , 'NAME' ] = 'Bldg_45'
district.loc[ 46 , 'NAME' ] = 'Bldg_46'
district.loc[ 47 , 'NAME' ] = 'Bldg_47'
district.loc[ 48 , 'NAME' ] = 'Bldg_48'
district.loc[ 49 , 'NAME' ] = 'Bldg_49'
district.loc[ 50 , 'NAME' ] = 'Bldg_50'
district.loc[ 51 , 'NAME' ] = 'Bldg_51'
district.loc[ 0 , 'geometry' ] = Poly_0
district.loc[ 1 , 'geometry' ] = Poly_1
district.loc[ 2 , 'geometry' ] = Poly_2
district.loc[ 3 , 'geometry' ] = Poly_3
district.loc[ 4 , 'geometry' ] = Poly_4
district.loc[ 5 , 'geometry' ] = Poly_5
district.loc[ 6 , 'geometry' ] = Poly_6
district.loc[ 7 , 'geometry' ] = Poly_7
district.loc[ 8 , 'geometry' ] = Poly_8
district.loc[ 9 , 'geometry' ] = Poly_9
district.loc[ 10 , 'geometry' ] = Poly_10
district.loc[ 11 , 'geometry' ] = Poly_11
district.loc[ 12 , 'geometry' ] = Poly_12
district.loc[ 13 , 'geometry' ] = Poly_13
district.loc[ 14 , 'geometry' ] = Poly_14
district.loc[ 15 , 'geometry' ] = Poly_15
district.loc[ 16 , 'geometry' ] = Poly_16
district.loc[ 17 , 'geometry' ] = Poly_17
district.loc[ 18 , 'geometry' ] = Poly_18
district.loc[ 19 , 'geometry' ] = Poly_19
district.loc[ 20 , 'geometry' ] = Poly_20
district.loc[ 21 , 'geometry' ] = Poly_21
district.loc[ 22 , 'geometry' ] = Poly_22
district.loc[ 23 , 'geometry' ] = Poly_23
district.loc[ 24 , 'geometry' ] = Poly_24
district.loc[ 25 , 'geometry' ] = Poly_25
district.loc[ 26 , 'geometry' ] = Poly_26
district.loc[ 27 , 'geometry' ] = Poly_27
district.loc[ 28 , 'geometry' ] = Poly_28
district.loc[ 29 , 'geometry' ] = Poly_29
district.loc[ 30 , 'geometry' ] = Poly_30
district.loc[ 31 , 'geometry' ] = Poly_31
district.loc[ 32 , 'geometry' ] = Poly_32
district.loc[ 33 , 'geometry' ] = Poly_33
district.loc[ 34 , 'geometry' ] = Poly_34
district.loc[ 35 , 'geometry' ] = Poly_35
district.loc[ 36 , 'geometry' ] = Poly_36
district.loc[ 37 , 'geometry' ] = Poly_37
district.loc[ 38 , 'geometry' ] = Poly_38
district.loc[ 39 , 'geometry' ] = Poly_39
district.loc[ 40 , 'geometry' ] = Poly_40
district.loc[ 41 , 'geometry' ] = Poly_41
district.loc[ 42 , 'geometry' ] = Poly_42
district.loc[ 43 , 'geometry' ] = Poly_43
district.loc[ 44 , 'geometry' ] = Poly_44
district.loc[ 45 , 'geometry' ] = Poly_45
district.loc[ 46 , 'geometry' ] = Poly_46
district.loc[ 47 , 'geometry' ] = Poly_47
district.loc[ 48 , 'geometry' ] = Poly_48
district.loc[ 49 , 'geometry' ] = Poly_49
district.loc[ 50 , 'geometry' ] = Poly_50
district.loc[ 51 , 'geometry' ] = Poly_51
district.loc[ 0 , 'HEIGHT_AG' ] = '33.0'
district.loc[ 1 , 'HEIGHT_AG' ] = '36.0'
district.loc[ 2 , 'HEIGHT_AG' ] = '36.0'
district.loc[ 3 , 'HEIGHT_AG' ] = '33.0'
district.loc[ 4 , 'HEIGHT_AG' ] = '36.0'
district.loc[ 5 , 'HEIGHT_AG' ] = '39.0'
district.loc[ 6 , 'HEIGHT_AG' ] = '42.0'
district.loc[ 7 , 'HEIGHT_AG' ] = '42.0'
district.loc[ 8 , 'HEIGHT_AG' ] = '39.0'
district.loc[ 9 , 'HEIGHT_AG' ] = '36.0'
district.loc[ 10 , 'HEIGHT_AG' ] = '33.0'
district.loc[ 11 , 'HEIGHT_AG' ] = '39.0'
district.loc[ 12 , 'HEIGHT_AG' ] = '48.0'
district.loc[ 13 , 'HEIGHT_AG' ] = '51.0'
district.loc[ 14 , 'HEIGHT_AG' ] = '51.0'
district.loc[ 15 , 'HEIGHT_AG' ] = '48.0'
district.loc[ 16 , 'HEIGHT_AG' ] = '39.0'
district.loc[ 17 , 'HEIGHT_AG' ] = '33.0'
district.loc[ 18 , 'HEIGHT_AG' ] = '36.0'
district.loc[ 19 , 'HEIGHT_AG' ] = '42.0'
district.loc[ 20 , 'HEIGHT_AG' ] = '51.0'
district.loc[ 21 , 'HEIGHT_AG' ] = '57.0'
district.loc[ 22 , 'HEIGHT_AG' ] = '57.0'
district.loc[ 23 , 'HEIGHT_AG' ] = '51.0'
district.loc[ 24 , 'HEIGHT_AG' ] = '42.0'
district.loc[ 25 , 'HEIGHT_AG' ] = '36.0'
district.loc[ 26 , 'HEIGHT_AG' ] = '36.0'
district.loc[ 27 , 'HEIGHT_AG' ] = '42.0'
district.loc[ 28 , 'HEIGHT_AG' ] = '51.0'
district.loc[ 29 , 'HEIGHT_AG' ] = '57.0'
district.loc[ 30 , 'HEIGHT_AG' ] = '57.0'
district.loc[ 31 , 'HEIGHT_AG' ] = '51.0'
district.loc[ 32 , 'HEIGHT_AG' ] = '42.0'
district.loc[ 33 , 'HEIGHT_AG' ] = '36.0'
district.loc[ 34 , 'HEIGHT_AG' ] = '33.0'
district.loc[ 35 , 'HEIGHT_AG' ] = '39.0'
district.loc[ 36 , 'HEIGHT_AG' ] = '48.0'
district.loc[ 37 , 'HEIGHT_AG' ] = '51.0'
district.loc[ 38 , 'HEIGHT_AG' ] = '51.0'
district.loc[ 39 , 'HEIGHT_AG' ] = '48.0'
district.loc[ 40 , 'HEIGHT_AG' ] = '39.0'
district.loc[ 41 , 'HEIGHT_AG' ] = '33.0'
district.loc[ 42 , 'HEIGHT_AG' ] = '36.0'
district.loc[ 43 , 'HEIGHT_AG' ] = '39.0'
district.loc[ 44 , 'HEIGHT_AG' ] = '42.0'
district.loc[ 45 , 'HEIGHT_AG' ] = '42.0'
district.loc[ 46 , 'HEIGHT_AG' ] = '39.0'
district.loc[ 47 , 'HEIGHT_AG' ] = '36.0'
district.loc[ 48 , 'HEIGHT_AG' ] = '33.0'
district.loc[ 49 , 'HEIGHT_AG' ] = '36.0'
district.loc[ 50 , 'HEIGHT_AG' ] = '36.0'
district.loc[ 51 , 'HEIGHT_AG' ] = '33.0'
district.loc[ 0 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 1 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 2 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 3 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 4 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 5 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 6 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 7 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 8 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 9 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 10 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 11 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 12 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 13 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 14 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 15 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 16 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 17 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 18 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 19 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 20 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 21 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 22 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 23 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 24 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 25 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 26 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 27 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 28 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 29 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 30 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 31 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 32 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 33 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 34 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 35 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 36 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 37 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 38 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 39 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 40 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 41 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 42 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 43 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 44 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 45 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 46 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 47 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 48 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 49 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 50 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 51 , 'HEIGHT_BG' ] = '0.0'
district.loc[ 0 , 'FLOORS_AG' ] = '11.0'
district.loc[ 1 , 'FLOORS_AG' ] = '12.0'
district.loc[ 2 , 'FLOORS_AG' ] = '12.0'
district.loc[ 3 , 'FLOORS_AG' ] = '11.0'
district.loc[ 4 , 'FLOORS_AG' ] = '12.0'
district.loc[ 5 , 'FLOORS_AG' ] = '13.0'
district.loc[ 6 , 'FLOORS_AG' ] = '14.0'
district.loc[ 7 , 'FLOORS_AG' ] = '14.0'
district.loc[ 8 , 'FLOORS_AG' ] = '13.0'
district.loc[ 9 , 'FLOORS_AG' ] = '12.0'
district.loc[ 10 , 'FLOORS_AG' ] = '11.0'
district.loc[ 11 , 'FLOORS_AG' ] = '13.0'
district.loc[ 12 , 'FLOORS_AG' ] = '16.0'
district.loc[ 13 , 'FLOORS_AG' ] = '17.0'
district.loc[ 14 , 'FLOORS_AG' ] = '17.0'
district.loc[ 15 , 'FLOORS_AG' ] = '16.0'
district.loc[ 16 , 'FLOORS_AG' ] = '13.0'
district.loc[ 17 , 'FLOORS_AG' ] = '11.0'
district.loc[ 18 , 'FLOORS_AG' ] = '12.0'
district.loc[ 19 , 'FLOORS_AG' ] = '14.0'
district.loc[ 20 , 'FLOORS_AG' ] = '17.0'
district.loc[ 21 , 'FLOORS_AG' ] = '19.0'
district.loc[ 22 , 'FLOORS_AG' ] = '19.0'
district.loc[ 23 , 'FLOORS_AG' ] = '17.0'
district.loc[ 24 , 'FLOORS_AG' ] = '14.0'
district.loc[ 25 , 'FLOORS_AG' ] = '12.0'
district.loc[ 26 , 'FLOORS_AG' ] = '12.0'
district.loc[ 27 , 'FLOORS_AG' ] = '14.0'
district.loc[ 28 , 'FLOORS_AG' ] = '17.0'
district.loc[ 29 , 'FLOORS_AG' ] = '19.0'
district.loc[ 30 , 'FLOORS_AG' ] = '19.0'
district.loc[ 31 , 'FLOORS_AG' ] = '17.0'
district.loc[ 32 , 'FLOORS_AG' ] = '14.0'
district.loc[ 33 , 'FLOORS_AG' ] = '12.0'
district.loc[ 34 , 'FLOORS_AG' ] = '11.0'
district.loc[ 35 , 'FLOORS_AG' ] = '13.0'
district.loc[ 36 , 'FLOORS_AG' ] = '16.0'
district.loc[ 37 , 'FLOORS_AG' ] = '17.0'
district.loc[ 38 , 'FLOORS_AG' ] = '17.0'
district.loc[ 39 , 'FLOORS_AG' ] = '16.0'
district.loc[ 40 , 'FLOORS_AG' ] = '13.0'
district.loc[ 41 , 'FLOORS_AG' ] = '11.0'
district.loc[ 42 , 'FLOORS_AG' ] = '12.0'
district.loc[ 43 , 'FLOORS_AG' ] = '13.0'
district.loc[ 44 , 'FLOORS_AG' ] = '14.0'
district.loc[ 45 , 'FLOORS_AG' ] = '14.0'
district.loc[ 46 , 'FLOORS_AG' ] = '13.0'
district.loc[ 47 , 'FLOORS_AG' ] = '12.0'
district.loc[ 48 , 'FLOORS_AG' ] = '11.0'
district.loc[ 49 , 'FLOORS_AG' ] = '12.0'
district.loc[ 50 , 'FLOORS_AG' ] = '12.0'
district.loc[ 51 , 'FLOORS_AG' ] = '11.0'
district.loc[ 0 , 'FLOORS_BG' ] = '0.0'
district.loc[ 1 , 'FLOORS_BG' ] = '0.0'
district.loc[ 2 , 'FLOORS_BG' ] = '0.0'
district.loc[ 3 , 'FLOORS_BG' ] = '0.0'
district.loc[ 4 , 'FLOORS_BG' ] = '0.0'
district.loc[ 5 , 'FLOORS_BG' ] = '0.0'
district.loc[ 6 , 'FLOORS_BG' ] = '0.0'
district.loc[ 7 , 'FLOORS_BG' ] = '0.0'
district.loc[ 8 , 'FLOORS_BG' ] = '0.0'
district.loc[ 9 , 'FLOORS_BG' ] = '0.0'
district.loc[ 10 , 'FLOORS_BG' ] = '0.0'
district.loc[ 11 , 'FLOORS_BG' ] = '0.0'
district.loc[ 12 , 'FLOORS_BG' ] = '0.0'
district.loc[ 13 , 'FLOORS_BG' ] = '0.0'
district.loc[ 14 , 'FLOORS_BG' ] = '0.0'
district.loc[ 15 , 'FLOORS_BG' ] = '0.0'
district.loc[ 16 , 'FLOORS_BG' ] = '0.0'
district.loc[ 17 , 'FLOORS_BG' ] = '0.0'
district.loc[ 18 , 'FLOORS_BG' ] = '0.0'
district.loc[ 19 , 'FLOORS_BG' ] = '0.0'
district.loc[ 20 , 'FLOORS_BG' ] = '0.0'
district.loc[ 21 , 'FLOORS_BG' ] = '0.0'
district.loc[ 22 , 'FLOORS_BG' ] = '0.0'
district.loc[ 23 , 'FLOORS_BG' ] = '0.0'
district.loc[ 24 , 'FLOORS_BG' ] = '0.0'
district.loc[ 25 , 'FLOORS_BG' ] = '0.0'
district.loc[ 26 , 'FLOORS_BG' ] = '0.0'
district.loc[ 27 , 'FLOORS_BG' ] = '0.0'
district.loc[ 28 , 'FLOORS_BG' ] = '0.0'
district.loc[ 29 , 'FLOORS_BG' ] = '0.0'
district.loc[ 30 , 'FLOORS_BG' ] = '0.0'
district.loc[ 31 , 'FLOORS_BG' ] = '0.0'
district.loc[ 32 , 'FLOORS_BG' ] = '0.0'
district.loc[ 33 , 'FLOORS_BG' ] = '0.0'
district.loc[ 34 , 'FLOORS_BG' ] = '0.0'
district.loc[ 35 , 'FLOORS_BG' ] = '0.0'
district.loc[ 36 , 'FLOORS_BG' ] = '0.0'
district.loc[ 37 , 'FLOORS_BG' ] = '0.0'
district.loc[ 38 , 'FLOORS_BG' ] = '0.0'
district.loc[ 39 , 'FLOORS_BG' ] = '0.0'
district.loc[ 40 , 'FLOORS_BG' ] = '0.0'
district.loc[ 41 , 'FLOORS_BG' ] = '0.0'
district.loc[ 42 , 'FLOORS_BG' ] = '0.0'
district.loc[ 43 , 'FLOORS_BG' ] = '0.0'
district.loc[ 44 , 'FLOORS_BG' ] = '0.0'
district.loc[ 45 , 'FLOORS_BG' ] = '0.0'
district.loc[ 46 , 'FLOORS_BG' ] = '0.0'
district.loc[ 47 , 'FLOORS_BG' ] = '0.0'
district.loc[ 48 , 'FLOORS_BG' ] = '0.0'
district.loc[ 49 , 'FLOORS_BG' ] = '0.0'
district.loc[ 50 , 'FLOORS_BG' ] = '0.0'
district.loc[ 51 , 'FLOORS_BG' ] = '0.0'
# Create an output path for the data to .shp
out_district=r"C:/UBG_to_CEA/baseline/inputs/building-geometry/district.shp"

# Write .shp
district.to_file(out_district, driver='ESRI Shapefile')
