# Streaming Service

from flask import Flask, request, jsonify
from testToken import generate_auth_token, verify_auth_token
import os
from flask_restful import Resource, Api
from pymongo import MongoClient

# API set-up
app = Flask(__name__)
SECRET_KEY = b"\xc0\x923\x909\x8b\x19H4'K9*\xaay\xdc\xaf\xb5\xbdf_>z \x13$H\x04\x8d\xee*\xbb"
app.secret_key = SECRET_KEY
api = Api(app)

# Database set-up
client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.brevetdb
user_db = client.userdb


def retrieve_user(uid=-2, username=""):
    """Returns user data as a list; can use user id (uid) or username to retrieve"""
    if username != "":
        return user_db.timestable.find_one({'username': username})
    if uid == -2:
        return user_db.timestable.find()
    return user_db.timestable.find_one({'_id': int(uid)})


class UserCheck(Resource):
    """
    returns a JSON object, {uid:int, username:str, password:str}

    uid: returns '_id' element from user_db; if -1 on exit,
    no entry matching uid or username was found in user_db
    username: returns 'username' element from user_db; if
    blank on exit, no entry found
    password: returns value only if needed for User object

    """
    def get(self):
        # variables
        uid = request.args.get('uid', default=-1)
        username = request.args.get('username', default='-1')
        # checking for user in user_db
        if uid == -1:  # if no uid given
            app.logger.debug("usercheck/username: {}".format(username))
            user_entry = retrieve_user(username=username)  # retrieve entry using username
        else:
            app.logger.debug("usercheck/uid: {}".format(uid))
            user_entry = retrieve_user(uid)  # uid given: retrieve entry using uid
        if user_entry:  # if an entry is found
            result = {
                'uid': user_entry['_id'],
                'username': user_entry['username'],
                'password': user_entry['password']
            }
        else:  # no entry found; return uid as -1, other values as blanks
            result = {
                'uid': -1,
                'username': '',
                'password': ''
            }
        return jsonify(result)


def retrieve(val_include="default"):
    """
    retrieves all data from brevets database
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
    app.logger.debug("MongoDB documents: {}".format(result))
    return result


def csv_form(result, top):
    data = ','.join(result[0].keys()) + '<br>'
    if top > 0:
        if top > len(result):
            top = len(result)
        for i in range(top):
            data = data + ','.join(result[i].values()) + '<br>'
    else:
        for i in range(len(result)):
            data = data + ','.join(result[i].values()) + '<br>'
    return data


def json_form(result, top):
    data = ''
    if top > 0:
        if top > len(result):
            top = len(result)
        for i in range(top):
            data = data + str(result[i]) + '<br>'
    else:
        for i in range(len(result)):
            data = data + str(result[i]) + '<br>'
    return data


class PullPassword(Resource):
    """
    Retrieves hashed password for specified username
    """
    def get(self):
        username = request.args.get('username')
        user = retrieve_user(username)
        if user:
            result = {'password': user['password']}
        else:
            return 400
        return jsonify(result)


@app.route('/register', methods=["POST"])
def register():
    """
    Inputs username and hashword into database, if it does not already
    exist. Returns
    """
    app.logger.debug("registerUser/output: {}".format(1))
    username = request.args.get('username')
    password = request.args.get('password')
    temp_user = retrieve_user(username=username)
    if temp_user:
        if temp_user['username'] != username:
            return 400
    user = {
        'username': username,
        'password': password
    }
    user_db.timestable.insert_one(user)
    temp = user_db.timestable.find_one({'username': user['username']})
    user['uid'] = temp['_id']
    app.logger.debug("registerUser/user: {}".format(user['uid']))
    app.logger.debug("registerUser/user: {}".format(user))
    return jsonify(user), 201


class TokenGeneration(Resource):
    """
    Checks if username and hashword (hashed password) exists in
    database. If so, generates and returns a token. Else, returns abort request
    """
    def get(self):
        username = request.args.get('username')
        hashword = request.args.get('password')
        user_info = retrieve_user(username=username)
        if user_info:
            if user_info['username'] == username and user_info['hashword'] == hashword:
                expiration = 600
                s = generate_auth_token(SECRET_KEY, expiration)
                result = {"token": s, "duration": str(expiration)}
                return jsonify(result=result)
        return 401


class ListAll(Resource):
    def get(self, dtype='json'):
        token = request.args.get('token', default='nope')
        if not verify_auth_token(SECRET_KEY, token):
            return 401
        top = request.args.get('top', default=-1, type=int)
        app.logger.debug("top: {}".format(top))
        if dtype == 'csv':
            return csv_form(retrieve(), top)
        return json_form(retrieve(), top)


class ListOpenOnly(Resource):
    def get(self, dtype='json'):
        token = request.args.get('token', default='nope')
        if not verify_auth_token(SECRET_KEY, token):
            return 401
        top = request.args.get('top', default=-1, type=int)
        app.logger.debug("top: {}".format(top))
        if dtype == 'csv':
            return csv_form(retrieve('open'), top)
        return json_form(retrieve('open'), top)


class ListCloseOnly(Resource):
    def get(self, dtype='json'):
        token = request.args.get('token', default='nope')
        if not verify_auth_token(SECRET_KEY, token):
            return 401
        top = request.args.get('top', default=-1, type=int)
        app.logger.debug("top: {}".format(top))
        if dtype == 'csv':
            return csv_form(retrieve('closed'), top)
        return json_form(retrieve('closed'), top)


# Create routes
# Another way, without decorators
api.add_resource(UserCheck, '/user_check')
api.add_resource(TokenGeneration, '/token')
api.add_resource(ListAll, '/listAll/<string:dtype>', '/listAll/')
api.add_resource(ListOpenOnly, '/listOpenOnly/<string:dtype>', '/listOpenOnly/')
api.add_resource(ListCloseOnly, '/listCloseOnly/<string:dtype>', '/listCloseOnly/')


# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
