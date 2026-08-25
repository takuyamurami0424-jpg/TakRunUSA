import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

RSS_URL = "https://note.com/tak0424/rss"
PROFILE_URL = "https://note.com/tak0424"
OUTPUT_FILE = Path("data/blog.json")
MAX_ARTICLES = 5

MEDIA_NS = "http://search.yahoo.com/mrss/"
DC_NS = "http://purl.org/dc/elements/1.1/"


def clean_html(value: str | None, limit: int = 180) -> str:
    if not value:
        return ""

    text = re.sub(r"<script.*?</script>", " ", value, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"

    return text


def first_image_url(value: str | None) -> str | None:
    if not value:
        return None

    match = re.search(
        r'<img[^>]+src=["\']([^"\']+)["\']',
        value,
        flags=re.I,
    )
    return html.unescape(match.group(1)) if match else None


def parse_pub_date(value: str | None) -> str | None:
    if not value:
        return None

    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except (TypeError, ValueError):
        return value


def child_text(item: ET.Element, tag: str) -> str | None:
    child = item.find(tag)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def fetch_rss() -> bytes:
    request = urllib.request.Request(
        RSS_URL,
        headers={
            "User-Agent": "TakRunUSA/1.0 (+https://takuyamurami0424-jpg.github.io/TakRunUSA/)"
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def parse_articles(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")

    if channel is None:
        raise RuntimeError("note RSS channel was not found")

    articles: list[dict] = []

    for item in channel.findall("item")[:MAX_ARTICLES]:
        title = child_text(item, "title") or "Untitled"
        link = child_text(item, "link") or PROFILE_URL
        description_html = child_text(item, "description") or ""
        published = parse_pub_date(child_text(item, "pubDate"))
        creator = child_text(item, f"{{{DC_NS}}}creator")

        thumbnail = None
        media_thumbnail = item.find(f"{{{MEDIA_NS}}}thumbnail")
        if media_thumbnail is not None:
            thumbnail = media_thumbnail.attrib.get("url")

        if not thumbnail:
            media_content = item.find(f"{{{MEDIA_NS}}}content")
            if media_content is not None:
                thumbnail = media_content.attrib.get("url")

        if not thumbnail:
            enclosure = item.find("enclosure")
            if enclosure is not None and str(enclosure.attrib.get("type", "")).startswith("image/"):
                thumbnail = enclosure.attrib.get("url")

        if not thumbnail:
            thumbnail = first_image_url(description_html)

        articles.append(
            {
                "title": title,
                "url": link,
                "published_at": published,
                "creator": creator,
                "excerpt": clean_html(description_html),
                "thumbnail": thumbnail,
            }
        )

    return articles


def write_if_changed(data: dict) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    compare_data = dict(data)
    compare_data.pop("generated_at", None)

    if OUTPUT_FILE.exists():
        try:
            previous = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
            previous.pop("generated_at", None)
            if previous == compare_data:
                print("data/blog.jsonに変更はありません。")
                return
        except json.JSONDecodeError:
            pass

    OUTPUT_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("data/blog.jsonを更新しました。")


def main() -> None:
    articles = parse_articles(fetch_rss())

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "note",
        "profile_url": PROFILE_URL,
        "rss_url": RSS_URL,
        "count": len(articles),
        "articles": articles,
    }

    write_if_changed(data)
    print(f"note最新記事 {len(articles)} 件を取得しました。")


if __name__ == "__main__":
    main()
