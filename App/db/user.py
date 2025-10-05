import pymysql
from .base import _get_connection


class User:
  """ユーザー情報を格納するためのデータクラス"""

  def __init__(self, id: int, line_user_id: str, name: str):
    self.id = id
    self.line_user_id = line_user_id
    self.name = name

  def __repr__(self):
    return f"User(id={self.id}, line_user_id='{self.line_user_id}', name='{self.name}')"


class UserDatabaseManager:
  """ユーザーに関連するデータベース操作を管理するクラス"""

  def __init__(self):
    self._get_connection = _get_connection

  # --- 書き込み操作 (Create, Update, Delete) ---

  def add(self, line_user_id: str, name: str) -> int | None:
    """新しいユーザーを1件追加し、そのユーザーのIDを返す"""
    sql = "INSERT INTO users (line_user_id, name) VALUES (%s, %s);"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (line_user_id, name))
          conn.commit()
          return cur.lastrowid
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました (add): {e}")
      return None


  def update(self, user_id: int, line_user_id: str, name: str) -> bool:
    """ユーザー情報を更新する"""
    sql = "UPDATE users SET line_user_id = %s, name = %s WHERE id = %s;"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          rows_affected = cur.execute(sql, (line_user_id, name, user_id))
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

  def get_user(self, user_id: int | None = None, line_user_id: str | None = None) -> User | None:
    """idまたはline_user_idを指定して、単一のユーザー情報を取得する"""
    if user_id:
      sql = "SELECT id, line_user_id, name FROM users WHERE id = %s;"
      args = (user_id,)
    elif line_user_id:
      sql = "SELECT id, line_user_id, name FROM users WHERE line_user_id = %s;"
      args = (line_user_id,)
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