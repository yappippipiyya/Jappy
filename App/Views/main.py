import hashlib
import json
import os
import urllib.parse
import urllib.request

from flask import abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..app_init_ import app
from ..auth import User
from ..db.user import UserDatabaseManager

from const import CLIENT_ID, CLIENT_SECRET, LINE_AUTHORIZATION_URL, LINE_TOKEN_URL, LINE_USER_INFO_URL, REDIRECT_URI



@app.route("/")
def index():
  """未ログイン時のトップページ"""
  if current_user.is_authenticated:
    return redirect(url_for("top"))
  return render_template("index.html")


@app.route("/login")
def login():
  """LINEログインを開始する"""
  # CSRF対策のためのstateを生成
  state = hashlib.sha256(os.urandom(32)).hexdigest()
  session["state"] = state

  # LINEの認可URLにリダイレクト
  params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "state": state,
    "scope": "profile openid",  # ユーザープロフィール取得のために'profile'スコープを指定
  }
  return redirect(f"{LINE_AUTHORIZATION_URL}?{urllib.parse.urlencode(params)}")


@app.route("/callback")
def callback():
  """LINEからのコールバックを処理し、ユーザをログインさせる"""
  # stateの検証
  received_state = request.args.get("state")
  expected_state = session.get("state")
  if received_state != expected_state:
    abort(400, "State mismatch error")

  # 認可コードの取得
  code = request.args.get("code")
  if not code:
    abort(400, "Authorization code not found.")

  # アクセストークンの取得
  try:
    token_request_body = urllib.parse.urlencode({
      "grant_type": "authorization_code",
      "code": code,
      "redirect_uri": REDIRECT_URI,
      "client_id": CLIENT_ID,
      "client_secret": CLIENT_SECRET,
    }).encode("utf-8")

    req = urllib.request.Request(
      LINE_TOKEN_URL, data=token_request_body, method="POST"
    )
    with urllib.request.urlopen(req) as f:
      token_response = json.loads(f.read())

    access_token = token_response.get("access_token")
    if not access_token:
      abort(500, "Access token not found in response.")

  except urllib.error.URLError as e:
    print(f"Error fetching token: {e.reason}")
    abort(500, "Failed to get access token.")

  # ユーザープロフィールの取得
  try:
    headers = {"Authorization": f"Bearer {access_token}"}
    req = urllib.request.Request(LINE_USER_INFO_URL, headers=headers, method="GET")
    with urllib.request.urlopen(req) as f:
      user_profile = json.loads(f.read())

    # LINEのプロフィールから'userId'を取得
    user_id = user_profile.get("userId")
    if not user_id:
      abort(500, "User ID not found in LINE profile.")

    # ユーザーオブジェクトを作成し、ログイン処理
    user = User(user_id)
    login_user(user, remember=True)
    return redirect(url_for("top"))

  except urllib.error.URLError as e:
    print(f"Error fetching user profile: {e.reason}")
    abort(500, "Failed to get user profile.")


@app.route("/logout")
@login_required
def logout():
  """ログアウト処理"""
  logout_user()
  return redirect(url_for("index"))


@app.route("/top")
@login_required
def top():
  """ログイン後のトップページ"""
  user_db = UserDatabaseManager()
  user_id = current_user.get_id()
  user = user_db.get_user(line_user_id=user_id)

  # ユーザーがDBに存在しない場合は登録ページへ
  if not user:
    return redirect(url_for("resist"))

  return render_template("top.html")


@app.route("/resist", methods=["GET", "POST"])
@login_required
def resist():
  """新規ユーザー登録ページ"""
  user_db = UserDatabaseManager()
  user_id = current_user.get_id()

  # 既に登録済みの場合はトップページへ
  if user_db.get_user(user_id=user_id):
    return redirect(url_for("top"))

  if request.method == "POST":
    nickname = request.form.get("nickname")

    if not nickname or not nickname.strip():
      flash("ニックネームを入力してください。", "error")
      return redirect(url_for("resist"))

    # データベースにユーザー情報を追加
    new_user_id_in_db = user_db.add(line_user_id=user_id, name=nickname.strip())

    if new_user_id_in_db:
      return redirect(url_for("top"))
    else:
      flash("登録中にエラーが発生しました。もう一度お試しください。", "error")
      return redirect(url_for("resist"))

  return render_template("resist.html", line_user_id=user_id)