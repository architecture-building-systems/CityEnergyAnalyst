import string
import csv

with open('metadatabase.csv','rb') as databases:
    reader = csv.reader(databases,delimiter=';')

    ## creates list of mini-tables corresponding to each database

    start = []  # stores the first row adjacent to database name
    var_table = []  # stores the values following the first database name until there is an input in the database name
    body = []  # stores the values for tac as one list before tac reset
    token = int(0)  # stores the row number when input detected for database name
    database_name = []  # list of database names (index 0)
    table_contents = []  # list of specific table contents
    header = []
    listheaders = []  # list of general table contents
    tag = []
    info = []
    details = []
    database_type = []

    for row, col in enumerate(reader):
        if row == 0:
            header = col[7:12]  # defines the glossary variable headers
            tag = col[2:7]  # defines the other information (e.g. interdependancies, location etc...)
        if row >= 1:  # skips header
            if col[1] != '':  # if database name column is not blank
                database_type.append(col[0])  # stores database type
                database_name.append(col[1])  # stores database name
                details.append(col[2:7])  # stores database information (excluding variable table)
                body.extend([var_table]) # stores variable table information without header or first row
                token = row  # counts each time a database name is input
                var_table = []  # resets variable table to blank list
            if col[1] == '':
                    var_table.append(col[7:12])  # stores each subsequent row in the glossary variables
        if row == token and token != 0:
            start.append([col[7:12]])
            listheaders.append([header])

del body[0]
body.append([])

table_contents = map(lambda x, y: x+y, start,body)
# table_contents = map(lambda x, y: x+y, listheaders,table_contents)
for x in range(0, len(table_contents)):
        data = table_contents[x]
        info = details[x]

print(table_contents)


# with open('databases.rst', 'w') as file:
#
#     for x in range(0, len(table_contents)):
#         data = table_contents[x]
#         info = details[x]
#         if database_type[x] != '':
#             file.write('\n' + database_type[x] + '\n' + len(database_type[x]) * '-' + '\n')
#
#         file.write(str(database_name[x]) + '\n' + len(database_name[x]) * '^' + '\n')
#
#         for y in range(len(info)):
#             file.write('**' + tag[y] + "**" + ": " + info[y] + '\n\n')
#         def as_rest_table(data, full=False):
#             data = data if data else [['']]
#
#             table = []
#             # max size of each column
#             sizes = map(max, zip(*[[len(str(elt)) for elt in member]
#                                    for member in data]))
#             num_elts = len(sizes)
#
#             if full:
#                 start_of_line = '| '
#                 vertical_separator = ' | '
#                 end_of_line = ' |'
#                 line_marker = '-'
#             else:
#                 start_of_line = ''
#                 vertical_separator = '  '
#                 end_of_line = ''
#                 line_marker = '='
#
#             meta_template = vertical_separator.join(['{{{{{0}:{{{0}}}}}}}'.format(i)
#                                                      for i in range(num_elts)])
#             template = '{0}{1}{2}'.format(start_of_line,
#                                           meta_template.format(*sizes),
#                                           end_of_line)
#             # determine top/bottom borders
#             if full:
#                 to_separator = string.maketrans('| ', '+-')
#             else:
#                 to_separator = string.maketrans('|', '+')
#             start_of_line = start_of_line.translate(to_separator)
#             vertical_separator = vertical_separator.translate(to_separator)
#             end_of_line = end_of_line.translate(to_separator)
#             separator = '{0}{1}{2}'.format(start_of_line,
#                                            vertical_separator.join([x * line_marker for x in sizes]),
#                                            end_of_line)
#             # determine header separator
#             th_separator_tr = string.maketrans('-', '=')
#             start_of_line = start_of_line.translate(th_separator_tr)
#             line_marker = line_marker.translate(th_separator_tr)
#             vertical_separator = vertical_separator.translate(th_separator_tr)
#             end_of_line = end_of_line.translate(th_separator_tr)
#             th_separator = '{0}{1}{2}'.format(start_of_line,
#                                               vertical_separator.join([x * line_marker for x in sizes]),
#                                               end_of_line)
#             # prepare result
#             table.append(separator)
#             # set table header
#             titles = data[0]
#             table.append(template.format(*titles))
#             table.append(th_separator)
#
#             for d in data[1:-1]:
#                 table.append(template.format(*d))
#                 if full:
#                     table.append(separator)
#             table.append(template.format(*data[-1]))
#             table.append(separator)
#             return '\n'.join(table)
#         file.write(as_rest_table(data, True) + '\n\n')
#
# with open('plots_ref.csv','rb') as databases:
#     reader = csv.reader(databases,delimiter=';')
#
#     ## creates list of mini-tables corresponding to each database
#
#     start = []  # stores the first row adjacent to database name
#     var_table = []  # stores the values following the first database name until there is an input in the database name
#     body = []  # stores the values for tac as one list before tac reset
#     token = int(0)  # stores the row number when input detected for database name
#     database_name = []  # list of database names (index 0)
#     table_contents = []  # list of specific table contents
#     header = []
#     listheaders = []  # list of general table contents
#
#     info = []
#     details = []
#     database_type = []
#
#     for row, col in enumerate(reader):
#         if row == 0:
#             header = col[2:5]  # defines the glossary variable headers
#         if row >= 1:  # skips header
#             if col[1] != '':  # if database name column is not blank
#                 database_type.append(col[0])  # stores database type
#                 database_name.append(col[1])  # stores database name
#                 body.extend([var_table]) # stores variable table information without header or first row
#                 token = row  # counts each time a database name is input
#                 var_table = []  # resets variable table to blank list
#             if col[1] == '':
#                     var_table.append(col[2:5])  # stores each subsequent row in the glossary variables
#         if row == token and token != 0:
#             start.append([col[2:5]])
#             listheaders.append([header])
#
# del body[0]
# body.append([])
#
# table_contents = map(lambda x, y: x+y, start,body)
# table_contents = map(lambda x, y: x+y, listheaders,table_contents)
#
# with open('plots_ref.rst', 'w') as file:
#
#     for x in range(0, len(table_contents)):
#         data = table_contents[x]
#         if database_type[x] != '':
#             file.write('\n' + database_type[x] + '\n' + len(database_type[x]) * '-' + '\n')
#
#         file.write(str(database_name[x]) + '\n' + len(database_name[x]) * '^' + '\n')
#
#         def as_rest_table(data, full=False):
#             data = data if data else [['']]
#
#             table = []
#             # max size of each column
#             sizes = map(max, zip(*[[len(str(elt)) for elt in member]
#                                    for member in data]))
#             num_elts = len(sizes)
#
#             if full:
#                 start_of_line = '| '
#                 vertical_separator = ' | '
#                 end_of_line = ' |'
#                 line_marker = '-'
#             else:
#                 start_of_line = ''
#                 vertical_separator = '  '
#                 end_of_line = ''
#                 line_marker = '='
#
#             meta_template = vertical_separator.join(['{{{{{0}:{{{0}}}}}}}'.format(i)
#                                                      for i in range(num_elts)])
#             template = '{0}{1}{2}'.format(start_of_line,
#                                           meta_template.format(*sizes),
#                                           end_of_line)
#             # determine top/bottom borders
#             if full:
#                 to_separator = string.maketrans('| ', '+-')
#             else:
#                 to_separator = string.maketrans('|', '+')
#             start_of_line = start_of_line.translate(to_separator)
#             vertical_separator = vertical_separator.translate(to_separator)
#             end_of_line = end_of_line.translate(to_separator)
#             separator = '{0}{1}{2}'.format(start_of_line,
#                                            vertical_separator.join([x * line_marker for x in sizes]),
#                                            end_of_line)
#             # determine header separator
#             th_separator_tr = string.maketrans('-', '=')
#             start_of_line = start_of_line.translate(th_separator_tr)
#             line_marker = line_marker.translate(th_separator_tr)
#             vertical_separator = vertical_separator.translate(th_separator_tr)
#             end_of_line = end_of_line.translate(th_separator_tr)
#             th_separator = '{0}{1}{2}'.format(start_of_line,
#                                               vertical_separator.join([x * line_marker for x in sizes]),
#                                               end_of_line)
#             # prepare result
#             table.append(separator)
#             # set table header
#             titles = data[0]
#             table.append(template.format(*titles))
#             table.append(th_separator)
#
#             for d in data[1:-1]:
#                 table.append(template.format(*d))
#                 if full:
#                     table.append(separator)
#             table.append(template.format(*data[-1]))
#             table.append(separator)
#             return '\n'.join(table)
#         file.write(as_rest_table(data, True) + '\n\n')