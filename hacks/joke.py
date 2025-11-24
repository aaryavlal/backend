from flask import Blueprint, jsonify  # jsonify creates an endpoint response object
from flask_restful import Api, Resource # used for REST API building
import requests  # used for testing 
import random

from hacks.jokes import *

scenario_api = Blueprint('scenario_api', __name__,
                   url_prefix='/api/scenarios')

# API generator https://flask-restful.readthedocs.io/en/latest/api.html#id1
api = Api(scenario_api)

class ScenariosAPI:
    # not implemented
    class _Create(Resource):
        def post(self, scenario):
            pass
            
    # getScenarios()
    class _Read(Resource):
        def get(self):
            return jsonify(getScenarios())

    # getScenario(id)
    class _ReadID(Resource):
        def get(self, id):
            return jsonify(getScenario(id))

    # getRandomScenario()
    class _ReadRandom(Resource):
        def get(self):
            return jsonify(getRandomScenario())
    
    # countScenarios()
    class _ReadCount(Resource):
        def get(self):
            count = countScenarios()
            countMsg = {'count': count}
            return jsonify(countMsg)

    # put method: addDistributed
    class _UpdateDistributed(Resource):
        def put(self, id):
            addDistributed(id)
            return jsonify(getScenario(id))

    # put method: addParallel
    class _UpdateParallel(Resource):
        def put(self, id):
            addParallel(id)
            return jsonify(getScenario(id))

    # put method: addSequential
    class _UpdateSequential(Resource):
        def put(self, id):
            addSequential(id)
            return jsonify(getScenario(id))

    # building RESTapi resources/interfaces, these routes are added to Web Server
    api.add_resource(_Create, '/create/<string:scenario>', '/create/<string:scenario>/')
    api.add_resource(_Read, "", '/')
    api.add_resource(_ReadID, '/<int:id>', '/<int:id>/')
    api.add_resource(_ReadRandom, '/random', '/random/')
    api.add_resource(_ReadCount, '/count', '/count/')
    api.add_resource(_UpdateDistributed, '/distributed/<int:id>', '/distributed/<int:id>/')
    api.add_resource(_UpdateParallel, '/parallel/<int:id>', '/parallel/<int:id>/')
    api.add_resource(_UpdateSequential, '/sequential/<int:id>', '/sequential/<int:id>/')

if __name__ == "__main__": 
    # server = "http://127.0.0.1:5000" # run local
    server = 'https://flask.opencodingsociety.com' # run from web
    url = server + "/api/scenarios"
    responses = []  # responses list

    # get count of scenarios on server
    count_response = requests.get(url+"/count")
    count_json = count_response.json()
    count = count_json['count']

    # update votes test sequence
    num = str(random.randint(0, count-1)) # test a random record
    responses.append(
        requests.get(url+"/"+num)  # read scenario by id
        ) 
    responses.append(
        requests.put(url+"/distributed/"+num) # vote for distributed
        ) 
    responses.append(
        requests.put(url+"/parallel/"+num) # vote for parallel
        ) 
    responses.append(
        requests.put(url+"/sequential/"+num) # vote for sequential
        ) 

    # obtain a random scenario
    responses.append(
        requests.get(url+"/random")  # read a random scenario
        ) 

    # cycle through responses
    for response in responses:
        print(response)
        try:
            print(response.json())
        except:
            print("unknown error")