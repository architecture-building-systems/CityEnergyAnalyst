import string
import csv

with open('metadatabase.csv','rb') as databases:
    reader = csv.reader(databases,delimiter=';')

    ## creates list of mini-tables corresponding to each database

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

with open('glossary.rst', 'w') as file:
    file.write('Glossary'+'\n'+'========'+'\n')
    for x in range(0, len(table_contents)):
        data = table_contents[x]
        info = details[x]

        file.write(str(database_name[x]) + '\n' + len(database_name[x]) * '-' + '\n')
        for y in range(len(info)):
            file.write('**' + tag[y] + "**" + ": " + info[y] + '\n\n')

        def as_rest_table(data, full=False):
            data = data if data else [['']]

            table = []
            # max size of each column
            sizes = map(max, zip(*[[len(str(elt)) for elt in member]
                                   for member in data]))
            num_elts = len(sizes)

            if full:
                start_of_line = '| '
                vertical_separator = ' | '
                end_of_line = ' |'
                line_marker = '-'
            else:
                start_of_line = ''
                vertical_separator = '  '
                end_of_line = ''
                line_marker = '='

            meta_template = vertical_separator.join(['{{{{{0}:{{{0}}}}}}}'.format(i)
                                                     for i in range(num_elts)])
            template = '{0}{1}{2}'.format(start_of_line,
                                          meta_template.format(*sizes),
                                          end_of_line)
            # determine top/bottom borders
            if full:
                to_separator = string.maketrans('| ', '+-')
            else:
                to_separator = string.maketrans('|', '+')
            start_of_line = start_of_line.translate(to_separator)
            vertical_separator = vertical_separator.translate(to_separator)
            end_of_line = end_of_line.translate(to_separator)
            separator = '{0}{1}{2}'.format(start_of_line,
                                           vertical_separator.join([x * line_marker for x in sizes]),
                                           end_of_line)
            # determine header separator
            th_separator_tr = string.maketrans('-', '=')
            start_of_line = start_of_line.translate(th_separator_tr)
            line_marker = line_marker.translate(th_separator_tr)
            vertical_separator = vertical_separator.translate(th_separator_tr)
            end_of_line = end_of_line.translate(th_separator_tr)
            th_separator = '{0}{1}{2}'.format(start_of_line,
                                              vertical_separator.join([x * line_marker for x in sizes]),
                                              end_of_line)
            # prepare result
            table.append(separator)
            # set table header
            titles = data[0]
            table.append(template.format(*titles))
            table.append(th_separator)

            for d in data[1:-1]:
                table.append(template.format(*d))
                if full:
                    table.append(separator)
            table.append(template.format(*data[-1]))
            table.append(separator)
            return '\n'.join(table)
        file.write(as_rest_table(data, True) + '\n\n')