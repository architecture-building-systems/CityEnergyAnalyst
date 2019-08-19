from flask_restplus import Namespace, Resource, fields

api = Namespace('Jobs', description='A job server for cea-worker processes')


# FIXME: replace with database or similar solution
class Job(object):
    """Store all the information required to run a job"""
    def __init__(self, id, script, project, scenario, parameters):
        self.id = id
        self.script = script
        self.project = project
        self.scenario = scenario
        self.parameters = parameters


jobs = [Job(id=1, script="demand", project="reference-case-cooling", scenario="baseline", parameters={})]

@api.route('/list')
class ListJobs(Resource):
    def get(self):
        return [j.id for j in jobs]
