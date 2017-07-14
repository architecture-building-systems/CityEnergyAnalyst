from dbfpy import dbf

## create empty DBF, set fields

path_occupancy=r'C:\UBG_to_CEA\baseline\inputs\building-properties\occupancy.dbf'

db = dbf.Dbf(path_occupancy, new=True)

db.addField(
    ("NAME", "C", 15),
    ("Floor_1", "C", 15),
    ("Floor_2", "C", 15),
    ("Floor_3", "C", 15)
)

## fill DBF with some records

for name, floor_1, floor_2, floor_3 in (
    ("B01", "Commercial", "Office",""),("B02", "Commercial", "Office", "Residential")

):
    rec = db.newRecord()
    rec["NAME"] = name
    rec["Floor_1"] = floor_1
    rec["Floor_2"] = floor_2
    rec["Floor_3"] = floor_3

    rec.store()
db.close()



