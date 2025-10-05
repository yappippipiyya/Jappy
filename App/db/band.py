import pymysql
import secrets
import string
from datetime import date, time, timedelta

from .base import _get_connection
from .user import User



def _timedelta_to_time(td: timedelta) -> time:
  """
  pymysqlが返すtimedeltaオブジェクトをtimeオブジェクトに変換するヘルパー関数
  """
  if not isinstance(td, timedelta):
    return td

  total_seconds = int(td.total_seconds())
  # 1日の秒数（86400秒）で剰余をとり、日付の繰り越しを無視して時間のみを抽出
  total_seconds %= 86400
  hour, remainder = divmod(total_seconds, 3600)
  minute, second = divmod(remainder, 60)

  return time(hour, minute, second)


class Band:
  """バンド情報を格納するためのデータクラス"""

  def __init__(
    self, id: int, name: str, creator_user_id: int, token: str,
    start_date: date, end_date: date, start_time: time, end_time: time
  ):
    self.id = id
    self.name = name
    self.creator_user_id = creator_user_id
    self.token = token
    self.start_date = start_date
    self.end_date = end_date
    self.start_time = start_time
    self.end_time = end_time

  def __repr__(self):
    return (
      f"Band(id={self.id}, name='{self.name}', "
      f"creator_user_id='{self.creator_user_id}', token='{self.token}', "
      f"start_date='{self.start_date}', end_date='{self.end_date}', "
      f"start_time='{self.start_time}', end_time='{self.end_time}')"
    )


class BandDatabaseManager:
  """バンドに関連するデータベース操作を管理するクラス"""

  def __init__(self):
    self._get_connection = _get_connection

  # --- 書き込み操作 (Create, Update, Delete) ---

  def create(
    self, name: str, start_date: date, end_date: date,
    start_time: time, end_time: time, creator_user_id: int
  ) -> tuple[int, str] | None:
    """
    新しいバンドを作成し、作成者をメンバーとして自動的に追加する。
    成功した場合、(バンドID, トークン) を返す。
    """
    token = self._generate_token()
    sql = """
      INSERT INTO bands
        (name, creator_user_id, token, start_date, end_date, start_time, end_time)
      VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (
            name, creator_user_id, token, start_date,
            end_date, start_time, end_time
          ))
          new_band_id = cur.lastrowid
          if not new_band_id:
            raise pymysql.Error("バンドの作成に失敗しました。")

          # 作成者を最初のメンバーとして追加
          member_sql = "INSERT INTO band_user (user_id, band_id) VALUES (%s, %s);"
          cur.execute(member_sql, (creator_user_id, new_band_id))

          conn.commit()
          return new_band_id, token
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました (create): {e}")
      return None


  def add_member(self, user_id: int, band_id: int) -> bool:
    """ユーザーをバンドのメンバーとして追加する"""
    sql = "INSERT INTO band_user (user_id, band_id) VALUES (%s, %s);"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (user_id, band_id))
          conn.commit()
          return True
    except pymysql.IntegrityError:
      # (user_id, band_id) の組み合わせはUNIQUE制約があるため、
      # 既にメンバーの場合はこのエラーが発生する
      print("ユーザーは既にこのバンドのメンバーです。")
      return False
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました (add_member): {e}")
      return False


  def remove_member(self, user_id: int, band_id: int) -> bool:
    """
    バンドから指定されたユーザーを脱退させ、関連するスケジュールも削除する
    """
    sql = "DELETE FROM band_user WHERE user_id = %s AND band_id = %s;"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          rows_affected = cur.execute(sql, (user_id, band_id))

          # 注意: band_id=0 (個人のデフォルトスケジュール) は削除しない
          if band_id != 0:
            schedule_sql = "DELETE FROM schedules WHERE user_id = %s AND band_id = %s;"
            cur.execute(schedule_sql, (user_id, band_id))

          conn.commit()
          # 1行以上削除されていれば成功
          return rows_affected > 0
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました (remove_member): {e}")
      return False


  def delete_band(self, band_id: int) -> bool:
    """
    バンド自体を削除する。関連する全てのデータも削除される。
    """
    # 外部キー制約のため、削除する順番が重要
    # 1. schedules -> 2. band_user -> 3. bands
    sqls = [
      "DELETE FROM schedules WHERE band_id = %s;",
      "DELETE FROM band_user WHERE band_id = %s;",
      "DELETE FROM bands WHERE id = %s;"
    ]
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          for sql in sqls:
            cur.execute(sql, (band_id,))
          conn.commit()
          return True
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました (delete_band): {e}")
      return False

  # --- 読み取り操作 (Read) ---

  def get_band(self, band_id: int | None = None, token: str | None = None) -> Band | None:
    """idまたはtokenを指定して、単一のバンド情報を取得する"""
    if band_id:
      sql = "SELECT * FROM bands WHERE id = %s;"
      args = (band_id,)
    elif token:
      sql = "SELECT * FROM bands WHERE token = %s;"
      args = (token,)
    else:
      return None

    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, args)
          result = cur.fetchone()
          if result:
            result['start_time'] = _timedelta_to_time(result['start_time'])
            result['end_time'] = _timedelta_to_time(result['end_time'])
            return Band(**result)
          return None
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました (get_band): {e}")
      return None


  def get_bands(self, user_id: int) -> list[Band]:
    """指定されたユーザーが所属する全てのバンド情報をリストで取得する"""
    sql = """
      SELECT b.*
      FROM bands b
      JOIN band_user bu ON b.id = bu.band_id
      WHERE bu.user_id = %s
      ORDER BY b.id DESC;
    """
    bands_list: list[Band] = []
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (user_id,))
          results = cur.fetchall()
          for row in results:
            row['start_time'] = _timedelta_to_time(row['start_time'])
            row['end_time'] = _timedelta_to_time(row['end_time'])
            bands_list.append(Band(**row))
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました (get_bands): {e}")
    return bands_list


  def get_users(self, band_id: int) -> list[User]:
    """指定されたバンドIDに所属する全てのユーザー情報をリストで取得する"""
    sql = """
      SELECT u.id, u.line_user_id, u.name
      FROM users u
      JOIN band_user bu ON u.id = bu.user_id
      WHERE bu.band_id = %s;
    """
    users_list: list[User] = []
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (band_id,))
          results = cur.fetchall()
          for row in results:
            users_list.append(User(**row))
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました (get_users): {e}")
    return users_list

  # --- 内部ヘルパーメソッド ---

  def _generate_token(self, length: int = 16) -> str:
    """指定された長さのランダムな英数字トークンを生成する"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))