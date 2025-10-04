import json
from datetime import date
from typing import Literal

import pymysql

from .base import _get_connection


"""
schedule: dictについて
key: date
value: 24個の0 | 1で構成されたlist, 0が不可, 1が可能で1時間毎(0:00～1:00, 1:00～2:00)の各時間帯のschedule
"""

class Schedule:
  """ バンド情報を格納するためのデータクラス """
  def __init__(self, id: int, user_id: int, band_id: int, schedule: dict[date, list[Literal[0, 1]]]):
    self.id = id
    self.user_id = user_id
    self.band_id = band_id
    self.schedule = schedule

  def __repr__(self):
    return f"Schedule(id={self.id}, user_id='{self.user_id}', band_id='{self.band_id}', schedule={self.schedule})"


class ScheduleDatabaseManager:
  def __init__(self):
    self._get_connection = _get_connection

  def _serialize_schedule(self, schedule: dict[date, list[Literal[0, 1]]]) -> str:
    """
    schedule辞書をJSON文字列に変換する。
    """
    if not isinstance(schedule, dict):
      return json.dumps({})
    str_key_schedule = {d.isoformat(): v for d, v in schedule.items()}
    return json.dumps(str_key_schedule)

  def _deserialize_schedule(self, schedule_json: str | None) -> dict[date, list[Literal[0, 1]]]:
    """
    JSON文字列をschedule辞書に変換する。
    キーである文字列はdateオブジェクトに変換される。
    """
    if not schedule_json:
      return {}
    str_key_schedule = json.loads(schedule_json)
    return {date.fromisoformat(k): v for k, v in str_key_schedule.items()}

  def update_schedule(self, user_id: int, schedule: dict[date, list[Literal[0, 1]]], band_id: int = 0) -> Schedule | None:
    """
    スケジュールを更新または新規作成する。
    user_idとband_idの組み合わせでレコードを特定し、存在すれば更新、なければ挿入する（UPSERT）。
    成功した場合、更新または作成されたScheduleオブジェクトを返す。
    """
    json_schedule = self._serialize_schedule(schedule)
    sql = """
      INSERT INTO schedules (user_id, band_id, schedule)
      VALUES (%s, %s, %s)
      ON DUPLICATE KEY UPDATE schedule = VALUES(schedule);
    """
    get_sql = "SELECT * FROM schedules WHERE user_id = %s AND band_id = %s;"

    try:
      with self._get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute(sql, (user_id, band_id, json_schedule))
          conn.commit()

          # 更新/挿入したレコードを取得してオブジェクトとして返す
          cur.execute(get_sql, (user_id, band_id))
          result = cur.fetchone()
          if result:
            result['schedule'] = self._deserialize_schedule(result['schedule'])
            return Schedule(**result)
          return None
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")
      return None

  def get_schedules(self, user_id: int | None = None, band_id: int | None = None) -> list[Schedule]:
    """
    ユーザーIDまたはバンドIDを指定して、関連するスケジュール情報のリストを取得する。
    エラーが発生した場合や、条件に合うデータがない場合は空のリストを返す。
    """
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
            deserialized_schedule = self._deserialize_schedule(row['schedule'])
            schedules_list.append(Schedule(
                id=row['id'],
                user_id=row['user_id'],
                band_id=row['band_id'],
                schedule=deserialized_schedule
            ))
    except pymysql.Error as e:
      print(f"データベースエラーが発生しました: {e}")

    return schedules_list