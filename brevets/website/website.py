from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

URL_TRACE = "http://" + os.environ['BACKEND_ADDR'] + ":" + os.environ['BACKEND_PORT']


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return render_template('404.html'), 404


@app.route('/')
@app.route('/index')
def home():
    return render_template('index.html')


@app.route('/listevery')
def listeverything():
    json_csv = request.args.get('json_csv')
    top = request.args.get('top', default=0, type=int)
    temp_path = URL_TRACE + '/listAll/'
    if json_csv == "csv":
        temp_path = temp_path + 'csv'
    if top != 0 and top != -1:
        r = requests.get(temp_path, params={'top': top})
    else:
        r = requests.get(temp_path)
    app.logger.debug("r.text: {}".format(r.text))
    return r.text


@app.route('/listopen')
def listopenonly():
    json_csv = request.args.get('json_csv')
    top = request.args.get('top', default=0, type=int)
    temp_path = URL_TRACE + '/listOpenOnly/'
    if json_csv == "csv":
        temp_path = temp_path + 'csv'
    if top != 0 and top != -1:
        r = requests.get(temp_path, params={'top': top})
    else:
        r = requests.get(temp_path)
    app.logger.debug("r.text: {}".format(r.text))
    return r.text


@app.route('/listclose')
def listcloseonly():
    json_csv = request.args.get('json_csv')
    top = request.args.get('top', default=0, type=int)
    temp_path = URL_TRACE + '/listCloseOnly/'
    if json_csv == "csv":
        temp_path = temp_path + 'csv'
    if top != 0 and top != -1:
        r = requests.get(temp_path, params={'top': top})
    else:
        r = requests.get(temp_path)
    app.logger.debug("r.text: {}".format(r.text))
    return r.text


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
