from collections import defaultdict
from datetime import datetime, timedelta

from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from App.db.schedule import ScheduleDatabaseManager
from ..app_init_ import app
from ..db.user import  UserDatabaseManager
from ..db.band import  BandDatabaseManager



def daterange(start_date, end_date):
  """指定された開始日から終了日までの日付を生成するジェネレータ"""
  for n in range(int((end_date - start_date).days) + 1):
    yield start_date + timedelta(n)


@app.route("/band-gen", methods=["GET", "POST"])
@login_required
def band_gen():
  """バンド作成フォームの表示と、フォーム送信を処理する"""
  if request.method == "POST":
    band_name = request.form.get("band-name")
    start_date_str = request.form.get("start-date")
    end_date_str = request.form.get("end-date")
    start_time_str = request.form.get("start-time")
    end_time_str = request.form.get("end-time")

    if not (band_name and start_date_str and end_date_str and start_time_str and end_time_str):
      flash("すべての項目を入力してください。", "error")
      return redirect(url_for("band_gen"))

    try:
      start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
      end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
      start_time = datetime.strptime(start_time_str, '%H:%M').time()
      end_time = datetime.strptime(end_time_str, '%H:%M').time()
    except (ValueError, TypeError):
      flash("日付または時刻の形式が正しくありません。", "error")
      return redirect(url_for("band_gen"))

    user_db = UserDatabaseManager()
    user = user_db.get_user(email=current_user.get_id())
    if not user:
      return redirect(url_for("logout"))

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

  return render_template("band/band-gen.html")


@app.route("/bands")
@login_required
def bands_list():
  """ユーザーが所属するバンドの一覧を表示する"""
  user_db = UserDatabaseManager()
  user = user_db.get_user(email=current_user.get_id())
  if not user:
    return redirect(url_for("logout"))

  band_db = BandDatabaseManager()
  bands = band_db.get_bands(user_id=user.id)
  users_dict = {
    band.id: ", ".join([user.name for user in band_db.get_users(band.id)])
    for band in bands
  }

  return render_template("band/bands.html", bands=bands, users_dict=users_dict)


@app.route("/band")
@login_required
def band():
  """バンドの詳細ページを表示し、メンバーのスケジュールを集計する"""
  token = request.args.get('token')
  if not token:
    abort(400, "バンドのトークンが必要です。")

  band_db = BandDatabaseManager()
  band = band_db.get_band(token=token)
  if not band:
    abort(404, "指定されたバンドが見つかりません。")

  members = band_db.get_users(band.id)
  total_members = len(members)
  member_map = {member.id: member.name for member in members}

  schedule_db = ScheduleDatabaseManager()
  schedules = schedule_db.get_schedules(band_id=band.id)

  # 日付と時間ごとの参加可能人数とメンバー名を集計
  schedules_agg = defaultdict(lambda: defaultdict(int))
  schedules_detail = defaultdict(lambda: defaultdict(list))

  for schedule_obj in schedules:
    member_name = member_map.get(schedule_obj.user_id)
    if not member_name or not schedule_obj.schedule:
      continue

    for date_obj, hour_list in schedule_obj.schedule.items():
      date_str = date_obj.isoformat()
      for hour, is_available in enumerate(hour_list):
        if is_available:
          schedules_agg[date_str][hour] += 1
          schedules_detail[date_str][hour].append(member_name)

  dates_to_display = list(daterange(band.start_date, band.end_date))
  times_to_display = range(band.start_time.hour, band.end_time.hour+1)

  user_db = UserDatabaseManager()
  creator = user_db.get_user(band.creator_user_id)
  is_creator = creator and current_user.id == creator.email

  return render_template(
    "band/band.html",
    band=band,
    is_creator=is_creator,
    dates=dates_to_display,
    times=list(times_to_display),
    schedules_agg=schedules_agg,
    schedules_detail=schedules_detail,
    total_members=total_members
  )


@app.route("/join")
@login_required
def join_band():
  """招待トークンを使ってバンドに参加する"""
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

  if band_db.add_member(user.id, band.id):
    flash(f"バンド「{band.name}」に参加しました！", "success")
  else:
    flash(f"すでにバンド「{band.name}」のメンバーです。", "info")

  return redirect(url_for('bands_list'))


@app.route("/band/edit", methods=["GET", "POST"])
@login_required
def band_edit():
  """バンド情報の編集ページを表示・処理する (作成者のみ)"""
  token = request.args.get('token') if request.method == "GET" else request.form.get('token')
  if not token:
    abort(400, "バンドのトークンが必要です。")

  user_db = UserDatabaseManager()
  band_db = BandDatabaseManager()
  user = user_db.get_user(email=current_user.get_id())
  band = band_db.get_band(token=token)

  if not band:
    abort(404, "指定されたバンドが見つかりません。")
  if not user or band.creator_user_id != user.id:
    abort(403, "このバンドを編集する権限がありません。")

  if request.method == "POST":
    band_name = request.form.get("band-name")
    start_date_str = request.form.get("start-date")
    end_date_str = request.form.get("end-date")
    start_time_str = request.form.get("start-time")
    end_time_str = request.form.get("end-time")

    if not (band_name and start_date_str and end_date_str and start_time_str and end_time_str):
      flash("すべての項目を入力してください。", "error")
      return redirect(url_for("band_edit", token=token))

    try:
      start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
      end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
      start_time = datetime.strptime(start_time_str, '%H:%M').time()
      end_time = datetime.strptime(end_time_str, '%H:%M').time()
    except (ValueError, TypeError):
      flash("日付または時刻の形式が正しくありません。", "error")
      return redirect(url_for("band_edit", token=token))

    if band_db.update_band(band.id, band_name, start_date, end_date, start_time, end_time):
      flash("バンド情報を更新しました。", "success")
      return redirect(url_for("band", token=token))
    else:
      flash("バンド情報の更新に失敗しました。", "error")
      return redirect(url_for("band_edit", token=token))

  # GETリクエストの場合
  return render_template("band/band-edit.html", band=band)


@app.route("/band/leave", methods=["POST"])
@login_required
def band_leave():
  """所属しているバンドから退出する"""
  token = request.form.get('token')
  if not token:
    abort(400)

  user_db = UserDatabaseManager()
  band_db = BandDatabaseManager()
  user = user_db.get_user(email=current_user.get_id())
  band = band_db.get_band(token=token)

  if not user or not band:
    abort(404)

  # バンド作成者は退出できない
  if band.creator_user_id == user.id:
    flash("バンド作成者はバンドを退出できません。バンド自体を削除してください。", "error")
    return redirect(url_for('band', token=token))

  band_db.remove_member(user.id, band.id)
  flash(f"バンド「{band.name}」から退出しました。", "success")
  return redirect(url_for('bands_list'))


@app.route("/band/delete", methods=["POST"])
@login_required
def band_delete():
  """バンドを削除する (作成者のみ)"""
  token = request.form.get('token')
  if not token:
    abort(400)

  user_db = UserDatabaseManager()
  band_db = BandDatabaseManager()
  user = user_db.get_user(email=current_user.get_id())
  band = band_db.get_band(token=token)

  if not user or not band:
    abort(404)

  # バンド作成者でなければ削除できない
  if band.creator_user_id != user.id:
    abort(403, "このバンドを削除する権限がありません。")

  band_db.delete_band(band.id)
  flash(f"バンド「{band.name}」を削除しました。", "success")
  return redirect(url_for('bands_list'))