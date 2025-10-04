import pymysql
from datetime import date, time
import secrets
import string

from .base import _get_connection
from .user import User



class Band:
  """ バンド情報を格納するためのデータクラス """
  def __init__(self, id: int, name: str, token: str, start_date: date, end_date: date, start_time: time, end_time: time):
    self.id = id
    self.name = name
    self.token = token
    self.start_date = start_date
    self.end_date = end_date
    self.start_time = start_time
    self.end_time = end_time

  def __repr__(self):
    return (f"Band(id={self.id}, name='{self.name}', token='{self.token}', "
            f"start_date='{self.start_date}', end_date='{self.end_date}', "
            f"start_time='{self.start_time}', end_time='{self.end_time}')")


class BandDatabaseManager:
  def __init__(self):
    self._get_connection = _get_connection

  def _generate_token(self, length: int = 16) -> str:
    """ 指定された長さのランダムな英数字トークンを生成する """
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for i in range(length))
    return token


  def create(self, name: str, start_date: date, end_date: date, start_time: time, end_time: time, creator_user_id: int) -> tuple[int, str] | None:
    """
    新しいバンドを作成し、そのIDとトークンを返す
    トークンは自動生成される
    """
    token = self._generate_token()
    sql = (
      "INSERT INTO bands (name, token, start_date, end_date, start_time, end_time) "
      "VALUES (%s, %s, %s, %s, %s, %s);"
    )
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (name, token, start_date, end_date, start_time, end_time))
          new_band_id = cur.lastrowid
          if not new_band_id:
            raise pymysql.Error("バンドの作成に失敗しました。")

          # band_userテーブルに作成者を追加
          member_sql = "INSERT INTO band_user (user_id, band_id) VALUES (%s, %s);"
          cur.execute(member_sql, (creator_user_id, new_band_id))

          conn.commit()
          return cur.lastrowid, token

    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return None


  def add_member(self, user_id: int, band_id: int) -> bool:
    """ ユーザーをバンドのメンバーとして追加する """
    sql = "INSERT INTO band_user (user_id, band_id) VALUES (%s, %s);"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (user_id, band_id))
          conn.commit()
          return True

    except pymysql.IntegrityError:
        print("ユーザーは既にこのバンドのメンバーです。")
        return False

    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return False


  def get_band(self, band_id: int | None = None, token: str | None = None) -> Band | None:
    """ id, tokenを指定して単一のバンド情報を取得する """
    if band_id:
      sql = "SELECT id, name, token, start_date, end_date, start_time, end_time FROM bands WHERE id = %s;"
      args = band_id

    elif token:
      sql = "SELECT id, name, token, start_date, end_date, start_time, end_time FROM bands WHERE token = %s;"
      args = token

    else:
      return None

    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (args,))
          result = cur.fetchone()
          return Band(**result) if result else None
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return None


  def get_bands(self, user_id: int) -> list[Band]:
    """ 指定されたユーザーが所属する全てのバンド情報をリストで取得する """
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
            bands_list.append(Band(**row))
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
    return bands_list


  def get_users(self, band_id: int) -> list[User]:
    """
    指定されたバンドIDに所属する全てのユーザー情報をリストで取得する
    """
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
            # Userクラスのインスタンスを作成してリストに追加
            users_list.append(User(**row))
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
    return users_list