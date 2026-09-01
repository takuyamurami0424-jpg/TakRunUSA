from pathlib import Path

INDEX = Path("index.html")

CSS_TAG = '    <link rel="stylesheet" href="run-card.css">\n'
JS_TAG = '    <script src="run-card.js"></script>\n'
HEAD_MARKER = "</head>"
SCRIPT_MARKER = "<!-- 🏃 GARMIN DATA SCRIPT -->"
DASHBOARD_MARKER = "    <!-- 📊 GARMIN RUNNING DASHBOARD -->"

SECTION = '''    <!-- 🖼️ AUTO-GENERATED GARMIN RUN CARD -->
    <section id="latest-run-card-section">
        <div class="section-header" style="margin-bottom: 35px;">
            <span class="section-subtitle">Auto-Generated Run Card</span>
            <h2 class="section-title">Latest Garmin Run Card</h2>
            <p style="color: var(--text-sub);">
                Garminの最新トレーニングから自動生成。ホームページとFacebook投稿に同じカードを使用します。
            </p>
        </div>

        <div class="latest-run-image-shell">
            <img
                id="latest-run-card-image"
                src="assets/latest_run_card.png"
                alt="Latest Garmin run performance card"
                loading="lazy"
            >
            <div class="latest-run-image-meta">
                <span id="latest-run-card-updated">Updated automatically from Garmin</span>
                <a href="run-logs.html" target="_blank" rel="noopener">
                    View full running log <i class="fa-solid fa-arrow-up-right-from-square"></i>
                </a>
            </div>
        </div>
    </section>
'''


def main():
    text = INDEX.read_text(encoding="utf-8")
    changed = False

    if 'href="run-card.css"' not in text:
        if HEAD_MARKER not in text:
            raise RuntimeError("</head> marker not found")
        text = text.replace(HEAD_MARKER, CSS_TAG + HEAD_MARKER, 1)
        changed = True

    if 'id="latest-run-card-section"' not in text:
        if DASHBOARD_MARKER not in text:
            raise RuntimeError("Running Dashboard marker not found")
        text = text.replace(DASHBOARD_MARKER, SECTION + DASHBOARD_MARKER, 1)
        changed = True

    if 'src="run-card.js"' not in text:
        if SCRIPT_MARKER not in text:
            raise RuntimeError("Garmin script marker not found")
        text = text.replace(SCRIPT_MARKER, JS_TAG + SCRIPT_MARKER, 1)
        changed = True

    if changed:
        INDEX.write_text(text, encoding="utf-8")
        print("index.html updated with auto-generated Garmin run card.")
    else:
        print("Run card integration is already present.")


if __name__ == "__main__":
    main()
