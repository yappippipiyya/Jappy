import pymysql
from datetime import date, time
import secrets
import string

from .base import _get_connection



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


  def create_band(self, name: str, start_date: date, end_date: date, start_time: time, end_time: time) -> tuple[int, str] | None:
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
          conn.commit()
          return cur.lastrowid, token
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return None


  def get_band_by_id(self, band_id: int) -> Band | None:
    """ idを指定して単一のバンド情報を取得する """
    sql = "SELECT id, name, token, start_date, end_date, start_time, end_time FROM bands WHERE id = %s;"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (band_id,))
          result = cur.fetchone()
          return Band(**result) if result else None
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return None


  def get_band_by_token(self, token: str) -> Band | None:
    """ tokenを指定して単一のバンド情報を取得する """
    sql = "SELECT id, name, token, start_date, end_date, start_time, end_time FROM bands WHERE token = %s;"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (token,))
          result = cur.fetchone()
          return Band(**result) if result else None
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return None