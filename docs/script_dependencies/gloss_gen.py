"""glossary generator"""

import os
import cea.config as config
import cea.inputlocator
import yaml
import string
import pandas

locator = cea.inputlocator.InputLocator(config.Configuration().scenario)
TRACE_PATH = os.path.join(os.path.dirname(locator.scenario),'baseline\\outputs\\trace_inputlocator.output.yml')
with open(TRACE_PATH, 'r') as td:
    trace_data = yaml.load(td)

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






