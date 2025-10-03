from flask import render_template, request, redirect, url_for, abort, session, flash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from flask_login import login_user, logout_user, login_required, current_user

from ..app_init_ import app
from ..auth import flow, User
from ..db.user import UserDatabaseManager

from const import GOOGLE_CLIENT_ID



@app.route("/band-gen")
@login_required
def band_gen():
  return render_template('band-gen/band-gen.html')
