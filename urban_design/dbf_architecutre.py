from dbfpy import dbf

## create empty DBF, set fields

path_architecture=r'C:\UBG_to_CEA\baseline\inputs\building-properties\architecture.dbf'

db = dbf.Dbf(path_architecture, new=True)

db.addField(
    ("NAME", "C", 15),
    ("HS", "C", 15),
    ("WIN_WALL", "C", 15),
    ("TYPE_CONS", "C", 15),
    ("TYPE_LEAK", "C", 15),
    ("TYPE_ROOF", "C", 15),
    ("TYPE_WALL", "C", 15),
    ("TYPE_WIN", "C", 15),
    ("TYPE_SHADE", "C", 15)
)
print db
print

## fill DBF with some records

for name, hs, win_wall, type_cons, type_leak, type_roof, type_wall, type_win, type_shade in (
    ("B01", "0", "0", "T3", "T2", "T4", "T5", "T2", "T1" ),

):
    rec = db.newRecord()
    rec["NAME"] = name
    rec["HS"] = hs
    rec["WIN_WALL"] = win_wall
    rec["TYPE_CONS"] = type_cons
    rec["TYPE_LEAK"] = type_leak
    rec["TYPE_ROOF"] = type_roof
    rec["TYPE_WALL"] = type_wall
    rec["TYPE_WIN"] = type_win
    rec["TYPE_SHADE"] = type_shade

    rec.store()
db.close()

## read DBF and print records

db = dbf.Dbf(path_architecture)
for rec in db:
    print rec
print

