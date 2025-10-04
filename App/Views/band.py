from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from datetime import datetime

from ..app_init_ import app
from ..db.user import User, UserDatabaseManager
from ..db.band import Band, BandDatabaseManager

# バンド作成フォームの表示と、フォーム送信の処理
@app.route("/band-gen", methods=["GET", "POST"])
@login_required
def band_gen():
  if request.method == "POST":
    # フォームからデータを取得
    band_name = request.form.get("band-name")
    start_date_str = request.form.get("start-date")
    end_date_str = request.form.get("end-date")
    start_time_str = request.form.get("start-time")
    end_time_str = request.form.get("end-time")

    # 簡単なバリデーション
    if not (band_name and start_date_str and end_date_str and start_time_str and end_time_str):
      flash("すべての項目を入力してください。", "error")
      return redirect(url_for("band_gen"))

    try:
      # 文字列をdate型、time型に変換
      start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
      end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
      start_time = datetime.strptime(start_time_str, '%H:%M').time()
      end_time = datetime.strptime(end_time_str, '%H:%M').time()
    except (ValueError, TypeError):
      flash("日付または時刻の形式が正しくありません。", "error")
      return redirect(url_for("band_gen"))

    # ログイン中のユーザー情報を取得
    user_db = UserDatabaseManager()
    user = user_db.get_user(email=current_user.get_id())
    if not user:
      # ユーザー情報が取得できなければエラーハンドリング（例: ログアウト）
      return redirect(url_for("logout"))

    # データベースにバンドを作成し、作成者をメンバーに追加
    band_db = BandDatabaseManager()
    token = band_db.create(
      name=band_name,
      start_date=start_date,
      end_date=end_date,
      start_time=start_time,
      end_time=end_time,
      creator_user_id=user.id
    )

    if token:
      return redirect(url_for("bands_list"))

    else:
      flash("バンドの作成に失敗しました。もう一度お試しください。", "error")
      return redirect(url_for("band_gen"))

  # GETリクエストの場合は作成フォームを表示
  return render_template("band/band-gen.html")


@app.route("/bands")
@login_required
def bands_list():
  user_db = UserDatabaseManager()
  user = user_db.get_user(email=current_user.get_id())
  if not user:
    return redirect(url_for("logout"))

  # db/band.py に get_bands_by_user_id メソッドが別途必要
  band_db = BandDatabaseManager()
  bands = band_db.get_bands(user_id=user.id) # ユーザーIDで所属バンドを取得
  users_dict = {band.id: ", ".join([user.name for user in band_db.get_users(band.id)]) for band in bands}

  return render_template("band/bands.html", bands=bands, users_dict=users_dict)


@app.route("/join")
@login_required
def join_band():
  token = request.args.get('token')
  if not token:
    abort(400, "招待トークンが必要です。")

  band_db = BandDatabaseManager()
  band = band_db.get_band(token=token)
  if not band:
    abort(404, "指定されたバンドが見つかりません。")

  user_db = UserDatabaseManager()
  user = user_db.get_user(email=current_user.get_id())
  if not user:
    return redirect(url_for("logout"))

  success = band_db.add_member(user.id, band.id)

  if success:
    flash(f"バンド「{band.name}」に参加しました！", "success")
  else:
    flash(f"すでにバンド「{band.name}」のメンバーです。", "info")
  
  # 参加処理が終わったら、新しく作ったバンド一覧ページにリダイレクト
  return redirect(url_for('bands_list'))