import json
import os
from datetime import datetime, timezone
from pathlib import Path

from garminconnect import Garmin
from update_garmin import build_latest_run_data, is_running_activity

RUN_LOGS_FILE = Path("data/run_logs.json")
ACTIVITY_FETCH_LIMIT = 100
RUN_LOG_LIMIT = 50


def read_existing_runs() -> list[dict] | None:
    if not RUN_LOGS_FILE.exists():
        return None

    try:
        data = json.loads(RUN_LOGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    runs = data.get("runs") if isinstance(data, dict) else None
    return runs if isinstance(runs, list) else None


def main() -> None:
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")

    if not email or not password:
        raise RuntimeError("GARMIN_EMAILまたはGARMIN_PASSWORDが設定されていません。")

    client = Garmin(email, password)
    client.login()

    activities = client.get_activities(0, ACTIVITY_FETCH_LIMIT)
    running_activities = [
        activity for activity in activities if is_running_activity(activity)
    ][:RUN_LOG_LIMIT]

    if not running_activities:
        raise RuntimeError("直近のアクティビティにラン記録が見つかりません。")

    runs = [build_latest_run_data(activity) for activity in running_activities]

    if read_existing_runs() == runs:
        print("data/run_logs.jsonに変更はありません。")
        return

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(runs),
        "runs": runs,
    }

    RUN_LOGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RUN_LOGS_FILE.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"data/run_logs.jsonを更新しました: {len(runs)} runs")


if __name__ == "__main__":
    main()
