import pymysql
from .base import _get_connection


class User:
  """ユーザー情報を格納するためのデータクラス"""

  def __init__(self, id: int, email: str, name: str):
    self.id = id
    self.email = email
    self.name = name

  def __repr__(self):
    return f"User(id={self.id}, email='{self.email}', name='{self.name}')"


class UserDatabaseManager:
  """ユーザーに関連するデータベース操作を管理するクラス"""

  def __init__(self):
    self._get_connection = _get_connection

  # --- 書き込み操作 (Create, Update, Delete) ---

  def add(self, email: str, name: str) -> int | None:
    """新しいユーザーを1件追加し、そのユーザーのIDを返す"""
    sql = "INSERT INTO users (email, name) VALUES (%s, %s);"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (email, name))
          conn.commit()
          return cur.lastrowid
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました (add): {e}")
      return None


  def update(self, user_id: int, email: str, name: str) -> bool:
    """ユーザー情報を更新する"""
    sql = "UPDATE users SET email = %s, name = %s WHERE id = %s;"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          rows_affected = cur.execute(sql, (email, name, user_id))
          conn.commit()
          # 1行以上更新されていれば成功
          return rows_affected > 0
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました (update): {e}")
      return False


  def delete(self, user_id: int) -> bool:
    """ユーザーを削除する"""
    sql = "DELETE FROM users WHERE id = %s;"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          rows_affected = cur.execute(sql, (user_id,))
          conn.commit()
          # 1行以上削除されていれば成功
          return rows_affected > 0
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました (delete): {e}")
      return False

  # --- 読み取り操作 (Read) ---

  def get_user(self, user_id: int | None = None, email: str | None = None) -> User | None:
    """idまたはemailを指定して、単一のユーザー情報を取得する"""
    if user_id:
      sql = "SELECT id, email, name FROM users WHERE id = %s;"
      args = (user_id,)
    elif email:
      sql = "SELECT id, email, name FROM users WHERE email = %s;"
      args = (email,)
    else:
      return None

    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, args)
          result = cur.fetchone()
          return User(**result) if result else None
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました (get_user): {e}")
      return None