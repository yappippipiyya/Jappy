from flask import flash, redirect, url_for
from flask_login import LoginManager, UserMixin
from google_auth_oauthlib.flow import Flow
from datetime import timedelta

from .app_init_ import app
from const import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, REDIRECT_URI, SECRET_KEY

app.secret_key = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

client_config = {
  "web": {
    "client_id": GOOGLE_CLIENT_ID,
    "project_id": "niischool-login-app",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": GOOGLE_CLIENT_SECRET,
    "redirect_uris": [REDIRECT_URI]
  }
}

flow = Flow.from_client_config(
  client_config=client_config,
  scopes=["openid", "https://www.googleapis.com/auth/userinfo.email"],
  redirect_uri=REDIRECT_URI
)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.unauthorized_handler
def unauthorized():
  """未認証時のリダイレクト処理"""
  flash('ログインが必要です。', 'warning')
  return redirect(url_for("index"))


class User(UserMixin):
  def __init__(self, email):
    self.id = email

@login_manager.user_loader
def load_user(user_id):
  return User(user_id)