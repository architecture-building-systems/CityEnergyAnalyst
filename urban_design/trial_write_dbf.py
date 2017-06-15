import dbf
path_architecture=r'C:\reference-case-test\baseline\inputs\building-properties\architecutre.dbf'
table = dbf.Table(path_architecture, 'Building C(30); HS N(3,0); WIN_WALL N(3,0)')

for datum in (
        ('John Doe', 31, 32),
        ('Ethan Furman', 102, 32),
        ('Jane Smith', 57, 32),
        ('John Adams', 44, 32),
):
    table.append(datum)