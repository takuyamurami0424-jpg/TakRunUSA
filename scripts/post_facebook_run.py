import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

LATEST_RUN_FILE = Path("data/latest_run.json")
STATE_FILE = Path("data/facebook_state.json")
CARD_FILE = Path("assets/latest_run_card.png")

DEFAULT_PAGE_ID = "1196272093578743"
DEFAULT_API_VERSION = "v26.0"
RUN_LOG_URL = "https://takuyamurami0424-jpg.github.io/TakRunUSA/run-logs.html"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def format_message(run: dict) -> str:
    name = run.get("activity_name_en") or run.get("activity_name") or "Running"
    date = str(run.get("date") or "").strip()
    distance = run.get("distance_km")
    duration = run.get("duration_minutes")
    pace = run.get("pace_per_km")
    avg_hr = run.get("average_hr")
    score = run.get("score")
    grade = run.get("grade")
    run_type = run.get("estimated_run_type")

    lines = ["🏃 New Garmin Run | Garminラン更新", "", name]

    if date:
        lines.append(f"📅 {date}")
    if distance is not None:
        lines.append(f"📏 {distance} km")
    if duration is not None:
        lines.append(f"⏱ {duration} min")
    if pace:
        lines.append(f"⚡ {pace}/km")
    if avg_hr is not None:
        lines.append(f"❤️ Avg HR {avg_hr} bpm")
    if score is not None:
        score_text = f"⭐ Run Score {score}/100"
        if grade:
            score_text += f" ({grade})"
        lines.append(score_text)
    if run_type:
        lines.append(f"🎯 {run_type}")

    lines.extend(["", "Full running log / ランニングログ:", RUN_LOG_URL])
    return "\n".join(lines)


def post_photo(page_id: str, token: str, api_version: str, run: dict) -> str:
    if not CARD_FILE.exists():
        raise RuntimeError(f"Run card image was not found: {CARD_FILE}")

    url = f"https://graph.facebook.com/{api_version}/{page_id}/photos"

    with CARD_FILE.open("rb") as image_file:
        response = requests.post(
            url,
            data={
                "caption": format_message(run),
                "published": "true",
                "access_token": token,
            },
            files={"source": (CARD_FILE.name, image_file, "image/png")},
            timeout=60,
        )

    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Facebook Graph API returned non-JSON HTTP {response.status_code}: {response.text}"
        ) from exc

    if not response.ok:
        raise RuntimeError(
            f"Facebook Graph API returned HTTP {response.status_code}: {result}"
        )

    post_id = result.get("post_id") or result.get("id")
    if not post_id:
        raise RuntimeError(f"Facebook Graph API response did not include a post id: {result}")

    return str(post_id)


def main() -> None:
    token = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
    page_id = os.environ.get("FACEBOOK_PAGE_ID", DEFAULT_PAGE_ID).strip()
    api_version = os.environ.get("FACEBOOK_GRAPH_API_VERSION", DEFAULT_API_VERSION).strip()

    if not token:
        print(
            "FACEBOOK_PAGE_ACCESS_TOKEN is not configured. "
            "Skipping Facebook post without failing Garmin updates."
        )
        return

    run = load_json(LATEST_RUN_FILE)
    if not run:
        raise RuntimeError("data/latest_run.json was not found or is empty.")

    activity_id = str(run.get("activity_id") or "").strip()
    if not activity_id:
        raise RuntimeError("Latest Garmin run does not contain activity_id.")

    state = load_json(STATE_FILE)
    if str(state.get("last_posted_activity_id") or "") == activity_id:
        print(f"Garmin activity {activity_id} has already been posted to Facebook.")
        return

    post_id = post_photo(page_id, token, api_version, run)

    state = {
        "last_posted_activity_id": run.get("activity_id"),
        "last_facebook_post_id": post_id,
        "last_posted_at": datetime.now(timezone.utc).isoformat(),
        "page_id": page_id,
        "post_format": "image_card",
    }

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Posted Garmin activity {activity_id} with run card to Facebook Page. "
        f"Facebook post id: {post_id}"
    )


if __name__ == "__main__":
    main()
