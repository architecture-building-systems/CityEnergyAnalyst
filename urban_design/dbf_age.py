from dbfpy import dbf

## create empty DBF, set fields

path_age =r'C:\UBG_to_CEA\baseline\inputs\building-properties\age.dbf'

db = dbf.Dbf(path_age, new=True)

db.addField(
    ("NAME", "C", 15),
    ("BUILT", "C", 15),
    ("ROOF", "C", 15),
    ("WINDOWS", "C", 15),
    ("PARTITIONS", "C", 15),
    ("BASEMENT", "C", 15),
    ("HVAC", "C", 15),
    ("ENVELOPE", "C", 15)
)
print db
print

## fill DBF with some records

for name, built, roof, windows, partitions, basement, hvac, envelope in (
    ("B01", "2016", "0", "0", "0", "0", "0", "0" ),

):
    rec = db.newRecord()
    rec["NAME"] = name
    rec["BUILT"] = built
    rec["ROOF"] = roof
    rec["WINDOWS"] = windows
    rec["PARTITIONS"] = partitions
    rec["BASEMENT"] = basement
    rec["HVAC"] = hvac
    rec["ENVELOPE"] = envelope

    rec.store()
db.close()

## read DBF and print records

db = dbf.Dbf(path_age)
for rec in db:
    print rec
print

