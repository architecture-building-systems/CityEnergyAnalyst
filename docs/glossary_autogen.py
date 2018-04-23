import csv

with open('default_databases.csv','rb') as databases, open('glossary.rst','wb') as gloss:
    reader = csv.reader(databases, delimiter=';')
    writer = csv.writer(gloss)

    headers = reader.next()
    table_headers = headers[4:8]
    tag1 = headers[1:4]

    for row, col in enumerate(reader):
        if row >= 1:
            if col[0] != '':
                database_name = col[0]
                info = map(lambda x, y: "**"+x+"**"+":"+y, tag1, col[1:4])
                print(str(database_name)+'\n'+len(database_name)*'=')
                print(info[0])
                print(info[1])
                print(info[2])
                print
