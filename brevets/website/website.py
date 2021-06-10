from flask import Flask, request, render_template, redirect, url_for, flash, abort
from passlib.hash import sha256_crypt as pwd_context
from urllib.parse import urlparse, urljoin
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user, UserMixin,
                         confirm_login, fresh_login_required)
from flask_wtf import FlaskForm as Form
from wtforms import BooleanField, StringField, PasswordField, validators
import requests
import os
import json

app = Flask(__name__)

app.secret_key = os.urandom(32)

# LoginManager set-up
login_manager = LoginManager()

login_manager.session_protection = "strong"

login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."

login_manager.refresh_view = "login"
login_manager.needs_refresh_message = (
    u"To protect your account, please reauthenticate to access this page."
)
login_manager.needs_refresh_message_category = "info"

URL_TRACE = "http://" + os.environ['BACKEND_ADDR'] + ":" + os.environ['BACKEND_PORT']

USERS = {}


@login_manager.user_loader
def load_user(uid):
    if str(uid) in USERS.keys():
        USERS[str(uid)] = current_user
        return USERS[str(uid)]
    else:
        USERS[str(uid)] = current_user
    return USERS[str(uid)]


login_manager.init_app(app)


class LoginForm(Form):
    username = StringField('Username', [
        validators.Length(min=2, max=25,
                          message=u"Invalid length for username - must be between 2 and 25 characters."),
        validators.InputRequired(u"Must put in a username!")])
    password = PasswordField('Password', [
        validators.Length(min=6, max=20,
                          message=u"Password must be between 6 and 20 characters"),
        validators.InputRequired(u"Must put in a password!")])
    remember = BooleanField('Remember me')


class RegisterForm(Form):
    username = StringField('Username', [
        validators.Length(min=2, max=25,
                          message=u"Invalid length for username - must be between 2 and 25 characters."),
        validators.InputRequired(u"Must put in a username!")])
    password = PasswordField('Password', [
        validators.Length(min=6, max=20,
                          message=u"Password must be between 6 and 20 characters"),
        validators.InputRequired(u"Must put in a password!"),
        validators.EqualTo('confirm', message='Passwords did not match')])
    confirm = PasswordField('Confirm password', [
        validators.Length(min=6, max=20,
                          message=u"Password must be between 6 and 20 characters")])


def is_safe_url(target):
    """
    :source: https://github.com/fengsp/flask-snippets/blob/master/security/redirect_back.py
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


class User(UserMixin):
    def __init__(self, uid, username, password):
        self.id = str(uid).encode("utf-8").decode("utf-8")
        self.username = username
        self.password = password
        self.token = 'nope'

    def set_id(self, uid):
        self.id = uid

    def set_token(self, token):
        self.token = token

    def db_dict(self):
        new_dict = {
            'uid': self.id,
            'username': self.username,
            'password': self.password,
            'token': self.token
        }
        return new_dict


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return render_template('404.html'), 404


@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated and current_user.db_dict()['token'] == 'none':
        return redirect(url_for('get_token'))
    return render_template('index.html')


@app.route('/calc_index.html')
@login_required
def home():
    return render_template('calc_index.html')


@app.route('/get_token')
def get_token():
    if current_user.is_authenticated:
        s = current_user.db_dict()
        uid = s['uid']
        r = requests.get(URL_TRACE + '/token', params=s)
        app.logger.debug("/get_token/token: {}".format(r.text))
        if r.status_code == 401:
            abort(401)
        current_user.set_token(r.text)
        if str(uid) in USERS.keys():
            USERS[str(uid)] = current_user
        else:
            USERS[str(uid)] = current_user
    return redirect(url_for('index'))


@app.route('/_check')
def check():
    s = current_user.db_dict()
    app.logger.debug(s)
    return s


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    proceed = True
    # Collect form data
    if form.validate_on_submit() and request.method == "POST" and ("username" and "password" in request.form):
        username = str(form.username.data)
        password = pwd_context.encrypt(str(form.password.data), salt='12345678abcdefgh')
        temp_user = User(-1, username, password)
        remember = request.form.get("remember", "false") == "true"

        # Check if user exists in database and if password is correct
        r = requests.get(URL_TRACE + '/pass_check', params=temp_user.db_dict())
        r_text = json.loads(r.text)
        if r_text['login'] == 'fail':  # no matching username found in database
            flash("Invalid username or password!")
            proceed = False
        r = requests.get(URL_TRACE + '/user_check', params=temp_user.db_dict())
        r_text = json.loads(r.text)
        temp_user.set_id(r_text['uid'])
        # Login user, if nothing went wrong finding user info in database
        if proceed:
            if login_user(temp_user, remember=remember):
                flash("Logged in!")
                flash("I'll remember you") if remember else None
                next = url_for('get_token')
                if not is_safe_url(next):
                    abort(400)
                return redirect(next or url_for('index'))
    return render_template('login.html', form=form)


@app.route("/add_user", methods=["GET", "POST"])
def new_user():
    form = RegisterForm()
    if form.validate_on_submit() and request.method == "POST" and ("username" and "password" in request.form):
        username = str(form.username.data)
        password = pwd_context.encrypt(str(form.password.data), salt='12345678abcdefgh')
        app.logger.debug("register/hash_password: {}".format(password))
        temp_user = User(-1, username, password)
        # check if username already exists
        r = requests.get(URL_TRACE + '/user_check', params=temp_user.db_dict())
        r_text = json.loads(r.text)
        if r_text['username'] == str(username):  # username already exists!
            flash("Username taken! Try again.")
            return render_template('register.html', form=form)
        else:  # if username does not already exist
            r = requests.post(URL_TRACE + '/register', params=temp_user.db_dict())
            if r.status_code == 400:
                return render_template('register.html', form=form)
            app.logger.debug("register/reg_success: {}".format(r.text))
            r_text = json.loads(r.text)
            app.logger.debug("register/reg_success: {}".format(r_text))
            return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/hidden')
def delete_all():
    requests.get(URL_TRACE + '/hidden')
    return redirect(url_for("index"))


@app.route('/logout')
@login_required
def logout():
    current_user.set_token("")
    logout_user()
    flash("Logged out.")
    return redirect(url_for("index"))


@app.route('/listevery')
@login_required
def listeverything():
    s = current_user.db_dict()['token']
    json_csv = request.args.get('json_csv')
    top = request.args.get('top', default=0, type=int)
    temp_path = URL_TRACE + '/listAll/'
    if json_csv == "csv":
        temp_path = temp_path + 'csv'
    if top != 0 and top != -1:
        r = requests.get(temp_path, params={'top': top, 'token': s})
    else:
        r = requests.get(temp_path)
        app.logger.debug("r.text: {}".format(r.status_code))
    if r.status_code == 401:
        return abort(401)
    app.logger.debug("r.text: {}".format(r.status_code))
    app.logger.debug("r.text: {}".format(r.text))
    return r.text


@app.route('/listopen')
@login_required
def listopenonly():
    s = current_user.db_dict()['token']
    json_csv = request.args.get('json_csv')
    top = request.args.get('top', default=0, type=int)
    temp_path = URL_TRACE + '/listOpenOnly/'
    if json_csv == "csv":
        temp_path = temp_path + 'csv'
    if top != 0 and top != -1:
        r = requests.get(temp_path, params={'top': top, 'token': s})
    else:
        r = requests.get(temp_path)
    if r.status_code == 401:
        return abort(401)
    app.logger.debug("r.text: {}".format(r.status_code))
    app.logger.debug("r.text: {}".format(r.text))
    return r.text


@app.route('/listclose')
@login_required
def listcloseonly():
    s = current_user.db_dict()['token']
    json_csv = request.args.get('json_csv')
    top = request.args.get('top', default=0, type=int)
    temp_path = URL_TRACE + '/listCloseOnly/'
    if json_csv == "csv":
        temp_path = temp_path + 'csv'
    if top != 0 and top != -1:
        r = requests.get(temp_path, params={'top': top, 'token': s})
    else:
        r = requests.get(temp_path)
    if r.status_code == 401:
        return abort(401)
    app.logger.debug("r.text: {}".format(r.status_code))
    app.logger.debug("r.text: {}".format(r.text))
    return r.text


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
