import sys
import os
import csv

with open('metadatabase.csv','rb') as databases:
    reader = csv.reader(databases,delimiter=';')

sys.path.insert(0, os.path.abspath('../docs'))

## creates list of mini- variable tables (stored as a list) corresponding to each database

    start = [] # stores the first row adjacent to database name
    var_table = [] # stores the values following the first database name until there is an input in the database name
    body = [] # stores the values for tac as one list before tac reset
    token = int(0) # stores the row number when input detected for database name
    database_name = []  # list of database names (index 0)
    table_contents = []  # list of specific table contents
    header = []
    listheaders = []  # list of general table contents
    tag = []
    info=[]
    details = []


    for row, col in enumerate(reader):
        if row == 0:
            header = col[6:11] # defines the glossary variable headers
            tag = col[1:6] # defines the other information (e.g. interdependancies, location etc...)
        if row >= 1: #skips header
            if col[0] != '': # if database name column is not blank
                database_name.append(col[0]) # stores database name
                details.append(col[1:6]) # stores database information (excluding variable table)
                body.extend([var_table])# stores variable table information without header or first row
                token = row #counts each time a database name is input
                var_table=[] # resets variable table to blank list
            if col[0] == '':
                    var_table.append(col[6:11]) # stores each subsequent row in the glossary variables
        if row == token and token != 0:
            start.append([col[6:11]])
            listheaders.append([header])

del body[0]
body.append([])


table_contents = map(lambda x, y: x+y, start,body)
table_contents = map(lambda x, y: x+y, listheaders,table_contents)


file = open('glossary.rst', 'w')
file.write('Glossary'+'\n'+'========'+'\n')