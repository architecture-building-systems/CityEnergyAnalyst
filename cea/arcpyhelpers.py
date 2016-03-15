"""
A collection of helper functions / classes to make life working with arcpy easier.
"""


def index_cursor(cursor, fields):
    """
    Wraps a cursor as a sequence of rows that can be indexed by field name. This makes looking up column values in the
    row less error prone as you can index them by field name as opposed to column number.
    :param cursor: An arcpy cursor as returned by `arcpy.da.SearchCursor`
    :param fields: A list of field names, the same as passed to `arcpy.da.SearchCursor`
    :return: A generator wrapping each row with an indexer.
    """
    fields_lookup = dict(zip(fields, range(len(fields))))

    class CursorWrapper(object):
        def __init__(self, row):
            self.row = row

        def __getitem__(self, item):
            return self.row[fields_lookup[item]]

    return (CursorWrapper(row) for row in cursor)
