import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests

from generate_run_card import generate_run_card

RUN_LOGS_FILE = Path("data/run_logs.json")
STATE_FILE = Path("data/facebook_state.json")

DEFAULT_PAGE_ID = "1196272093578743"
DEFAULT_API_VERSION = "v26.0"
RUN_LOG_URL = "https://takuyamurami0424-jpg.github.io/TakRunUSA/run-logs.html"
MAX_POSTED_IDS = 100


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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


def post_photo(
    page_id: str,
    token: str,
    api_version: str,
    run: dict,
    card_file: Path,
) -> str:
    if not card_file.exists():
        raise RuntimeError(f"Run card image was not found: {card_file}")

    url = f"https://graph.facebook.com/{api_version}/{page_id}/photos"

    with card_file.open("rb") as image_file:
        response = requests.post(
            url,
            data={
                "caption": format_message(run),
                "published": "true",
                "access_token": token,
            },
            files={"source": (card_file.name, image_file, "image/png")},
            timeout=60,
        )

    try:
        result = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Facebook Graph API returned non-JSON HTTP {response.status_code}: "
            f"{response.text}"
        ) from exc

    if not response.ok:
        raise RuntimeError(
            f"Facebook Graph API returned HTTP {response.status_code}: {result}"
        )

    post_id = result.get("post_id") or result.get("id")
    if not post_id:
        raise RuntimeError(
            f"Facebook Graph API response did not include a post id: {result}"
        )

    return str(post_id)


def get_runs() -> list[dict]:
    data = load_json(RUN_LOGS_FILE)
    runs = data.get("runs") if isinstance(data, dict) else None
    if not isinstance(runs, list) or not runs:
        raise RuntimeError("data/run_logs.json was not found or contains no runs.")
    return runs


def collect_new_window(
    runs: list[dict],
    watermark_activity_id: str,
) -> tuple[list[dict], bool]:
    """Return runs newer than the last fully synchronized activity."""
    if not watermark_activity_id:
        return [runs[0]], True

    window: list[dict] = []
    for run in runs:
        activity_id = str(run.get("activity_id") or "").strip()
        if activity_id == watermark_activity_id:
            return window, True
        window.append(run)

    return window, False


def main() -> None:
    token = os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
    page_id = os.environ.get("FACEBOOK_PAGE_ID", DEFAULT_PAGE_ID).strip()
    api_version = os.environ.get(
        "FACEBOOK_GRAPH_API_VERSION",
        DEFAULT_API_VERSION,
    ).strip()

    if not token:
        print(
            "FACEBOOK_PAGE_ACCESS_TOKEN is not configured. "
            "Skipping Facebook post without failing Garmin updates."
        )
        return

    runs = get_runs()
    state = load_json(STATE_FILE)

    legacy_last_id = str(state.get("last_posted_activity_id") or "").strip()
    watermark_id = str(
        state.get("watermark_activity_id") or legacy_last_id
    ).strip()

    posted_ids = {
        str(value)
        for value in state.get("posted_activity_ids", [])
        if value is not None
    }
    if legacy_last_id:
        posted_ids.add(legacy_last_id)

    new_window, watermark_found = collect_new_window(runs, watermark_id)

    if not watermark_found:
        print(
            "Facebook watermark was not found in the current run log. "
            "The script will post only the newest run to avoid backfilling old history."
        )
        new_window = [runs[0]]

    pending_runs = [
        run
        for run in reversed(new_window)
        if str(run.get("activity_id") or "").strip() not in posted_ids
    ]

    if not pending_runs:
        newest_id = str(runs[0].get("activity_id") or "").strip()
        if watermark_found and newest_id:
            state["watermark_activity_id"] = newest_id
            state["posted_activity_ids"] = [newest_id]
            state["page_id"] = page_id
            state["post_format"] = "image_card"
            save_state(state)
        print("No unposted Garmin runs found for Facebook.")
        return

    print(f"Found {len(pending_runs)} unposted Garmin run(s) for Facebook.")

    with tempfile.TemporaryDirectory(prefix="takrun-facebook-") as temp_dir:
        temp_dir_path = Path(temp_dir)

        for run in pending_runs:
            activity_id = str(run.get("activity_id") or "").strip()
            if not activity_id:
                print("Skipping a run without activity_id.")
                continue

            card_path = temp_dir_path / f"run_card_{activity_id}.png"
            generate_run_card(run, card_path)
            post_id = post_photo(
                page_id,
                token,
                api_version,
                run,
                card_path,
            )

            posted_ids.add(activity_id)
            state.update(
                {
                    "last_posted_activity_id": run.get("activity_id"),
                    "last_facebook_post_id": post_id,
                    "last_posted_at": datetime.now(timezone.utc).isoformat(),
                    "page_id": page_id,
                    "post_format": "image_card",
                    "posted_activity_ids": list(posted_ids)[-MAX_POSTED_IDS:],
                }
            )
            # Save after every successful post. If a later post fails, the
            # successful ones will not be duplicated on the next workflow run.
            save_state(state)

            print(
                f"Posted Garmin activity {activity_id} with its own run card "
                f"to Facebook Page. Facebook post id: {post_id}"
            )

    newest_id = str(runs[0].get("activity_id") or "").strip()
    if watermark_found and newest_id:
        # Every run between the previous watermark and newest run is now handled.
        state["watermark_activity_id"] = newest_id
        state["posted_activity_ids"] = [newest_id]
        save_state(state)
        print(f"Advanced Facebook synchronization watermark to {newest_id}.")


if __name__ == "__main__":
    main()
