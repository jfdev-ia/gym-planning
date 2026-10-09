"""Turn the HTML of a club page into a list of classes, with the LLM."""
import os
from pathlib import Path
from typing import Literal

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from mistralai.client import Mistral
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
MODEL = "mistral-small-latest"
MAX_CHARS = 60_000  # safety limit for the text sent to the LLM

Day = Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
Slot = Literal["morning", "noon", "evening"]


class GymClass(BaseModel):
    day: Day = Field(description="Day of the class, in English (lundi = Monday, mardi = Tuesday ...).")
    slot: Slot = Field(description="Part of the day the class is listed under on the page: "
                                   "matin = morning, midi = noon, soir = evening.")
    start: str = Field(description="Start time as HH:MM, for example 18:30.")
    end: str | None = Field(description="End time as HH:MM, null if not shown.")
    name: str = Field(description="Name of the class, for example BodyPump.")


class Planning(BaseModel):
    classes: list[GymClass]


SYSTEM_PROMPT = """You read the text of a gym club web page.
The page contains a weekly planning of group classes, sorted by day and by
part of the day (matin, midi, soir). List every class of the planning.
Use only what is in the text. Ignore everything that is not a class of the planning."""


def page_text(html: str) -> str:
    """Keep only the visible words of the page: the LLM does not need the HTML."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "img", "picture", "iframe"]):
        tag.decompose()
    lines = (line.strip() for line in soup.get_text("\n").splitlines())
    return "\n".join(line for line in lines if line)[:MAX_CHARS]


def extract_classes(html: str) -> list[dict]:
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    response = client.chat.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": page_text(html)},
        ],
        response_format=Planning,
        temperature=0,
    )
    return [c.model_dump() for c in response.choices[0].message.parsed.classes]
