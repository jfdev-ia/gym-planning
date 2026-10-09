"""Collect the group classes of several Let's Go Fitness clubs into one weekly report."""
import argparse
import json
from datetime import date
from pathlib import Path

from gym_planning import fetch
from gym_planning.extract import extract_classes
from gym_planning.mailer import send_email
from gym_planning.report import build_report

CLUBS = {
    "Flon": "https://www.letsgofitness.ch/fr/club/lausanne-flon/",
    "Saint-François": "https://www.letsgofitness.ch/fr/club/lausanne-saint-francois/",
    "Grancy": "https://www.letsgofitness.ch/fr/club/lausanne-grancy/",
    "La Borde": "https://www.letsgofitness.ch/fr/club/lausanne-la-borde/",
    "Malley": "https://www.letsgofitness.ch/fr/club/malley/",
}

ROOT = Path(__file__).resolve().parents[2]  # the project folder
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "out"


def get_pages(use_saved: bool) -> dict[str, str]:
    """Step 1: load the club pages, or reuse the ones saved today."""
    if use_saved:
        pages = {}
        for club in CLUBS:
            path = RAW_DIR / f"{club}_{date.today()}.html"
            if path.exists():
                pages[club] = path.read_text(encoding="utf-8")
        print(f"using {len(pages)} saved pages")
        return pages
    pages = fetch.fetch_clubs(CLUBS)
    for club, html in pages.items():
        fetch.save_html(html, RAW_DIR / f"{club}_{date.today()}.html")
    return pages


def get_classes(pages: dict[str, str]) -> list[dict]:
    """Step 2: one LLM call per club."""
    classes = []
    for club, html in pages.items():
        try:
            found = extract_classes(html)
        except Exception as error:  # one club failing must not stop the run
            print(f"{club}: extraction FAILED, {error}")
            continue
        per_day = {}
        for c in found:
            per_day[c["day"][:3]] = per_day.get(c["day"][:3], 0) + 1
        print(f"{club}: {len(found)} classes {per_day}")  # check: every day should be there
        classes += [{"club": club, **c} for c in found]
    return classes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-fetch", action="store_true", help="reuse the pages saved today")
    parser.add_argument("--mail", action="store_true", help="also send the report by email")
    parser.add_argument("--headless", action="store_true", help="hide the browser window")
    args = parser.parse_args()
    fetch.HEADLESS = args.headless

    classes = get_classes(get_pages(args.no_fetch))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / f"planning_{date.today()}.json"
    json_path.write_text(json.dumps(classes, ensure_ascii=False, indent=2), encoding="utf-8")

    report = build_report(classes, list(CLUBS))
    report_path = OUT_DIR / f"planning_{date.today()}.html"
    report_path.write_text(report, encoding="utf-8")
    print(f"{len(classes)} classes saved to {json_path}\nreport saved to {report_path}")

    if args.mail:
        send_email(f"Group classes, week of {date.today():%d.%m.%Y}", report)
        print("report sent by email")


if __name__ == "__main__":
    main()
