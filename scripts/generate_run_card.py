import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "latest_run.json"
OUTPUT_FILE = ROOT / "assets" / "latest_run_card.png"

WIDTH = 1200
HEIGHT = 1200

NAVY = "#082B5B"
BLUE = "#3E73B8"
SKY = "#E9F2FC"
ICE = "#F7FAFE"
WHITE = "#FFFFFF"
INK = "#102A43"
MUTED = "#6B7C93"
BORDER = "#D9E5F3"
GREEN = "#198754"
AMBER = "#B7791F"
RED = "#C53030"


def font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Bold.otf" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def width(draw, text, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def wrap(draw, text, fnt, max_width, max_lines=2):
    text = str(text or "").strip()
    if not text:
        return []

    if " " in text:
        tokens = text.split()
        joiner = " "
    else:
        tokens = list(text)
        joiner = ""

    lines = []
    current = ""
    for token in tokens:
        candidate = token if not current else current + joiner + token
        if current and width(draw, candidate, fnt) > max_width:
            lines.append(current)
            current = token
            if len(lines) >= max_lines:
                break
        else:
            current = candidate

    if len(lines) < max_lines and current:
        lines.append(current)

    original_flat = text.replace(" ", "")
    rendered_flat = "".join(lines).replace(" ", "")
    if len(rendered_flat) < len(original_flat) and lines:
        last = lines[-1]
        while last and width(draw, last + "…", fnt) > max_width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"

    return lines


def draw_lines(draw, lines, x, y, fnt, fill, gap=8):
    line_h = draw.textbbox((0, 0), "Ag", font=fnt)[3] + gap
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += line_h
    return y


def fmt(value, suffix="", decimals=None):
    if value is None or value == "":
        return "—"
    if isinstance(value, (int, float)) and decimals is not None:
        return f"{value:.{decimals}f}{suffix}"
    return f"{value}{suffix}"


def grade_color(grade):
    return {"A": GREEN, "B": BLUE, "C": AMBER}.get(str(grade).upper(), RED)


def draw_mountains(draw):
    draw.polygon([(0, 420), (160, 260), (280, 400), (420, 235), (580, 410), (720, 285), (880, 420), (1040, 250), (1200, 400), (1200, 0), (0, 0)], fill="#F4F8FD")
    draw.polygon([(0, 455), (175, 330), (330, 430), (500, 300), (655, 445), (815, 330), (970, 450), (1120, 340), (1200, 405), (1200, 525), (0, 525)], fill="#E5EFFA")


def generate_run_card(run: dict, output_file: Path = OUTPUT_FILE) -> Path:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (WIDTH, HEIGHT), ICE)
    draw = ImageDraw.Draw(image)
    draw_mountains(draw)

    rounded(draw, (28, 28, 1172, 1172), 34, WHITE, BORDER, 2)

    f_brand = font(66, True)
    f_sub = font(25, True)
    f_name = font(65, True)
    f_date = font(28)
    f_hero = font(96, True)
    f_hero_unit = font(42, True)
    f_label = font(22, True)
    f_metric = font(39, True)
    f_type = font(34, True)
    f_comment = font(24)
    f_comment_ja = font(24)
    f_footer = font(21, True)

    draw.ellipse((72, 70, 204, 202), outline=NAVY, width=6)
    draw.text((94, 92), "Tak", font=font(36, True), fill=NAVY)
    draw.text((88, 134), "RUN", font=font(31, True), fill=BLUE)

    draw.text((238, 76), "Tak Run USA", font=f_brand, fill=NAVY)
    draw.text((242, 153), "New Garmin Run  |  Garminラン更新", font=f_sub, fill=BLUE)

    name = run.get("activity_name_en") or run.get("activity_name") or "Latest Run"
    draw.text((74, 264), str(name), font=f_name, fill=NAVY)

    date = str(run.get("date") or "").replace("T", " ")
    draw.text((78, 350), f"DATE  {date}", font=f_date, fill=BLUE)

    rounded(draw, (72, 422, 650, 618), 30, NAVY)
    distance = run.get("distance_km")
    distance_text = f"{float(distance):.2f}" if distance is not None else "—"
    draw.text((112, 446), distance_text, font=f_hero, fill=WHITE)
    draw.text((126 + width(draw, distance_text, f_hero), 505), "km", font=f_hero_unit, fill="#BCD1ED")

    score = run.get("score")
    grade = str(run.get("grade") or "—")
    rounded(draw, (685, 422, 1118, 618), 30, SKY, BORDER, 2)
    draw.text((725, 450), "RUN SCORE", font=f_label, fill=MUTED)
    score_text = f"{score if score is not None else '—'}/100"
    draw.text((725, 492), score_text, font=font(60, True), fill=NAVY)
    rounded(draw, (977, 482, 1076, 573), 24, grade_color(grade))
    draw.text((1005, 493), grade, font=font(54, True), fill=WHITE)

    metrics = [
        ("DURATION", fmt(run.get("duration_minutes"), " min", 1)),
        ("PACE", fmt(run.get("pace_per_km"), "/km")),
        ("AVG HR", fmt(run.get("average_hr"), " bpm")),
        ("ELEVATION", fmt(run.get("elevation_m"), " m")),
    ]
    boxes = [(72, 654, 331, 796), (347, 654, 606, 796), (622, 654, 881, 796), (897, 654, 1118, 796)]
    for (label, value), box in zip(metrics, boxes):
        rounded(draw, box, 22, ICE, BORDER, 2)
        x1, y1, _, _ = box
        draw.text((x1 + 23, y1 + 20), label, font=f_label, fill=MUTED)
        draw.text((x1 + 23, y1 + 62), str(value), font=f_metric, fill=INK)

    run_type = str(run.get("estimated_run_type") or "Running")
    rounded(draw, (72, 830, 1118, 914), 24, NAVY)
    type_line = wrap(draw, run_type, f_type, 970, 1)
    draw.text((106, 851), type_line[0] if type_line else run_type, font=f_type, fill=WHITE)

    rounded(draw, (72, 948, 1118, 1118), 24, ICE, BORDER, 2)
    en = str(run.get("comment_en") or "")
    ja = str(run.get("comment") or "")
    y = 974
    if en:
        y = draw_lines(draw, wrap(draw, en, f_comment, 970, 2), 104, y, f_comment, INK, 6) + 4
    if ja:
        draw_lines(draw, wrap(draw, ja, f_comment_ja, 970, 2), 104, y, f_comment_ja, BLUE, 6)

    draw.text((72, 1135), "takuyamurami0424-jpg.github.io/TakRunUSA/", font=f_footer, fill=MUTED)

    image.save(output_file, "PNG", optimize=True)
    print(f"Generated {output_file} for activity {run.get('activity_id')}")
    return output_file


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing Garmin data: {DATA_FILE}")

    run = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    generate_run_card(run, OUTPUT_FILE)


if __name__ == "__main__":
    main()
