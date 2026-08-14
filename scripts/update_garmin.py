import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from garminconnect import Garmin

LATEST_RUN_FILE = Path("data/latest_run.json")
JOURNEY_FILE = Path("data/journey_data.json")
JOURNEY_START_DATE = datetime(2024, 7, 1)
PAGE_SIZE = 100
MAX_ACTIVITIES = 5000

RUN_ACTIVITY_TYPES = {
    "running",
    "run",
    "street_running",
    "trail_running",
    "treadmill_running",
    "track_running",
    "indoor_running",
    "virtual_running",
}


def format_pace(seconds_per_km: float) -> str:
    """秒/kmをM:SS形式に変換する。"""
    if seconds_per_km <= 0:
        return "--:--"

    minutes = int(seconds_per_km // 60)
    seconds = int(round(seconds_per_km % 60))

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d}"


def parse_activity_datetime(activity: dict[str, Any]) -> datetime | None:
    """Garminのアクティビティ日時をdatetimeへ変換する。"""
    date_value = activity.get("startTimeLocal") or activity.get("startTimeGMT")

    if not date_value:
        return None

    normalized = str(date_value).replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        try:
            parsed = datetime.strptime(str(date_value), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    if parsed.tzinfo is not None:
        parsed = parsed.replace(tzinfo=None)

    return parsed


def is_running_activity(activity: dict[str, Any]) -> bool:
    """アクティビティがランニング系か判定する。"""
    activity_type = activity.get("activityType") or {}
    type_key = str(activity_type.get("typeKey") or "").lower()

    if type_key in RUN_ACTIVITY_TYPES:
        return True

    return "running" in type_key or type_key.endswith("_run")


def find_latest_run(activities: list[dict[str, Any]]) -> dict[str, Any]:
    """最新のランニングアクティビティを探す。"""
    for activity in activities:
        if is_running_activity(activity):
            return activity

    raise RuntimeError("直近のアクティビティにラン記録が見つかりません。")


def translate_activity_name(activity_name: str) -> str:
    """Garminの日本語アクティビティ名を英語へ簡易変換する。"""
    translations = {
        "トレッドミルランニング": "Treadmill Running",
        "トレッドミルラン": "Treadmill Run",
        "トラックランニング": "Track Running",
        "トラックラン": "Track Run",
        "トレイルランニング": "Trail Running",
        "トレイルラン": "Trail Run",
        "リカバリーラン": "Recovery Run",
        "イージーラン": "Easy Run",
        "ロングラン": "Long Run",
        "テンポラン": "Tempo Run",
        "インターバル走": "Interval Run",
        "インターバル": "Intervals",
        "ランニング": "Running",
        "ラン": "Run",
    }

    translated = activity_name

    for japanese in sorted(translations, key=len, reverse=True):
        translated = translated.replace(japanese, translations[japanese])

    return translated.strip()


def classify_run(
    distance_km: float,
    duration_minutes: float,
    average_hr: float | None,
) -> tuple[str, int, str, str]:
    """最新ランを簡易分類し、日英コメントを返す。"""
    if distance_km >= 24 or duration_minutes >= 120:
        return (
            "Long Run",
            88,
            "持久力強化につながるロングランです。翌日は回復を優先してください。",
            "This was a productive long run for building endurance. Prioritize recovery tomorrow.",
        )

    if duration_minutes <= 45 and average_hr is not None and average_hr < 140:
        return (
            "Recovery Run",
            90,
            "心拍を抑えた回復目的のランとして、適切にコントロールされています。",
            "This was a well-controlled recovery run with an appropriately low heart rate.",
        )

    if average_hr is not None and average_hr >= 165:
        return (
            "Tempo / High Intensity",
            86,
            "高強度トレーニングと推定されます。翌日の疲労状態を確認してください。",
            "This appears to be a high-intensity workout. Check your fatigue and recovery tomorrow.",
        )

    return (
        "Easy / Steady Run",
        85,
        "安定した有酸素トレーニングと推定されます。",
        "This appears to be a steady and controlled aerobic training run.",
    )


def load_all_activities_since(
    client: Garmin,
    start_date: datetime,
) -> list[dict[str, Any]]:
    """Garminから指定日以降を含むアクティビティをページ単位で取得する。"""
    all_activities: list[dict[str, Any]] = []
    offset = 0

    while offset < MAX_ACTIVITIES:
        batch = client.get_activities(offset, PAGE_SIZE)

        if not batch:
            break

        all_activities.extend(batch)

        dates = [
            parsed
            for activity in batch
            if (parsed := parse_activity_datetime(activity)) is not None
        ]

        if dates and min(dates) < start_date:
            break

        if len(batch) < PAGE_SIZE:
            break

        offset += PAGE_SIZE

    return all_activities


def build_latest_run_data(latest: dict[str, Any]) -> dict[str, Any]:
    """最新ラン用JSONデータを作成する。"""
    activity_id = latest.get("activityId")
    activity_name = str(latest.get("activityName") or "Running")
    activity_name_en = translate_activity_name(activity_name)
    start_time = latest.get("startTimeLocal") or latest.get("startTimeGMT")

    distance_m = float(latest.get("distance") or 0)
    duration_seconds = float(
        latest.get("movingDuration")
        or latest.get("duration")
        or latest.get("elapsedDuration")
        or 0
    )

    distance_km = distance_m / 1000
    duration_minutes = duration_seconds / 60

    average_hr_value = latest.get("averageHR")
    average_hr = float(average_hr_value) if average_hr_value is not None else None

    maximum_hr_value = latest.get("maxHR")
    maximum_hr = float(maximum_hr_value) if maximum_hr_value is not None else None

    elevation_m = float(latest.get("elevationGain") or 0)
    pace_seconds_per_km = duration_seconds / distance_km if distance_km > 0 else 0

    run_type, score, comment_ja, comment_en = classify_run(
        distance_km,
        duration_minutes,
        average_hr,
    )

    return {
        "activity_id": activity_id,
        "activity_name": activity_name,
        "activity_name_en": activity_name_en,
        "date": start_time,
        "distance_km": round(distance_km, 2),
        "duration_minutes": round(duration_minutes, 1),
        "pace_per_km": format_pace(pace_seconds_per_km),
        "average_hr": round(average_hr) if average_hr is not None else None,
        "maximum_hr": round(maximum_hr) if maximum_hr is not None else None,
        "elevation_m": round(elevation_m),
        "estimated_run_type": run_type,
        "score": score,
        "grade": "A" if score >= 85 else "B",
        "comment": comment_ja,
        "comment_en": comment_en,
    }


def build_journey_data(activities: list[dict[str, Any]]) -> dict[str, Any]:
    """2024年7月以降のランニング累計データを作成する。"""
    activity_ids: set[str] = set()
    total_distance_m = 0.0
    total_duration_seconds = 0.0

    for activity in activities:
        activity_date = parse_activity_datetime(activity)

        if activity_date is None or activity_date < JOURNEY_START_DATE:
            continue

        if not is_running_activity(activity):
            continue

        activity_id = str(activity.get("activityId") or "")
        if activity_id and activity_id in activity_ids:
            continue

        distance_m = float(activity.get("distance") or 0)
        if distance_m <= 0:
            continue

        duration_seconds = float(
            activity.get("movingDuration")
            or activity.get("duration")
            or activity.get("elapsedDuration")
            or 0
        )

        if activity_id:
            activity_ids.add(activity_id)

        total_distance_m += distance_m
        total_duration_seconds += duration_seconds

    return {
        "total_distance_km": round(total_distance_m / 1000, 1),
        "total_duration_hours": round(total_duration_seconds / 3600, 1),
        "activity_count": len(activity_ids),
        "start_date": "July 2024",
        "start_date_iso": "2024-07-01",
        "base_location": "Adairsville, Georgia",
    }


def write_json_if_changed(
    path: Path,
    data: dict[str, Any],
    timestamp_key: str,
) -> bool:
    """実データが変わったときだけJSONを書き換える。"""
    path.parent.mkdir(parents=True, exist_ok=True)

    previous: dict[str, Any] | None = None
    if path.exists():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = None

    previous_compare = dict(previous or {})
    previous_compare.pop(timestamp_key, None)

    if previous is not None and previous_compare == data:
        return False

    output = dict(data)
    output[timestamp_key] = datetime.now(timezone.utc).isoformat()

    path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return True


def main() -> None:
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")

    if not email or not password:
        raise RuntimeError("GARMIN_EMAILまたはGARMIN_PASSWORDが設定されていません。")

    client = Garmin(email, password)
    client.login()

    print("Garminから2024年7月以降のアクティビティを取得しています...")
    activities = load_all_activities_since(client, JOURNEY_START_DATE)

    if not activities:
        raise RuntimeError("Garminからアクティビティを取得できませんでした。")

    latest = find_latest_run(activities)
    latest_run_data = build_latest_run_data(latest)
    journey_data = build_journey_data(activities)

    latest_changed = write_json_if_changed(
        LATEST_RUN_FILE,
        latest_run_data,
        "updated_at",
    )
    journey_changed = write_json_if_changed(
        JOURNEY_FILE,
        journey_data,
        "last_updated",
    )

    print(
        f"最新ラン: {latest_run_data['distance_km']:.2f} km / "
        f"{latest_run_data['pace_per_km']}/km"
    )
    print(
        f"累計ラン: {journey_data['total_distance_km']:,.1f} km / "
        f"{journey_data['activity_count']} activities"
    )

    if latest_changed:
        print("data/latest_run.jsonを更新しました。")
    else:
        print("data/latest_run.jsonに変更はありません。")

    if journey_changed:
        print("data/journey_data.jsonを更新しました。")
    else:
        print("data/journey_data.jsonに変更はありません。")


if __name__ == "__main__":
    main()
