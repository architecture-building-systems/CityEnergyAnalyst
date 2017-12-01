from dbfpy import dbf

## create empty DBF, set fields

path_supply=r'C:\UBG_to_CEA\baseline\inputs\building-properties\supply_systems.dbf'

db = dbf.Dbf(path_supply, new=True)

db.addField(
    ("NAME", "C", 15),
("TYPE_EL", "C", 15),
("TYPE_CS", "C", 15),
("TYPE_HS", "C", 15),
("TYPE_DHW", "C", 15)
)

## fill DBF with some records

for name, el, cs, hs, dhw in (
("Bldg_0", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_1", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_2", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_3", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_4", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_5", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_6", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_7", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_8", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_9", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_10", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_11", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_12", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_13", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_14", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_15", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_16", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_17", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_18", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_19", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_20", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_21", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_22", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_23", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_24", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_25", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_26", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_27", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_28", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_29", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_30", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_31", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_32", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_33", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_34", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_35", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_36", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_37", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_38", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_39", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_40", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_41", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_42", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_43", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_44", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_45", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_46", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_47", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_48", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_49", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_50", " T1 ", " T4 "," T12 " ," T12 "),("Bldg_51", " T1 ", " T4 "," T12 " ," T12 ")
):
    rec = db.newRecord()
    rec["NAME"] = name
    rec["TYPE_EL"] = el
    rec["TYPE_CS"] = cs
    rec["TYPE_HS"] = hs
    rec["TYPE_DHW"] = dhw

    rec.store()
db.close()