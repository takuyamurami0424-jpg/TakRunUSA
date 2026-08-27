import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from garminconnect import Garmin

from update_garmin import (
    JOURNEY_START_DATE,
    is_running_activity,
    load_all_activities_since,
    parse_activity_datetime,
)

OUTPUT_FILE = Path("data/dashboard.json")
LOCAL_TZ = ZoneInfo("America/New_York")

PB_WINDOWS = {
    "5K": (4.8, 5.3),
    "10K": (9.7, 10.5),
    "Half Marathon": (20.5, 21.8),
    "Marathon": (41.0, 43.5),
}


def activity_duration_seconds(activity: dict) -> float:
    return float(
        activity.get("movingDuration")
        or activity.get("duration")
        or activity.get("elapsedDuration")
        or 0
    )


def format_duration(seconds: float) -> str:
    total_seconds = int(round(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_pace(seconds_per_km: float | None) -> str | None:
    if seconds_per_km is None or seconds_per_km <= 0:
        return None

    minutes = int(seconds_per_km // 60)
    seconds = int(round(seconds_per_km % 60))

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d}"


def month_key(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"


def previous_months(now: datetime, count: int = 12) -> list[tuple[int, int]]:
    months: list[tuple[int, int]] = []
    year = now.year
    month = now.month

    for _ in range(count):
        months.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1

    months.reverse()
    return months


def summarize_runs(runs: list[dict]) -> dict:
    total_distance = sum(run["distance_km"] for run in runs)
    total_duration = sum(run["duration_seconds"] for run in runs)

    hr_runs = [run for run in runs if run["average_hr"] is not None]
    hr_duration = sum(run["duration_seconds"] for run in hr_runs)
    weighted_hr = (
        sum(run["average_hr"] * run["duration_seconds"] for run in hr_runs) / hr_duration
        if hr_duration > 0
        else None
    )

    avg_pace_seconds = (
        total_duration / total_distance
        if total_distance > 0
        else None
    )

    return {
        "distance_km": round(total_distance, 1),
        "run_count": len(runs),
        "duration_hours": round(total_duration / 3600, 1),
        "avg_pace_per_km": format_pace(avg_pace_seconds),
        "avg_hr": round(weighted_hr) if weighted_hr is not None else None,
        "longest_run_km": round(max((run["distance_km"] for run in runs), default=0), 1),
    }


def build_training_trend(unique_runs: list[dict], now: datetime) -> dict:
    current_start = now - timedelta(days=28)
    previous_start = now - timedelta(days=56)

    current_runs = [
        run for run in unique_runs
        if current_start <= run["date"] <= now
    ]
    previous_runs = [
        run for run in unique_runs
        if previous_start <= run["date"] < current_start
    ]

    current = summarize_runs(current_runs)
    previous = summarize_runs(previous_runs)

    if previous["distance_km"] > 0:
        distance_change_pct = round(
            (current["distance_km"] - previous["distance_km"])
            / previous["distance_km"]
            * 100,
            1,
        )
    else:
        distance_change_pct = None

    if distance_change_pct is None:
        direction = "no-baseline"
    elif distance_change_pct > 2:
        direction = "up"
    elif distance_change_pct < -2:
        direction = "down"
    else:
        direction = "steady"

    weekly = []

    for index in range(4):
        start = now - timedelta(days=7 * (4 - index))
        end = now - timedelta(days=7 * (3 - index))

        week_runs = [
            run for run in unique_runs
            if start <= run["date"] < end
        ]

        week_summary = summarize_runs(week_runs)

        weekly.append(
            {
                "label": f"W{index + 1}",
                "date_range": (
                    f"{start.strftime('%b %d')}–"
                    f"{(end - timedelta(days=1)).strftime('%b %d')}"
                ),
                "distance_km": week_summary["distance_km"],
                "run_count": week_summary["run_count"],
                "avg_pace_per_km": week_summary["avg_pace_per_km"],
            }
        )

    return {
        "period_days": 28,
        "current": current,
        "previous": previous,
        "distance_change_pct": distance_change_pct,
        "direction": direction,
        "weekly": weekly,
    }


def build_dashboard(activities: list[dict]) -> dict:
    now = datetime.now(LOCAL_TZ).replace(tzinfo=None)
    month_start = datetime(now.year, now.month, 1)
    year_start = datetime(now.year, 1, 1)
    last_7_days_start = now - timedelta(days=7)

    unique_runs: list[dict] = []
    seen_ids: set[str] = set()

    for activity in activities:
        if not is_running_activity(activity):
            continue

        dt = parse_activity_datetime(activity)
        if dt is None or dt < JOURNEY_START_DATE:
            continue

        distance_km = float(activity.get("distance") or 0) / 1000
        duration_seconds = activity_duration_seconds(activity)
        if distance_km <= 0 or duration_seconds <= 0:
            continue

        activity_id = str(activity.get("activityId") or "")
        if activity_id and activity_id in seen_ids:
            continue
        if activity_id:
            seen_ids.add(activity_id)

        average_hr_value = activity.get("averageHR")
        average_hr = (
            float(average_hr_value)
            if average_hr_value is not None
            else None
        )

        unique_runs.append(
            {
                "activity_id": activity.get("activityId"),
                "name": activity.get("activityName") or "Running",
                "date": dt,
                "distance_km": distance_km,
                "duration_seconds": duration_seconds,
                "average_hr": average_hr,
            }
        )

    total_distance = sum(run["distance_km"] for run in unique_runs)
    month_distance = sum(
        run["distance_km"] for run in unique_runs if run["date"] >= month_start
    )
    year_distance = sum(
        run["distance_km"] for run in unique_runs if run["date"] >= year_start
    )
    last_7_days_distance = sum(
        run["distance_km"] for run in unique_runs if run["date"] >= last_7_days_start
    )

    month_totals: dict[str, float] = defaultdict(float)
    for run in unique_runs:
        month_totals[month_key(run["date"])] += run["distance_km"]

    monthly = []
    for year, month in previous_months(now, 12):
        key = f"{year:04d}-{month:02d}"
        monthly.append(
            {
                "key": key,
                "label": datetime(year, month, 1).strftime("%b"),
                "year": year,
                "distance_km": round(month_totals.get(key, 0.0), 1),
                "is_current": year == now.year and month == now.month,
            }
        )

    pbs: dict[str, dict | None] = {}
    for label, (min_km, max_km) in PB_WINDOWS.items():
        candidates = [
            run
            for run in unique_runs
            if min_km <= run["distance_km"] <= max_km
        ]

        if not candidates:
            pbs[label] = None
            continue

        best = min(candidates, key=lambda run: run["duration_seconds"])
        age_days = (now.date() - best["date"].date()).days

        pbs[label] = {
            "time": format_duration(best["duration_seconds"]),
            "date": best["date"].date().isoformat(),
            "distance_km": round(best["distance_km"], 2),
            "activity_id": best["activity_id"],
            "activity_name": best["name"],
            "new_pb": 0 <= age_days <= 7,
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Garmin running activities since July 2024",
        "summary": {
            "this_month_km": round(month_distance, 1),
            "this_year_km": round(year_distance, 1),
            "last_7_days_km": round(last_7_days_distance, 1),
            "total_km": round(total_distance, 1),
            "activity_count": len(unique_runs),
        },
        "training_trend": build_training_trend(unique_runs, now),
        "monthly_mileage": monthly,
        "pbs": pbs,
    }


def write_if_changed(data: dict) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    compare_data = dict(data)
    compare_data.pop("generated_at", None)

    if OUTPUT_FILE.exists():
        try:
            previous = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
            previous.pop("generated_at", None)
            if previous == compare_data:
                print("data/dashboard.jsonに変更はありません。")
                return
        except json.JSONDecodeError:
            pass

    OUTPUT_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("data/dashboard.jsonを更新しました。")


def main() -> None:
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")

    if not email or not password:
        raise RuntimeError("GARMIN_EMAILまたはGARMIN_PASSWORDが設定されていません。")

    client = Garmin(email, password)
    client.login()

    activities = load_all_activities_since(client, JOURNEY_START_DATE)
    if not activities:
        raise RuntimeError("Garminからアクティビティを取得できませんでした。")

    dashboard = build_dashboard(activities)
    write_if_changed(dashboard)

    summary = dashboard["summary"]
    trend = dashboard["training_trend"]["current"]

    print(
        "Dashboard: "
        f"month={summary['this_month_km']:.1f} km, "
        f"year={summary['this_year_km']:.1f} km, "
        f"total={summary['total_km']:.1f} km, "
        f"last28={trend['distance_km']:.1f} km"
    )


if __name__ == "__main__":
    main()
