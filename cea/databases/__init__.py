import os
from collections import OrderedDict

FILE_EXTENSIONS = ['.xlsx', '.xls', '.csv']
databases_folder_path = os.path.dirname(os.path.abspath(__file__))


def get_regions():
    return [folder for folder in os.listdir(databases_folder_path) if folder != "weather"
            and os.path.isdir(os.path.join(databases_folder_path, folder))]


def get_categories(db_path):
    return [folder for folder in os.listdir(db_path) if os.path.isdir(os.path.join(db_path, folder))]


def get_database_template_tree():
    """
    Assumes that folders in `databases_folder_path` are `categories` and items (file/folder) in `categories` are `databases`.
    Uses first region database as template (i.e. CH)
    :return: dict containing `categories` and `databases`
    e.g.
    {
        'categories': {
            '$category_name': {
                'databases': [
                    {
                        'name': '$database_name',
                        'extension': '$database_extension'
                    },
                    ...
                ]
            },
            ...
        }
    }
    """
    out = {'categories': OrderedDict()}
    template_path = os.path.join(databases_folder_path, get_regions()[0])
    for category in get_categories(template_path):
        category_path = os.path.join(template_path, category)
        category_databases = []
        for database in os.listdir(category_path):
            database_name, ext = os.path.splitext(database)
            if ext in FILE_EXTENSIONS or os.path.isdir(os.path.join(category_path, database_name)):
                database_name = database_name.upper()
                category_databases.append({'name': database_name, 'extension': ext})
        if category_databases:
            out['categories'][category] = {'databases': category_databases}
    return out


def get_database_tree(db_path):
    """
    Look for database files in `db_path` based on `get_database_template_tree`
    :param db_path: path of databases
    :return: dict containing `categories` and `databases` found in `db_path`
    e.g.
    {
        'categories': {
            '$category_name': {
                'databases': [...]
            },
            ...
        },
        'databases': {
            '$database_name': {
                'files': [
                    {
                        'extension': '$file_extension',
                        'name': '$file_name',
                        'path': '$path'
                    },
                    ...
                ]
            },
            ...
        }
    }
    """
    database_categories_tree = get_database_template_tree()['categories']
    out = {'categories': OrderedDict(), 'databases': OrderedDict()}
    for category, databases in database_categories_tree.items():
        out['categories'][category] = {'databases': []}
        for database in databases['databases']:
            database_name = database['name']
            database_path = os.path.join(db_path, category, database_name)
            out['databases'][database_name] = {'files': path_crawler(database_path + database['extension'])}
            out['categories'][category]['databases'].append(database_name)
    return out


def path_crawler(parent_path, out=None):
    """
    Recursive function that looks for files in `parent_path`
    :param parent_path:
    :param out:
    :return: list of files with its properties (i.e. name, extension, path) contained in `parent_path`
    """
    if out is None:
        out = []
    if os.path.isfile(parent_path):
        name, ext = os.path.splitext(os.path.basename(parent_path))
        if ext in FILE_EXTENSIONS:
            out.append({'path': parent_path, 'name': name, 'extension': ext})
    else:
        for path in os.listdir(parent_path):
            child_path = os.path.join(parent_path, path)
            path_crawler(child_path, out)
    return out


if __name__ == '__main__':
    import json
    import cea.config
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)

    print(json.dumps(get_database_template_tree(), indent=2))
    print(json.dumps(get_database_tree(locator.get_databases_folder()), indent=2))

