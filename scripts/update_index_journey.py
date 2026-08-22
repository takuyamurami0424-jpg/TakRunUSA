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

OLD_RUNNING_CARD = '''            <div class="card">
                <span style="color:var(--accent); font-weight:700; font-size:0.8rem;">LIFESTYLE</span>
                <h3>Running Logs</h3>
                <p style="color:#718096; margin-bottom: 15px;">Documenting marathons across the US.</p>
                <!-- 実際にファイルをアップロードしたら href="running_logs.xlsx" 等に書き換えてください -->
                <a href="#" class="btn-outline" style="font-size: 0.8rem; padding: 8px 20px;" download>
                    <i class="fa-solid fa-file-excel"></i> Download Logs
                </a>
            </div>'''

NEW_RUNNING_CARD = '''            <a href="run-logs.html" target="_blank" rel="noopener" class="card" aria-label="Open Garmin Running Logs">
                <span style="color:var(--accent); font-weight:700; font-size:0.8rem;">LIFESTYLE</span>
                <h3>Running Logs</h3>
                <p style="color:#718096; margin-bottom: 15px;">Garmin running history, updated automatically.</p>
                <span class="btn-outline" style="font-size: 0.8rem; padding: 8px 20px;">
                    <i class="fa-solid fa-person-running"></i> View Runs
                </span>
            </a>'''


def main() -> None:
    text = INDEX_FILE.read_text(encoding="utf-8")
    changed = False

    if OLD_DESCRIPTION in text:
        text = text.replace(OLD_DESCRIPTION, NEW_DESCRIPTION, 1)
        changed = True

    if 'src="journey-route.js"' not in text:
        if MARKER not in text:
            raise RuntimeError("Garmin data script marker was not found in index.html")

        text = text.replace(MARKER, SCRIPT_TAG + MARKER, 1)
        changed = True

    if OLD_RUNNING_CARD in text:
        text = text.replace(OLD_RUNNING_CARD, NEW_RUNNING_CARD, 1)
        changed = True

    if changed:
        INDEX_FILE.write_text(text, encoding="utf-8")
        print("index.htmlをGarmin/Journey連携に更新しました。")
    else:
        print("index.htmlはすでにGarmin/Journey連携済みです。")


if __name__ == "__main__":
    main()
