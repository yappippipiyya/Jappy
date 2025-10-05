from datetime import date, timedelta

from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..app_init_ import app
from ..db.band import BandDatabaseManager
from ..db.schedule import ScheduleDatabaseManager
from ..db.user import UserDatabaseManager



def daterange(start_date, end_date):
  """指定された開始日から終了日までの日付を1日ずつ生成する。"""
  for n in range(int((end_date - start_date).days) + 1):
    yield start_date + timedelta(n)


@app.route("/schedule-manage")
@login_required
def schedule_manage():
  user_db_manager = UserDatabaseManager()
  band_db_manager = BandDatabaseManager()
  schedule_db_manager = ScheduleDatabaseManager()

  user = user_db_manager.get_user(line_user_id=current_user.id)
  if not user:
    flash("ユーザー情報が見つかりません。", "error")
    return redirect(url_for("top"))

  user_bands = band_db_manager.get_bands(user.id)

  # クエリパラメータから表示対象のband_idを取得（指定がなければデフォルト=0）
  try:
    selected_band_id = int(request.args.get("band_id", 0))
  except (ValueError, TypeError):
    selected_band_id = 0

  # ユーザーの全スケジュール情報を取得し、band_idをキーとする辞書に変換
  all_schedules = schedule_db_manager.get_schedules(user_id=user.id)
  schedules_by_band = {s.band_id: s.schedule for s in all_schedules}

  # 表示するスケジュールを決定
  current_schedule = schedules_by_band.get(selected_band_id, {})

  # 表示範囲の初期化
  dates_to_display = []
  times_to_display = range(24)

  if selected_band_id == 0:  # デフォルトスケジュール表示
    if not user_bands:
      # バンドに未所属の場合、今日から14日間を表示
      start_date = date.today()
      end_date = start_date + timedelta(days=13)
    else:
      # 全所属バンドの期間をカバーする日付範囲を計算
      start_date = min(band.start_date for band in user_bands)
      end_date = max(band.end_date for band in user_bands)
    dates_to_display = list(daterange(start_date, end_date))

  else:  # 特定のバンドのスケジュール表示
    selected_band = next(
      (band for band in user_bands if band.id == selected_band_id), None
    )
    if not selected_band:
      # ユーザーが所属していないバンドIDが指定された場合はアクセスを拒否
      abort(403, "このバンドへのアクセス権がありません。")

    # バンドの期間と時間に合わせて表示範囲を制限
    dates_to_display = list(
      daterange(selected_band.start_date, selected_band.end_date)
    )
    times_to_display = range(
      selected_band.start_time.hour, selected_band.end_time.hour
    )

  # テンプレートで扱いやすいように、スケジュール辞書のキーをISO形式の文字列に変換
  current_schedule_str_keys = {
    d.isoformat(): v for d, v in current_schedule.items()
  }

  return render_template(
    "schedule/manage.html",
    bands=user_bands,
    selected_band_id=selected_band_id,
    dates=dates_to_display,
    times=list(times_to_display),  # rangeオブジェクトをリストに変換
    schedule_data=current_schedule_str_keys,
  )


@app.route("/schedule-manage/save", methods=["POST"])
@login_required
def save_schedule():
  """スケジュールをDBに保存するためのエンドポイント"""
  user_db_manager = UserDatabaseManager()
  schedule_db_manager = ScheduleDatabaseManager()

  user = user_db_manager.get_user(line_user_id=current_user.id)
  if not user:
    return jsonify({"status": "error", "message": "User not found"}), 404

  data = request.get_json()
  if not data or "schedule" not in data or "band_id" not in data:
    return jsonify({"status": "error", "message": "Invalid data"}), 400

  band_id = data["band_id"]
  schedule_str_keys = data["schedule"]

  # キーをdateオブジェクトに変換し、チェックが入っている日付のみを保存対象とする
  schedule_to_save = {}
  for date_str, time_list in schedule_str_keys.items():
    if any(time_list):  # リストにtrue相当の値が1つでも含まれていれば保存
      try:
        schedule_date = date.fromisoformat(date_str)
        schedule_to_save[schedule_date] = time_list
      except ValueError:
        # 不正な日付フォーマットはスキップ
        continue

  schedule_db_manager.update_schedule(user.id, schedule_to_save, band_id)
  return jsonify({"status": "success", "message": "Schedule updated."})


@app.route("/schedule-manage/default-schedule", methods=["GET"])
@login_required
def get_default_schedule():
  """「デフォルトを適用」機能のために、デフォルトのスケジュール情報を返すエンドポイント"""
  user_db_manager = UserDatabaseManager()
  schedule_db_manager = ScheduleDatabaseManager()

  user = user_db_manager.get_user(line_user_id=current_user.id)
  if not user:
    return jsonify({"status": "error", "message": "User not found"}), 404

  # band_id=0 のスケジュールを取得
  schedules = schedule_db_manager.get_schedules(user_id=user.id)
  default_schedule_obj = next((s for s in schedules if s.band_id == 0), None)

  if default_schedule_obj and default_schedule_obj.schedule:
    # JSONで返せるようにキーを文字列に変換
    default_schedule_str_keys = {
      d.isoformat(): v for d, v in default_schedule_obj.schedule.items()
    }
    return jsonify(default_schedule_str_keys)
  else:
    return jsonify({})