# Streaming Service

from flask import Flask, request
import os
from flask_restful import Resource, Api
from pymongo import MongoClient


app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.brevetdb


def retrieve(val_include="default"):
    """
    retrieves all data from database
    """
    app.logger.debug("Pulling data from db")
    temp = db.timestable.find()
    result = []
    for i in temp:
        del i['_id']
        del i['km']
        if val_include == "open":
            del i['close_time']
        if val_include == "closed":
            del i['open_time']
        result.append(i)
    app.logger.debug("MangoDB documents: {}".format(result))
    return result


def csv_form(result, top):
    data = ','.join(result[0].keys()) + '\n'
    if top > 0:
        if top > len(result):
            top = len(result)
        for i in range(top):
            data = data + ','.join(result[i].values()) + '\n'
    else:
        for i in range(len(result)):
            data = data + ','.join(result[i].values()) + '\n'
    return data


def json_form(result, top):
    data = ''
    if top > 0:
        if top > len(result):
            top = len(result)
        for i in range(top):
            data = data + str(result[i]) + '\n'
    else:
        for i in range(len(result)):
            data = data + str(result[i]) + '\n'
    return data


class ListAll(Resource):
    def get(self, dtype='json', top=-1):
        if dtype == 'csv':
            return csv_form(retrieve(), top)
        return json_form(retrieve(), top)


class ListOpenOnly(Resource):
    def get(self, dtype='json', top=-1):
        if dtype == 'csv':
            return csv_form(retrieve('open'), top)
        return json_form(retrieve('open'), top)


class ListCloseOnly(Resource):
    def get(self, dtype, top=-1):
        if dtype == 'csv':
            return csv_form(retrieve('closed'), top)
        return json_form(retrieve('closed'), top)


# Create routes
# Another way, without decorators
api.add_resource(ListAll, '/listAll/<string:dtype>/<int:top>')
api.add_resource(ListOpenOnly, '/listOpenOnly/<string:dtype>/<int:top>')
api.add_resource(ListCloseOnly, '/listCloseOnly/<string:dtype>/<int:top>')


# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
