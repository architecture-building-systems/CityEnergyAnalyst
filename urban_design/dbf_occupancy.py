from dbfpy import dbf

## create empty DBF, set fields

path_occupancy=r'C:\reference-case-test\baseline\inputs\building-properties\occupancy.dbf'

db = dbf.Dbf(path_occupancy, new=True)

db.addField(
    ("NAME", "C", 15),
    ("Floor_1", "C", 15),
    ("Floor_2", "C", 15),
    ("Floor_3", "C", 15)
)
print db
print

## fill DBF with some records

for name, floor_1, floor_2, floor_3 in (
    ("B01", "Commercial", "Office", "Residential"),

):
    rec = db.newRecord()
    rec["NAME"] = name
    rec["Floor_1"] = floor_1
    rec["Floor_2"] = floor_2
    rec["Floor_3"] = floor_3

    rec.store()
db.close()

## read DBF and print records

db = dbf.Dbf(path_occupancy)
for rec in db:
    print rec
print

