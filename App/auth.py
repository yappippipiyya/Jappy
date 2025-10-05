from flask import flash, redirect, url_for
from flask_login import LoginManager, UserMixin
from datetime import timedelta

from .app_init_ import app
from const import SECRET_KEY

app.secret_key = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)


# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.unauthorized_handler
def unauthorized():
  """未認証時のリダイレクト処理"""
  flash('ログインが必要です。', 'warning')
  return redirect(url_for("index"))


class User(UserMixin):
  def __init__(self, line_user_id):
    self.id = line_user_id

@login_manager.user_loader
def load_user(user_id):
  return User(user_id)