import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from garminconnect import Garmin

OUTPUT_FILE = Path("data/latest_run.json")
RUN_LOGS_FILE = Path("data/run_logs.json")
RUN_LOG_LIMIT = 50
ACTIVITY_FETCH_LIMIT = 100


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


def is_running_activity(activity: dict[str, Any]) -> bool:
    """Garminアクティビティがランニングか判定する。"""
    activity_type = activity.get("activityType", {})
    type_key = str(activity_type.get("typeKey", "")).lower()

    return (
        type_key
        in {
            "running",
            "run",
            "trail_running",
            "treadmill_running",
            "track_running",
        }
        or "running" in type_key
    )


def find_latest_run(
    activities: list[dict[str, Any]],
) -> dict[str, Any]:
    """最新のランニングアクティビティを探す。"""
    for activity in activities:
        if is_running_activity(activity):
            return activity

    raise RuntimeError(
        "直近のアクティビティにラン記録が見つかりません。"
    )


def translate_activity_name(
    activity_name: str,
) -> str:
    """
    Garminの日本語アクティビティ名を簡易的に英語へ変換する。

    例:
    Adairsville ラン
    → Adairsville Run
    """
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

    # 長い語句から先に置換する
    for japanese in sorted(
        translations,
        key=len,
        reverse=True,
    ):
        translated = translated.replace(
            japanese,
            translations[japanese],
        )

    return translated.strip()


def classify_run(
    distance_km: float,
    duration_minutes: float,
    average_hr: float | None,
) -> tuple[str, int, str, str]:
    """
    初期版のラン分類と評価。

    戻り値:
    英語ランタイプ
    スコア
    日本語コメント
    英語コメント
    """
    if distance_km >= 24 or duration_minutes >= 120:
        return (
            "Long Run",
            88,
            (
                "持久力強化につながるロングランです。"
                "翌日は回復を優先してください。"
            ),
            (
                "This was a productive long run for building "
                "endurance. Prioritize recovery tomorrow."
            ),
        )

    if (
        duration_minutes <= 45
        and average_hr is not None
        and average_hr < 140
    ):
        return (
            "Recovery Run",
            90,
            (
                "心拍を抑えた回復目的のランとして、"
                "適切にコントロールされています。"
            ),
            (
                "This was a well-controlled recovery run "
                "with an appropriately low heart rate."
            ),
        )

    if (
        average_hr is not None
        and average_hr >= 165
    ):
        return (
            "Tempo / High Intensity",
            86,
            (
                "高強度トレーニングと推定されます。"
                "翌日の疲労状態を確認してください。"
            ),
            (
                "This appears to be a high-intensity workout. "
                "Check your fatigue and recovery tomorrow."
            ),
        )

    return (
        "Easy / Steady Run",
        85,
        "安定した有酸素トレーニングと推定されます。",
        (
            "This appears to be a steady and controlled "
            "aerobic training run."
        ),
    )


def build_run_record(activity: dict[str, Any]) -> dict[str, Any]:
    """Garminアクティビティを公開用のラン記録へ変換する。"""
    activity_name = str(activity.get("activityName") or "Running")
    start_time = (
        activity.get("startTimeLocal")
        or activity.get("startTimeGMT")
    )
    distance_m = float(activity.get("distance") or 0)
    duration_seconds = float(
        activity.get("movingDuration")
        or activity.get("duration")
        or activity.get("elapsedDuration")
        or 0
    )
    distance_km = distance_m / 1000
    duration_minutes = duration_seconds / 60

    average_hr_value = activity.get("averageHR")
    average_hr = (
        float(average_hr_value)
        if average_hr_value is not None
        else None
    )
    maximum_hr_value = activity.get("maxHR")
    maximum_hr = (
        float(maximum_hr_value)
        if maximum_hr_value is not None
        else None
    )
    elevation_m = float(activity.get("elevationGain") or 0)
    pace_seconds_per_km = (
        duration_seconds / distance_km
        if distance_km > 0
        else 0
    )
    run_type, score, comment_ja, comment_en = classify_run(
        distance_km,
        duration_minutes,
        average_hr,
    )

    return {
        "activity_id": activity.get("activityId"),
        "activity_name": activity_name,
        "activity_name_en": translate_activity_name(activity_name),
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
        "comment": comment_ja,
        "comment_en": comment_en,
    }


def read_json(path: Path) -> Any:
    """JSONファイルを安全に読み込む。"""
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def main() -> None:
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")

    if not email or not password:
        raise RuntimeError(
            "GARMIN_EMAILまたはGARMIN_PASSWORDが"
            "設定されていません。"
        )

    client = Garmin(email, password)
    client.login()

    activities = client.get_activities(0, ACTIVITY_FETCH_LIMIT)
    running_activities = [
        activity
        for activity in activities
        if is_running_activity(activity)
    ][:RUN_LOG_LIMIT]

    if not running_activities:
        raise RuntimeError(
            "直近のアクティビティにラン記録が見つかりません。"
        )

    run_logs = [
        build_run_record(activity)
        for activity in running_activities
    ]
    latest_result = run_logs[0]

    previous_latest = read_json(OUTPUT_FILE)
    previous_logs = read_json(RUN_LOGS_FILE)
    comparable_latest = (
        {
            key: value
            for key, value in previous_latest.items()
            if key != "updated_at"
        }
        if isinstance(previous_latest, dict)
        else None
    )
    previous_run_list = (
        previous_logs.get("runs")
        if isinstance(previous_logs, dict)
        else None
    )

    if (
        comparable_latest == latest_result
        and previous_run_list == run_logs
    ):
        print("Garminのラン記録に変更はありません。")
        return

    generated_at = datetime.now(timezone.utc).isoformat()
    latest_output = {
        **latest_result,
        "updated_at": generated_at,
    }
    logs_output = {
        "generated_at": generated_at,
        "count": len(run_logs),
        "runs": run_logs,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(
            latest_output,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    RUN_LOGS_FILE.write_text(
        json.dumps(
            logs_output,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"更新完了: {len(run_logs)}件 / "
        f"最新 {latest_result['distance_km']:.2f} km / "
        f"{latest_result['pace_per_km']}/km"
    )


if __name__ == "__main__":
    main()

