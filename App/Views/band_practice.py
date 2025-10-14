from datetime import date, timedelta

from flask import abort, jsonify, redirect, render_template, request, url_for, flash
from flask_login import current_user, login_required

from ..app_init_ import app
from ..db.band import BandDatabaseManager
from ..db.schedule import ScheduleDatabaseManager
from ..db.user import UserDatabaseManager



def daterange(start_date, end_date):
  """指定された開始日から終了日までの日付を1日ずつ生成する。"""
  for n in range(int((end_date - start_date).days) + 1):
    yield start_date + timedelta(n)


@app.route("/band-practice")
@login_required
def band_practice():
  """バンド練習のスケジュールページを表示する。
  閲覧モードと特定のバンドの編集モードを切り替える。
  """
  user_db_manager = UserDatabaseManager()
  band_db_manager = BandDatabaseManager()
  schedule_db_manager = ScheduleDatabaseManager()

  user = user_db_manager.get_user(email=current_user.id)
  if not user:
    flash("ユーザー情報が見つかりません。", "error")
    return redirect(url_for("top"))

  user_bands = band_db_manager.get_bands(user.id)

  # クエリパラメータから表示対象を取得 ("view" または band_id)
  selected_band_id_str = request.args.get("band_id", "view")

  # 表示期間を所属バンド全体から計算
  if not user_bands:
    start_date = date.today()
    end_date = start_date + timedelta(days=13)
    times_to_display = range(24)
  else:
    start_date = min(band.start_date for band in user_bands)
    end_date = max(band.end_date for band in user_bands)
    start_time = min(band.start_time for band in user_bands)
    end_time = max(band.end_time for band in user_bands)
    times_to_display = range(start_time.hour, end_time.hour + 1)

  dates_to_display = list(daterange(start_date, end_date))

  # モードに応じて処理を分岐
  if selected_band_id_str == "view":
    # --- 閲覧モード ---
    band_schedules = {}
    band_colors = {}
    colors = ["#ffadad", "#a5dfff", "#b6ffbc", "#ffe3bf", "#a79bff", "#ffa0b6", "#bdb2ff", "#ffc6ff"]

    for i, band in enumerate(user_bands):
      schedules = schedule_db_manager.get_schedules(band_id=band.id)
      # user_id=0 のスケジュール(バンド練)を探す
      schedule_obj = next((s for s in schedules if s.user_id == 0), None)

      if schedule_obj and schedule_obj.schedule:
        schedule_str_keys = {d.isoformat(): v for d, v in schedule_obj.schedule.items()}
        band_schedules[band.id] = schedule_str_keys
      band_colors[band.id] = colors[i % len(colors)]

    return render_template(
      "band-practice/band-practice.html",
      bands=user_bands,
      selected_band_id="view",
      dates=dates_to_display,
      times=list(times_to_display),
      band_schedules=band_schedules,
      band_colors=band_colors,
      view_mode=True
    )
  else:
    # --- 編集モード ---
    try:
      selected_band_id = int(selected_band_id_str)
    except (ValueError, TypeError):
      abort(400, "無効なバンドIDです。")

    selected_band = next((b for b in user_bands if b.id == selected_band_id), None)
    if not selected_band:
      abort(403, "このバンドへのアクセス権がありません。")

    schedules = schedule_db_manager.get_schedules(band_id=selected_band_id)
    schedule_obj = next((s for s in schedules if s.user_id == 0), None)
    current_schedule = schedule_obj.schedule if schedule_obj else {}

    current_schedule_str_keys = {d.isoformat(): v for d, v in current_schedule.items()}

    # 表示範囲を該当バンドの期間に限定
    dates_to_display = list(daterange(selected_band.start_date, selected_band.end_date))
    times_to_display = range(selected_band.start_time.hour, selected_band.end_time.hour + 1)

    return render_template(
      "band-practice/band-practice.html",
      bands=user_bands,
      selected_band_id=selected_band_id,
      dates=dates_to_display,
      times=list(times_to_display),
      schedule_data=current_schedule_str_keys,
      view_mode=False
    )


@app.route("/band-practice/save", methods=["POST"])
@login_required
def save_band_practice():
  """バンド練のスケジュールをDBに保存する"""
  user_db_manager = UserDatabaseManager()
  band_db_manager = BandDatabaseManager()
  schedule_db_manager = ScheduleDatabaseManager()

  user = user_db_manager.get_user(email=current_user.id)
  if not user:
    return jsonify({"status": "error", "message": "User not found"}), 404

  data = request.get_json()
  if not data or "schedule" not in data or "band_id" not in data:
    return jsonify({"status": "error", "message": "Invalid data"}), 400

  try:
    band_id = int(data["band_id"])
  except (ValueError, TypeError):
    return jsonify({"status": "error", "message": "Invalid band ID"}), 400

  # ユーザーがそのバンドに所属しているか検証
  user_bands_ids = [b.id for b in band_db_manager.get_bands(user.id)]
  if band_id not in user_bands_ids:
    return jsonify({"status": "error", "message": "Permission denied"}), 403

  schedule_str_keys = data["schedule"]
  schedule_to_save = {}
  for date_str, time_list in schedule_str_keys.items():
    if any(time_list):
      try:
        schedule_date = date.fromisoformat(date_str)
        schedule_to_save[schedule_date] = time_list
      except ValueError:
        continue

  # user_id=0 でバンド練のスケジュールを更新
  schedule_db_manager.update_schedule(user_id=0, schedule=schedule_to_save, band_id=band_id, comment="")

  return jsonify({"status": "success", "message": "Band practice schedule updated."})