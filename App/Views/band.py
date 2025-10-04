from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from datetime import datetime

from App.db.schedule import ScheduleDatabaseManager
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

from collections import defaultdict
from datetime import date, timedelta
def daterange(start_date, end_date):
  for n in range(int((end_date - start_date).days) + 1):
    yield start_date + timedelta(n)

@app.route("/band")
@login_required
def band():
  token = request.args.get('token')
  if not token:
    abort(400, "バンドのトークンが必要です。")

  band_db = BandDatabaseManager()
  band = band_db.get_band(token=token)
  if not band:
    abort(404, "指定されたバンドが見つかりません。")

  # --- ここからが修正・追加部分 ---

  # バンドメンバーを取得し、IDと名前の対応辞書を作成
  members = band_db.get_users(band.id)
  total_members = len(members)
  member_map = {member.id: member.name for member in members}

  # バンドメンバー全員のスケジュールを取得
  schedule_db = ScheduleDatabaseManager()
  schedules = schedule_db.get_schedules(band_id=band.id)

  # スケジュールを集計する辞書を初期化
  schedules_agg = defaultdict(lambda: defaultdict(int))
  schedules_detail = defaultdict(lambda: defaultdict(list)) # ★メンバー名リスト用

  # 全員のスケジュールをループして集計
  for schedule_obj in schedules:
    # メンバー名を取得
    member_name = member_map.get(schedule_obj.user_id)
    if not member_name or not schedule_obj.schedule:
      continue

    for date_obj, hour_list in schedule_obj.schedule.items():
      date_str = date_obj.isoformat()
      for hour, is_available in enumerate(hour_list):
        if is_available:
          schedules_agg[date_str][hour] += 1
          schedules_detail[date_str][hour].append(member_name) # ★リストに名前を追加

  # テンプレートに渡す日付と時間の範囲を生成
  dates_to_display = list(daterange(band.start_date, band.end_date))
  times_to_display = range(band.start_time.hour, band.end_time.hour)

  user_db = UserDatabaseManager()
  creator = user_db.get_user(band.creator_user_id)
  is_creator = False
  if creator:
    if current_user.id == creator.email:
      is_creator = True


  return render_template(
    "band/band.html",
    band=band,
    is_creator=is_creator,
    dates=dates_to_display,
    times=list(times_to_display),
    schedules_agg=schedules_agg,
    schedules_detail=schedules_detail, # ★詳細データを渡す
    total_members=total_members
  )

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


# ファイルの先頭で abort, flash, redirect, url_for, request をインポートしておくこと
# from flask import abort, flash, redirect, url_for, request

@app.route("/band/leave", methods=["POST"])
@login_required
def band_leave():
  token = request.form.get('token')
  if not token:
    abort(400)

  user_db = UserDatabaseManager()
  band_db = BandDatabaseManager()

  user = user_db.get_user(email=current_user.get_id())
  band = band_db.get_band(token=token)

  if not user or not band:
    abort(404)

  # バンド作成者は退出できない仕様（代わりに削除を促す）
  if band.creator_user_id == user.id:
    flash("バンド作成者はバンドを退出できません。バンド自体を削除してください。", "error")
    return redirect(url_for('band', token=token))

  # ここに、BandDatabaseManagerにメンバーを削除するメソッドを実装する必要があります
  # 例: band_db.remove_member(user.id, band.id)
  band_db.remove_member(user.id, band.id)

  flash(f"バンド「{band.name}」から退出しました。", "success")
  return redirect(url_for('bands_list'))


@app.route("/band/delete", methods=["POST"])
@login_required
def band_delete():
  token = request.form.get('token')
  if not token:
    abort(400)

  user_db = UserDatabaseManager()
  band_db = BandDatabaseManager()

  user = user_db.get_user(email=current_user.get_id())
  band = band_db.get_band(token=token)

  if not user or not band:
    abort(404)

  # バンド作成者でなければ削除できないように保護
  if band.creator_user_id != user.id:
    abort(403, "このバンドを削除する権限がありません。")

  # ここに、BandDatabaseManagerにバンドを削除するメソッドを実装する必要があります
  # 例: band_db.delete_band(band.id)
  band_db.delete_band(band.id)

  flash(f"バンド「{band.name}」を削除しました。", "success")
  return redirect(url_for('bands_list'))