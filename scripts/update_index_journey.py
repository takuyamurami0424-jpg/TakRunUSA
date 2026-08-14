from pathlib import Path

INDEX_FILE = Path("index.html")
SCRIPT_TAG = '    <script src="journey-route.js"></script>\n'
MARKER = '<!-- 🏃 GARMIN DATA SCRIPT -->'

OLD_DESCRIPTION = (
    "                2024年7月から現在までの累計走行距離を地図上に可視化。<br>\n"
    "                ジョージア州から西へ約3000km、仮想の旅を続けています。"
)

NEW_DESCRIPTION = (
    "                2024年7月からのGarmin累計走行距離を地図上に可視化。<br>\n"
    "                距離が増えるたびに次の目的地へ進み、世界一周を目指します。"
)


def main() -> None:
    text = INDEX_FILE.read_text(encoding="utf-8")
    changed = False

    if OLD_DESCRIPTION in text:
        text = text.replace(OLD_DESCRIPTION, NEW_DESCRIPTION, 1)
        changed = True

    if 'src="journey-route.js"' not in text:
        if MARKER not in text:
            raise RuntimeError("Garmin data script marker was not found in index.html")

        text = text.replace(
            MARKER,
            SCRIPT_TAG + MARKER,
            1,
        )
        changed = True

    if changed:
        INDEX_FILE.write_text(text, encoding="utf-8")
        print("index.htmlをJourney自動ルート対応に更新しました。")
    else:
        print("index.htmlはすでにJourney自動ルート対応済みです。")


if __name__ == "__main__":
    main()
