"""Build the weekly planning as one HTML page: one table per day, clubs side by side."""
import html
from datetime import datetime

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SLOTS = ["morning", "noon", "evening"]
CELL = 'style="padding:6px 10px;border:1px solid #d0d7de;vertical-align:top;text-align:left"'


def class_line(gym_class: dict) -> str:
    time = gym_class["start"] + (f"–{gym_class['end']}" if gym_class["end"] else "")
    return f"<b>{html.escape(time)}</b> {html.escape(gym_class['name'])}"


def build_report(classes: list[dict], clubs: list[str]) -> str:
    """classes: dicts with club, day, slot, start, end, name."""
    parts = [
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#1f2328">',
        f"<h2>Group classes, week of {datetime.now():%d %B %Y}</h2>",
    ]
    for day in DAYS:
        today = [c for c in classes if c["day"] == day]
        if not today:
            continue
        header = "".join(f"<th {CELL}>{html.escape(club)}</th>" for club in clubs)
        rows = []
        for slot in SLOTS:
            cells = []
            for club in clubs:
                found = sorted((c for c in today if c["club"] == club and c["slot"] == slot),
                               key=lambda c: c["start"])
                cells.append(f"<td {CELL}>{'<br>'.join(class_line(c) for c in found)}</td>")
            rows.append(f"<tr><th {CELL}>{slot}</th>{''.join(cells)}</tr>")
        parts.append(f"<h3>{day}</h3>")
        parts.append(f'<table style="border-collapse:collapse"><tr><th {CELL}></th>{header}</tr>'
                     + "".join(rows) + "</table>")
    parts.append("</div>")
    return "\n".join(parts)
