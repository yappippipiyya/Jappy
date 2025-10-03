from flask import render_template, request, redirect, url_for, abort, session, flash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from flask_login import login_user, logout_user, login_required, current_user

from ..app_init_ import app
from ..auth import flow, User

from const import GOOGLE_CLIENT_ID



@app.route("/")
def index():
  if current_user.is_authenticated:
    return redirect("top")

  return render_template('index.html')


@app.route('/login')
def login():
  authorization_url, state = flow.authorization_url()
  session['state'] = state
  return redirect(authorization_url)


@app.route('/callback')
def callback():
  flow.fetch_token(authorization_response=request.url)

  if not session['state'] == request.args['state']:
      abort(400, "State mismatch error")

  credentials = flow.credentials
  request_session = google_requests.Request()

  id_info = id_token.verify_oauth2_token(
    credentials.id_token, request_session, GOOGLE_CLIENT_ID # type: ignore
  )
  user_email = id_info.get("email")

  user = User(user_email)
  login_user(user, remember=True)

  return redirect(url_for('top'))


@app.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect('/')


@app.route("/top")
@login_required
def top():
  return render_template("top.html")