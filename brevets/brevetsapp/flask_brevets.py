"""
Replacement for RUSA ACP brevet time calculator
(see https://rusa.org/octime_acp.html)

"""

import os
import flask
from flask import request
import json
import arrow  # Replacement for datetime, based on moment.js
import acp_times  # Brevet time calculations
from pymongo import MongoClient

import logging

###
# Globals
###
app = flask.Flask(__name__)

client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.brevetdb
###
# Pages
###


@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    return flask.render_template('calc.html')


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('404.html'), 404


@app.route("/_submit_route", methods=['POST'])
def insert():
    app.logger.debug("Got a JSON request")
    db.timestable.delete_many({})
    app.logger.debug("Current database emptied")
    vals = request.form.get("vals")
    app.logger.debug("request.form: {}".format(request.form))
    if vals is not None:
        vals = json.loads(vals)
    app.logger.debug("vals={}".format(vals))
    for i in vals:
        app.logger.debug("vals={}".format(i))
        control_point = {
            'km': i[0],
            'open_time': i[1],
            'close_time': i[2]
        }
        db.timestable.insert_one(control_point)
    result = "Success!"
    return flask.jsonify(result=result)


@app.route('/_display_route')
def display():
    app.logger.debug("Got a JSON request")
    result = []
    temp = db.timestable.find()
    for i in temp:
        del i['_id']
        result.append(i)
    app.logger.debug("MangoDB documents: {}".format(result))
    return flask.jsonify(result=result)


###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############
@app.route("/_calc_times")
def _calc_times():
    """
    Calculates open/close times from miles, using rules
    described at https://rusa.org/octime_alg.html.
    Expects one URL-encoded argument, the number of miles.
    """
    app.logger.debug("Got a JSON request")
    km = request.args.get('km', 999, type=float)
    brev_distance = request.args.get('brev_distance', type=float)
    begin_date = request.args.get('begin_date', type=str)
    app.logger.debug("km={}".format(km))
    app.logger.debug("distance={}".format(brev_distance))
    app.logger.debug("begin date={}".format(begin_date))
    app.logger.debug("request.args: {}".format(request.args))
    open_time = acp_times.open_time(km, brev_distance, arrow.get(begin_date)).format('YYYY-MM-DDTHH:mm')
    close_time = acp_times.close_time(km, brev_distance, arrow.get(begin_date)).format('YYYY-MM-DDTHH:mm')
    result = {"open": open_time, "close": close_time}
    return flask.jsonify(result=result)


#############

app.debug = True
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    print("Opening for global access on port {}".format(5000))
    app.run(port=5000, host="0.0.0.0")
