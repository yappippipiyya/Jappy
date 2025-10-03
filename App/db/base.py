import pymysql
from const import DB_NAME, HOST, PASSWORD, USER


def _get_connection():
  return pymysql.connect(
    host=HOST,
    user=USER,
    password=PASSWORD,
    database=DB_NAME,
    cursorclass=pymysql.cursors.DictCursor
  )