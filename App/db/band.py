import psycopg
import secrets
import string
from datetime import date, time

from .base import _get_connection
from .user import User


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
    # RETURNING id を追加して、挿入した行のIDを取得する
    sql = """
      INSERT INTO bands
        (name, creator_user_id, token, start_date, end_date, start_time, end_time)
      VALUES (%s, %s, %s, %s, %s, %s, %s)
      RETURNING id;
    """
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (
            name, creator_user_id, token, start_date,
            end_date, start_time, end_time
          ))

          # fetchone()で結果を取得する
          result = cur.fetchone()
          if not result:
            raise psycopg.Error("バンドの作成に失敗しました。")
          new_band_id = result['id']

          # 作成者を最初のメンバーとして追加
          member_sql = "INSERT INTO band_user (user_id, band_id) VALUES (%s, %s);"
          cur.execute(member_sql, (creator_user_id, new_band_id))

          conn.commit()
          return new_band_id, token
    except psycopg.Error as e:
      print(f"データベースエラーが発生しました (create): {e}")
      return None


  def update_band(
    self, band_id: int, name: str, start_date: date,
    end_date: date, start_time: time, end_time: time
  ) -> bool:
    """指定されたバンドIDの情報を更新する"""
    sql = """
      UPDATE bands
      SET name = %s, start_date = %s, end_date = %s, start_time = %s, end_time = %s
      WHERE id = %s;
    """
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (
            name, start_date, end_date,
            start_time, end_time, band_id
          ))
          conn.commit()
          # 1行以上更新されていれば成功
          return cur.rowcount > 0

    except psycopg.Error as e:
      print(f"データベースエラーが発生しました (update_band): {e}")
      return False


  def add_member(self, user_id: int, band_id: int) -> bool:
    """ユーザーをバンドのメンバーとして追加する"""
    sql = "INSERT INTO band_user (user_id, band_id) VALUES (%s, %s);"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (user_id, band_id))
          conn.commit()
          return True
    except psycopg.IntegrityError:
      # (user_id, band_id) の組み合わせはUNIQUE制約があるため、
      # 既にメンバーの場合はこのエラーが発生する
      print("ユーザーは既にこのバンドのメンバーです。")
      return False
    except psycopg.Error as e:
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
          cur.execute(sql, (user_id, band_id))
          rows_affected = cur.rowcount

          # 注意: band_id=0 (個人のデフォルトスケジュール) は削除しない
          if band_id != 0:
            schedule_sql = "DELETE FROM schedules WHERE user_id = %s AND band_id = %s;"
            cur.execute(schedule_sql, (user_id, band_id))

          conn.commit()
          # 1行以上削除されていれば成功
          return rows_affected > 0
    except psycopg.Error as e:
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
    except psycopg.Error as e:
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
            # psycopgはtimeオブジェクトを直接返すため、timedeltaからの変換は不要
            return Band(**result)
          return None
    except psycopg.Error as e:
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
            # psycopgはtimeオブジェクトを直接返すため、timedeltaからの変換は不要
            bands_list.append(Band(**row))
    except psycopg.Error as e:
      print(f"データベースエラーが発生しました (get_bands): {e}")

    bands_list.sort(key=lambda x: x.end_date, reverse=True)
    print(bands_list)
    return bands_list


  def get_users(self, band_id: int) -> list[User]:
    """指定されたバンドIDに所属する全てのユーザー情報をリストで取得する"""
    sql = """
      SELECT u.id, u.email, u.name
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
    except psycopg.Error as e:
      print(f"データベースエラーが発生しました (get_users): {e}")
    return users_list

  # --- 内部ヘルパーメソッド ---

  def _generate_token(self, length: int = 16) -> str:
    """指定された長さのランダムな英数字トークンを生成する"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))