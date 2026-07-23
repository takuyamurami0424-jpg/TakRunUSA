import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from garminconnect import Garmin

OUTPUT_FILE = Path("data/latest_run.json")


def format_pace(seconds_per_km: float) -> str:
    """秒/kmを M:SS/km 形式に変換する。"""
    if seconds_per_km <= 0:
        return "--:--"

    minutes = int(seconds_per_km // 60)
    seconds = int(round(seconds_per_km % 60))

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d}"


def find_latest_run(activities: list[dict[str, Any]]) -> dict[str, Any]:
    """最新のランニングアクティビティを探す。"""
    for activity in activities:
        activity_type = activity.get("activityType", {})
        type_key = str(activity_type.get("typeKey", "")).lower()

        if type_key in {
            "running",
            "run",
            "trail_running",
            "treadmill_running",
            "track_running",
        }:
            return activity

        if "running" in type_key:
            return activity

    raise RuntimeError("直近のアクティビティにラン記録が見つかりません。")


def classify_run(
    distance_km: float,
    duration_minutes: float,
    average_hr: float | None,
) -> tuple[str, int, str]:
    """初期版のラン分類と評価。"""

    if distance_km >= 24 or duration_minutes >= 120:
        return (
            "Long Run",
            88,
            "持久力強化につながるロングランです。翌日は回復を優先してください。",
        )

    if duration_minutes <= 45 and average_hr is not None and average_hr < 140:
        return (
            "Recovery Run",
            90,
            "心拍を抑えた回復目的のランとして、適切にコントロールされています。",
        )

    if average_hr is not None and average_hr >= 165:
        return (
            "Tempo / High Intensity",
            86,
            "高強度トレーニングと推定されます。翌日の疲労状態を確認してください。",
        )

    return (
        "Easy / Steady Run",
        85,
        "安定した有酸素トレーニングと推定されます。",
    )


def main() -> None:
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")

    if not email or not password:
        raise RuntimeError(
            "GARMIN_EMAILまたはGARMIN_PASSWORDが設定されていません。"
        )

    client = Garmin(email, password)
    client.login()

    activities = client.get_activities(0, 20)
    latest = find_latest_run(activities)

    activity_id = latest.get("activityId")
    activity_name = latest.get("activityName", "Running")
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
    average_hr = (
        float(average_hr_value)
        if average_hr_value is not None
        else None
    )

    maximum_hr_value = latest.get("maxHR")
    maximum_hr = (
        float(maximum_hr_value)
        if maximum_hr_value is not None
        else None
    )

    elevation_m = float(latest.get("elevationGain") or 0)

    pace_seconds_per_km = (
        duration_seconds / distance_km
        if distance_km > 0
        else 0
    )

    run_type, score, comment = classify_run(
        distance_km,
        duration_minutes,
        average_hr,
    )

    result = {
        "activity_id": activity_id,
        "activity_name": activity_name,
        "date": start_time,
        "distance_km": round(distance_km, 2),
        "duration_minutes": round(duration_minutes, 1),
        "pace_per_km": format_pace(pace_seconds_per_km),
        "average_hr": (
            round(average_hr)
            if average_hr is not None
            else None
        ),
        "maximum_hr": (
            round(maximum_hr)
            if maximum_hr is not None
            else None
        ),
        "elevation_m": round(elevation_m),
        "estimated_run_type": run_type,
        "score": score,
        "grade": "A" if score >= 85 else "B",
        "comment": comment,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_FILE.exists():
        try:
            previous = json.loads(
                OUTPUT_FILE.read_text(encoding="utf-8")
            )

            if previous.get("activity_id") == activity_id:
                print("最新ランはすでに処理済みです。")
                return
        except json.JSONDecodeError:
            pass

    OUTPUT_FILE.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"更新完了: {distance_km:.2f} km / "
        f"{format_pace(pace_seconds_per_km)}/km / "
        f"{run_type}"
    )


if __name__ == "__main__":
    main()
