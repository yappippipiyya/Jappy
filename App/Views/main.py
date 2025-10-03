from flask import render_template, request, redirect, url_for, abort, session, flash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from flask_login import login_user, logout_user, login_required, current_user

from ..app_init_ import app
from ..auth import flow, User
from ..db.user import UserDatabaseManager

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
  user_db = UserDatabaseManager()
  user_email = current_user.get_id()
  user = user_db.get_user_by_email(user_email)

  if not user:
    return redirect(url_for("resist"))

  return render_template("top.html")


@app.route("/resist", methods=["GET", "POST"])
@login_required
def resist():
  user_db = UserDatabaseManager()
  user_email = current_user.get_id()

  if user_db.get_user_by_email(user_email):
    return redirect(url_for("top"))

  if request.method == "POST":
    nickname = request.form.get("nickname")

    if not nickname or not nickname.strip():
      flash("ニックネームを入力してください。", "error")
      return redirect(url_for("resist"))

    new_user_id = user_db.add_user(email=user_email, name=nickname.strip())

    if new_user_id:
      return redirect(url_for("top"))

    else:
      flash("登録中にエラーが発生しました。もう一度お試しください。", "error")
      return redirect(url_for("resist"))

  return render_template("resist.html", user_email=user_email)
