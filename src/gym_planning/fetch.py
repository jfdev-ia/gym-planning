"""Open each club page with Playwright and return its HTML, planning included."""
import time
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

BROWSER = "firefox"
HEADLESS = False     # False = you see the window
PAUSE_SECONDS = 5    # wait between two clubs, to be gentle with the site


def open_planning(page, url: str) -> str:
    """Open a club page, click "Voir planning" if it is there, return all the HTML."""
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)  # let the page build itself
    try:
        page.get_by_text("Voir planning").first.click(timeout=5000)
        page.wait_for_timeout(3000)
    except PlaywrightError:
        pass  # no button, or it could not be clicked: keep the page as it is
    # The planning can be in the page, in an iframe or in a new tab: take them all.
    parts = [frame.content() for tab in page.context.pages for frame in tab.frames]
    return "\n".join(parts)


def fetch_clubs(clubs: dict[str, str]) -> dict[str, str]:
    """{club name: url} -> {club name: html}. A club that fails is left out."""
    pages = {}
    with sync_playwright() as p:
        browser = getattr(p, BROWSER).launch(headless=HEADLESS)
        for number, (club, url) in enumerate(clubs.items(), start=1):
            if number > 1:
                time.sleep(PAUSE_SECONDS)  # no page is open here, so a plain sleep is fine
            context = browser.new_context()  # fresh tabs for each club
            try:
                pages[club] = open_planning(context.new_page(), url)
                print(f"{number}/{len(clubs)} {club}: page loaded")
            except PlaywrightError as error:
                print(f"{number}/{len(clubs)} {club}: FAILED, {str(error).splitlines()[0]}")
            context.close()
        browser.close()
    return pages


def save_html(html: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
