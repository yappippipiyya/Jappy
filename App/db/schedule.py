import json
from datetime import date
from typing import Literal

import psycopg

from .base import _get_connection


class Schedule:
  """スケジュール情報を格納するためのデータクラス"""

  def __init__(self, id: int, user_id: int, band_id: int, schedule: dict[date, list[Literal[0, 1]]], comment: str):
    self.id = id
    self.user_id = user_id
    self.band_id = band_id
    self.schedule = schedule
    self.comment = comment

  def __repr__(self):
    return (
      f"Schedule(id={self.id}, user_id='{self.user_id}', "
      f"band_id='{self.band_id}', schedule={self.schedule}, comment={self.comment})"
    )


class ScheduleDatabaseManager:
  """schedulesテーブルを操作するためのクラス"""

  def __init__(self):
    self._get_connection = _get_connection

  def get_schedules(self, user_id: int | None = None, band_id: int | None = None) -> list[Schedule]:
    """ユーザーIDまたはバンドIDでスケジュール情報を取得する"""
    if user_id is not None:
      sql = "SELECT * FROM schedules WHERE user_id = %s;"
      args = (user_id,)
    elif band_id is not None:
      sql = "SELECT * FROM schedules WHERE band_id = %s;"
      args = (band_id,)
    else:
      return []

    schedules_list: list[Schedule] = []
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, args)
          results = cur.fetchall()
          for row in results:
            row['schedule'] = self._deserialize_schedule(row['schedule'])
            schedules_list.append(Schedule(**row))
    except psycopg.Error as e:
      print(f"データベースエラーが発生しました: {e}")

    return schedules_list


  def update_schedule(self, user_id: int, schedule: dict[date, list[Literal[0, 1]]], band_id: int = 0, comment: str | None = None) -> Schedule | None:
    """スケジュールを更新または新規作成する (UPSERT)"""
    json_schedule = self._serialize_schedule(schedule)
    sql = """
      INSERT INTO schedules (user_id, band_id, schedule, comment)
      VALUES (%s, %s, %s, %s)
      ON CONFLICT (user_id, band_id) DO UPDATE
      SET schedule = EXCLUDED.schedule,
          comment = EXCLUDED.comment;
    """
    get_sql = "SELECT * FROM schedules WHERE user_id = %s AND band_id = %s;"

    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (user_id, band_id, json_schedule, comment))
          conn.commit()

          # 更新/挿入したレコードを取得してオブジェクトとして返す
          cur.execute(get_sql, (user_id, band_id))
          result = cur.fetchone()
          if result:
            result['schedule'] = self._deserialize_schedule(result['schedule'])
            return Schedule(**result)
          return None
    except psycopg.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return None


  def delete_schedules(self, user_id: int) -> bool:
    """指定されたユーザーIDのスケジュールをすべて削除する"""
    sql = "DELETE FROM schedules WHERE user_id = %s;"
    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (user_id,))
          conn.commit()
          return True
    except psycopg.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return False


  def _serialize_schedule(self, schedule: dict[date, list[Literal[0, 1]]]) -> str:
    """schedule辞書をJSON文字列にシリアライズする"""
    if not isinstance(schedule, dict):
      return json.dumps({})

    str_key_schedule = {d.isoformat(): v for d, v in schedule.items()}
    return json.dumps(str_key_schedule)


  def _deserialize_schedule(self, schedule_data: str | dict | None) -> dict[date, list[Literal[0, 1]]]:
    """JSON文字列または辞書をschedule辞書にデシリアライズする"""
    if not schedule_data:
      return {}

    # psycopgはJSON/JSONB型を自動的にdictにデコードするため、型をチェック
    if isinstance(schedule_data, str):
      # pymysqlなど、文字列で返された場合
      str_key_schedule = json.loads(schedule_data)
    else:
      # psycopgなど、既に辞書の場合
      str_key_schedule = schedule_data

    return {date.fromisoformat(k): v for k, v in str_key_schedule.items()}