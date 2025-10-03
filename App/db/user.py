import pymysql
from .base import _get_connection

class User:
  """ ユーザー情報を格納するためのデータクラス """
  # DBのカラム名 'id' に合わせました
  def __init__(self, id: int, email: str, name: str):
    self.id = id
    self.email = email
    self.name = name

  def __repr__(self):
    return f"User(id={self.id}, email='{self.email}', name='{self.name}')"


class UserDatabaseManager:
  def __init__(self):
    self._get_connection = _get_connection


  def get_user_by_id(self, user_id: int) -> User | None:
    """ idを指定して単一のユーザー情報を取得する """
    sql = "SELECT id, email, name FROM users WHERE id = %s;"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (user_id,))
          result = cur.fetchone()
          return User(**result) if result else None
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return None


  def get_user_by_email(self, email: str) -> User | None:
    """ emailを指定して単一のユーザー情報を取得する """
    sql = "SELECT id, email, name FROM users WHERE email = %s;"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (email,))
          result = cur.fetchone()
          return User(**result) if result else None
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return None


  def add_user(self, email: str, name: str) -> int | None:
    """ 新しいユーザーを1件追加し、そのユーザーのIDを返す """
    sql = "INSERT INTO users (email, name) VALUES (%s, %s);"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (email, name))
          conn.commit()
          return cur.lastrowid
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return None


  def update_user(self, user_id: int, email: str, name: str) -> bool:
    """ ユーザー情報を更新する """
    sql = "UPDATE users SET email = %s, name = %s WHERE id = %s;"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          rows_affected = cur.execute(sql, (email, name, user_id))
          conn.commit()
          return rows_affected > 0
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return False


  def delete_user(self, user_id: int) -> bool:
    """ ユーザーを削除する """
    sql = "DELETE FROM users WHERE id = %s;"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          rows_affected = cur.execute(sql, (user_id,))
          conn.commit()
          return rows_affected > 0
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return False