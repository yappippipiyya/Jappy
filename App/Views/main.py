from flask import render_template, request, redirect, url_for, abort, session, flash, send_file
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from flask_login import login_user, logout_user, login_required, current_user

from ..app_init_ import app
from ..auth import flow, User
from ..db.user import UserDatabaseManager
from ..db.band import BandDatabaseManager
from ..db.schedule import ScheduleDatabaseManager

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
  app.logger.info(f"State saved to session in /login: {session['state']}")
  return redirect(authorization_url)


@app.route('/callback')
def callback():
  session_state = session.get('state')
  request_state = request.args.get('state')
  app.logger.info(f"Callback received. Session state: {session_state}")
  app.logger.info(f"Callback received. Request state: {request_state}")
  app.logger.info(f"Full session content in /callback: {session}")

  if not session_state or session_state != request_state:
    app.logger.error("State mismatch detected before fetching token!")
    abort(400, "State mismatch error. Please try logging in again.")

  try:
    flow.fetch_token(
      authorization_response=request.url,
      state=session['state']
    )
  except Exception as e:
    app.logger.error(f"Error during fetch_token: {e}")
    app.logger.error(f"Session state at time of error: {session.get('state')}")
    raise

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
  user = user_db.get_user(email=user_email)

  if not user:
    return redirect(url_for("resist"))

  return render_template("top.html")


@app.route("/resist", methods=["GET", "POST"])
@login_required
def resist():
  user_db = UserDatabaseManager()
  user_email = current_user.get_id()

  if user_db.get_user(email=user_email):
    return redirect(url_for("top"))

  if request.method == "POST":
    nickname = request.form.get("nickname")

    if not nickname or not nickname.strip():
      flash("ニックネームを入力してください。", "error")
      return redirect(url_for("resist"))

    new_user_id = user_db.add(email=user_email, name=nickname.strip())

    if new_user_id:
      return redirect(url_for("top"))

    else:
      flash("登録中にエラーが発生しました。もう一度お試しください。", "error")
      return redirect(url_for("resist"))

  return render_template("resist.html", user_email=user_email)


@app.route("/usage")
@login_required
def usage():
  return render_template("usage.html")


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
  user_db = UserDatabaseManager()
  user_email = current_user.get_id()
  user = user_db.get_user(email=user_email)

  if not user:
    return redirect(url_for("resist"))

  if request.method == "POST":
    new_nickname = request.form.get("nickname", "").strip()

    if not new_nickname:
      flash("新しいニックネームを入力してください。", "error")
      return redirect(url_for("account"))

    if new_nickname == user.name:
      flash("現在のニックネームと同じです。", "info")
      return redirect(url_for("account"))

    success = user_db.update(user_id=user.id, email=user.email, name=new_nickname)

    if success:
      flash("ニックネームを更新しました。", "success")
    else:
      flash("更新中にエラーが発生しました。もう一度お試しください。", "error")

    return redirect(url_for("account"))

  return render_template("account.html", user=user)


@app.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
  user_db = UserDatabaseManager()
  user_email = current_user.get_id()
  user = user_db.get_user(email=user_email)

  if not user:
    abort(404)

  success = user_db.delete(user_id=user.id)

  band_db = BandDatabaseManager()
  bands = band_db.get_bands(user.id)
  for band in bands:
    band_db.remove_member(user_id=user.id, band_id=band.id)

  schedule_db = ScheduleDatabaseManager()
  schedule_db.delete_schedules(user.id)

  if success:
    logout_user()
    flash("アカウントを削除しました。", "success")
    return redirect(url_for("index"))
  else:
    flash("アカウントの削除中にエラーが発生しました。", "error")
    return redirect(url_for("account"))