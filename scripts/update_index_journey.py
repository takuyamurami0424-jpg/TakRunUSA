from pathlib import Path

INDEX_FILE = Path("index.html")
JOURNEY_SCRIPT_TAG = '    <script src="journey-route.js"></script>\n'
DASHBOARD_SCRIPT_TAG = '    <script src="dashboard.js"></script>\n'
BLOG_SCRIPT_TAG = '    <script src="blog.js"></script>\n'
DASHBOARD_CSS_TAG = '    <link rel="stylesheet" href="dashboard.css">\n'
BLOG_CSS_TAG = '    <link rel="stylesheet" href="blog.css">\n'
GARMIN_MARKER = '<!-- 🏃 GARMIN DATA SCRIPT -->'
JOURNEY_MARKER = '    <!-- 🗺️ JOURNEY MAP SECTION (Running Log) -->'
WORKS_MARKER = '    <!-- Works -->'
HEAD_MARKER = '</head>'

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

DASHBOARD_SECTION = '''    <!-- 📊 GARMIN RUNNING DASHBOARD -->
    <section id="running-dashboard">
        <div class="section-header" style="margin-bottom: 40px;">
            <span class="section-subtitle">Garmin Performance Data</span>
            <h2 class="section-title">Running Dashboard</h2>
            <p style="color: var(--text-sub);">
                Garminのランニング履歴から、走行距離・Personal Best・月別Mileageを自動集計。
            </p>
        </div>

        <div id="dashboard-loading" class="dashboard-loading">Running dashboardを読み込んでいます...</div>
        <div id="dashboard-error" class="dashboard-error hidden">Running dashboardを読み込めませんでした。</div>

        <div id="dashboard-content" class="hidden">
            <div class="dashboard-grid">
                <div class="dashboard-card">
                    <div class="dashboard-kicker">This Month</div>
                    <div><span id="dash-month" class="dashboard-value">--</span><span class="dashboard-unit">km</span></div>
                </div>
                <div class="dashboard-card">
                    <div class="dashboard-kicker">This Year</div>
                    <div><span id="dash-year" class="dashboard-value">--</span><span class="dashboard-unit">km</span></div>
                </div>
                <div class="dashboard-card">
                    <div class="dashboard-kicker">Last 7 Days</div>
                    <div><span id="dash-week" class="dashboard-value">--</span><span class="dashboard-unit">km</span></div>
                </div>
                <div class="dashboard-card">
                    <div class="dashboard-kicker">Total Since Jul 2024</div>
                    <div><span id="dash-total" class="dashboard-value">--</span><span class="dashboard-unit">km</span></div>
                </div>
            </div>

            <div class="section-header" style="margin: 45px 0 25px;">
                <span class="section-subtitle">Personal Best</span>
                <h3 class="section-title" style="font-size: 1.7rem;">Garmin PBs</h3>
            </div>

            <div class="pb-grid">
                <div class="dashboard-card pb-card">
                    <div class="dashboard-kicker">5K</div>
                    <div id="pb-5k-time" class="pb-time">--</div>
                    <div id="pb-5k-date" class="pb-date">--</div>
                    <span id="pb-5k-badge" class="pb-badge">Waiting for data</span>
                </div>
                <div class="dashboard-card pb-card">
                    <div class="dashboard-kicker">10K</div>
                    <div id="pb-10k-time" class="pb-time">--</div>
                    <div id="pb-10k-date" class="pb-date">--</div>
                    <span id="pb-10k-badge" class="pb-badge">Waiting for data</span>
                </div>
                <div class="dashboard-card pb-card">
                    <div class="dashboard-kicker">Half Marathon</div>
                    <div id="pb-half-time" class="pb-time">--</div>
                    <div id="pb-half-date" class="pb-date">--</div>
                    <span id="pb-half-badge" class="pb-badge">Waiting for data</span>
                </div>
                <div class="dashboard-card pb-card">
                    <div class="dashboard-kicker">Marathon</div>
                    <div id="pb-marathon-time" class="pb-time">--</div>
                    <div id="pb-marathon-date" class="pb-date">--</div>
                    <span id="pb-marathon-badge" class="pb-badge">Waiting for data</span>
                </div>
            </div>

            <div class="dashboard-card mileage-card">
                <div class="dashboard-kicker">Last 12 Months</div>
                <h3 style="font-size: 1.35rem;">Monthly Mileage</h3>
                <div id="mileage-chart" class="mileage-chart" aria-label="Monthly running mileage chart"></div>
            </div>

            <div class="dashboard-card next-race-card">
                <div>
                    <div class="dashboard-kicker">Next Race</div>
                    <h3 id="next-race-name" style="font-size: 1.4rem;">Next race not set</h3>
                    <p id="next-race-meta" style="margin: 7px 0 0; color: var(--text-sub);">Add the next confirmed race when you are ready.</p>
                </div>
                <div class="next-race-days">
                    <div><span id="next-race-days" class="dashboard-value">—</span></div>
                    <div class="dashboard-kicker" style="margin-top: 4px;">Days To Go</div>
                </div>
            </div>
        </div>
    </section>
'''

BLOG_SECTION = '''    <!-- ✍️ NOTE BLOG -->
    <section id="blog-section">
        <div class="section-header" style="margin-bottom: 35px;">
            <span class="section-subtitle">Latest From My Blog</span>
            <h2 class="section-title">Official Note Blog</h2>
            <p style="color: var(--text-sub);">
                Supply Chain、アメリカ生活、ランニングについて書いています。
            </p>
        </div>

        <div class="blog-toolbar">
            <div style="color: var(--text-sub);">最新3記事を自動表示</div>
            <a id="blog-profile-link" class="blog-profile-link" href="https://note.com/tak0424" target="_blank" rel="noopener noreferrer">
                View all on note <i class="fa-solid fa-arrow-up-right-from-square"></i>
            </a>
        </div>

        <div id="blog-loading" class="blog-loading">最新記事を読み込んでいます...</div>
        <div id="blog-error" class="blog-error hidden">ブログ記事を読み込めませんでした。</div>
        <div id="blog-grid" class="blog-grid hidden"></div>
    </section>
'''


TRAINING_TREND_SECTION = '''            <div id="training-trend" class="dashboard-card training-trend-card">
                <div class="training-trend-header">
                    <div>
                        <div class="dashboard-kicker">Last 4 Weeks</div>
                        <h3 style="font-size: 1.35rem;">Training Trend</h3>
                        <p style="margin: 6px 0 0; color: var(--text-sub);">
                            Garminの直近28日間を、その前の28日間と比較します。
                        </p>
                    </div>
                    <span id="trend-change" class="trend-change">Calculating...</span>
                </div>

                <div class="trend-grid">
                    <div class="trend-metric"><div class="dashboard-kicker">Distance</div><div id="trend-distance" class="trend-value">--</div></div>
                    <div class="trend-metric"><div class="dashboard-kicker">Runs</div><div id="trend-runs" class="trend-value">--</div></div>
                    <div class="trend-metric"><div class="dashboard-kicker">Avg Pace</div><div id="trend-pace" class="trend-value">--</div></div>
                    <div class="trend-metric"><div class="dashboard-kicker">Avg HR</div><div id="trend-hr" class="trend-value">--</div></div>
                    <div class="trend-metric"><div class="dashboard-kicker">Longest Run</div><div id="trend-longest" class="trend-value">--</div></div>
                </div>

                <div class="trend-weekly-heading">Weekly mileage · 直近4週間</div>
                <div id="trend-weekly-chart" class="trend-weekly-chart" aria-label="Last four weeks running mileage"></div>
            </div>

'''

OLD_NEXT_RACE_CARD = '''            <div class="dashboard-card next-race-card">
                <div>
                    <div class="dashboard-kicker">Next Race</div>
                    <h3 id="next-race-name" style="font-size: 1.4rem;">Next race not set</h3>
                    <p id="next-race-meta" style="margin: 7px 0 0; color: var(--text-sub);">Add the next confirmed race when you are ready.</p>
                </div>
                <div class="next-race-days">
                    <div><span id="next-race-days" class="dashboard-value">—</span></div>
                    <div class="dashboard-kicker" style="margin-top: 4px;">Days To Go</div>
                </div>
            </div>'''

NEW_NEXT_RACE_CARD = '''            <div class="dashboard-card next-race-card">
                <div class="next-race-main">
                    <div class="dashboard-kicker">Next Race & Goal</div>
                    <h3 id="next-race-name" style="font-size: 1.4rem;">Next race not set</h3>
                    <p id="next-race-meta" style="margin: 7px 0 0; color: var(--text-sub);">
                        Add the next confirmed race when you are ready.
                    </p>
                    <span id="next-race-goal" class="race-goal-pill">Goal not set</span>
                </div>
                <div class="next-race-days">
                    <div><span id="next-race-days" class="dashboard-value">—</span></div>
                    <div class="dashboard-kicker" style="margin-top: 4px;">Days To Go</div>
                </div>
            </div>'''


def main() -> None:
    text = INDEX_FILE.read_text(encoding="utf-8")
    changed = False

    if OLD_DESCRIPTION in text:
        text = text.replace(OLD_DESCRIPTION, NEW_DESCRIPTION, 1)
        changed = True

    css_tags = ""
    if 'href="dashboard.css"' not in text:
        css_tags += DASHBOARD_CSS_TAG
    if 'href="blog.css"' not in text:
        css_tags += BLOG_CSS_TAG

    if css_tags:
        if HEAD_MARKER not in text:
            raise RuntimeError("</head> was not found in index.html")
        text = text.replace(HEAD_MARKER, css_tags + HEAD_MARKER, 1)
        changed = True

    if 'id="running-dashboard"' not in text:
        if JOURNEY_MARKER not in text:
            raise RuntimeError("Journey section marker was not found in index.html")
        text = text.replace(JOURNEY_MARKER, DASHBOARD_SECTION + JOURNEY_MARKER, 1)
        changed = True

    if 'id="blog-section"' not in text:
        if WORKS_MARKER not in text:
            raise RuntimeError("Works section marker was not found in index.html")
        text = text.replace(WORKS_MARKER, BLOG_SECTION + WORKS_MARKER, 1)
        changed = True

    if 'id="training-trend"' not in text:
        race_marker = '            <div class="dashboard-card next-race-card">'
        if race_marker not in text:
            raise RuntimeError("Next Race card marker was not found in index.html")
        text = text.replace(race_marker, TRAINING_TREND_SECTION + race_marker, 1)
        changed = True

    if 'id="next-race-goal"' not in text and OLD_NEXT_RACE_CARD in text:
        text = text.replace(OLD_NEXT_RACE_CARD, NEW_NEXT_RACE_CARD, 1)
        changed = True

    script_tags = ""
    if 'src="journey-route.js"' not in text:
        script_tags += JOURNEY_SCRIPT_TAG
    if 'src="dashboard.js"' not in text:
        script_tags += DASHBOARD_SCRIPT_TAG
    if 'src="blog.js"' not in text:
        script_tags += BLOG_SCRIPT_TAG

    if script_tags:
        if GARMIN_MARKER not in text:
            raise RuntimeError("Garmin data script marker was not found in index.html")
        text = text.replace(GARMIN_MARKER, script_tags + GARMIN_MARKER, 1)
        changed = True

    if OLD_RUNNING_CARD in text:
        text = text.replace(OLD_RUNNING_CARD, NEW_RUNNING_CARD, 1)
        changed = True

    if changed:
        INDEX_FILE.write_text(text, encoding="utf-8")
        print("index.htmlをGarmin Dashboard/Training Trend/Journey/Blog連携に更新しました。")
    else:
        print("index.htmlはすでにGarmin Dashboard/Training Trend/Journey/Blog連携済みです。")


if __name__ == "__main__":
    main()
