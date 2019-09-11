Author: Prakhar Mehta (pmehta@student.ethz.ch)
with the help of Martin Mosteiro (Catch him for errors :P )

****************************************************************************************************************************************************************************************************************************************
**construction_properties.xlsx**
"all values taken from SIA 2024 (2015)"

Color Codes:
red = value not available in SIA 2024
yellow = calculated values/discussed values

#######INTERNAL_LOADS#######
MULTI_RES	: 1.1
SINGLE_RES	: 1.2
HOTEL		: 2.1 (Hotelzimmer)
OFFICE		: 3.1 (Einzel-, Gruppenburo)
RETAIL		: 5.2 (Fachgeschaft)
FOODSTORE	: 5.1 (Lebensmittelverkauf)
RESTAURANT	: 6.1 
INDUSTRIAL	: 9.1 (Grosse Arbeit) <no value for Epro_Wm2 and Qhpro_Wm2 in SIA hence left unchanged from old CEA database value>
SCHOOL		: 4.1 (Schulzimmer)
GYM			: 11.2
SWIMMING	: 11.3
SERVERROOM	: 12.12
PARKING		: 12.9
COOLROOM	: 12.11
LAB			: 9.3 <no value for Epro_Wm2 in SIA hence left unchanged from old CEA database value, which is same as INDUSTRIAL>
MUSEUM		: 7.3
LIBRARY		: 4.3
UNIVERSITY	: 4.4 (Horsaal)
HOSPITAL	: SPECIAL! - calculated as a combination of Bettenzimmer, behandlungsraum and sitzungzimmer in proportion to the floor areas of University Hospital Zurich. Refer Hospital_Proportions.xlsx, filter_USZ.xlsx and USZHospital_Ratio_Roomuse_Types.xlsx - sent to Martin. Data of the hospital provided by Martin. <no value for Qhpro_Wm2 in SIA hence left unchanged from old CEA database value>


#######INDOOR_COMFORT#######
Tcs_set_C and Ths_set_C : taken from SIA 2024
Tcs_setb_C and Ths_setb_C : not available in SIA 2024. Kept the same as the old CEA Database
COOLROOM: Special case, Tcs_set_C and Ths_set_C are both set at 2 degrees C. 

Ve_lps: Calculated from SIA standards to have the correct units (litres per person per second)
SERVERROOM: <no value in SIA hence left unchanged from old CEA database value>

rhum_min_pc and rhum_max_pc: taken from SIA 2024
PARKING and COOLROOM: <no value in SIA hence left unchanged from old CEA database value>



#######SUPPLY#######
type_cs: old CEA database: T2 instead of T3 (mini split AC instead of central AC). Currently: all changed to T3. Discussion with Martin about this

 
#######ARCHITECTURE AND HVAC#######
No Changes 



****************************************************************************************************************************************************************************************************************************************
**occupancy_schedules.xlsx**
"all values taken from SIA 2024 (2015)"

Color Codes:
GREEN - all new schedules from SIA 2024 (2015)
No Color (only for Probability of DHW consumption) - Unchanged from old CEA Database because not available in SIA 2024, and no reference for old CEA Database. 

Occupancy and Prob. of lighting and appliances - taken from SIA 2024 as is. If the schedule is for one day off (Ruhetage pro Woche), then Sunday is set to base loads. If two days off, then Saturday and Sunday are both set at base loads