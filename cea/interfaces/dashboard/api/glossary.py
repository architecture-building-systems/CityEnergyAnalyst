from flask_restplus import Namespace, Resource

from cea.glossary import read_glossary_df

api = Namespace('Glossary', description='Glossary for variables used in CEA')


@api.route('/')
class Glossary(Resource):
    def get(self):
        glossary = read_glossary_df()
        groups = glossary.groupby('SCRIPT')
        data = []
        for group in groups.groups:
            df = groups.get_group(group)
            result = df[~df.index.duplicated(keep='first')].fillna('-')
            data.append({'script': group if group != '-' else 'inputs', 'variables': result.to_dict(orient='records')})
        return data
