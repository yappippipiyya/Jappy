import psycopg
from psycopg.rows import dict_row
from const import DATABASE_URL


def _get_connection():
  """
  データベース接続を取得する。
  結果が辞書形式で返されるように設定する。
  """
  conn = psycopg.connect(DATABASE_URL)
  conn.row_factory = dict_row # type: ignore
  return conn