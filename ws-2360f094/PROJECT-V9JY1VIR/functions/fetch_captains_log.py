from _gen import *  # <AUTO GENERATED>
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CAPTAINS_LOG_URL = "https://sanctuarycruises.com/captains-log/"
CACHE_TTL = 1800  # 30 minutes — log updates at most once daily

_log_cache: dict | None = None
_cache_time: float = 0.0


@func_description(
    "Fetch the Sanctuary Cruises Captain's Log from sanctuarycruises.com to get "
    "the most recent wildlife sightings and trip reports from Monterey Bay. "
    "Call this when a caller asks what has been seen lately, what is out there right now, "
    "recent sightings, what was spotted on the last trip, or whether a specific species "
    "has been seen recently."
)
def fetch_captains_log(conv: Conversation):
    global _log_cache, _cache_time
    now = time.time()

    if _log_cache is not None and now - _cache_time < CACHE_TTL:
        return _log_cache

    try:
        req = Request(
            CAPTAINS_LOG_URL,
            headers={"User-Agent": "SanctuaryCruisesVoiceAgent/1.0", "Accept": "text/html"},
        )
        with urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, Exception) as exc:
        conv.log.warning(f"fetch_captains_log: HTTP error: {exc}")
        return {
            "source": "error",
            "message": (
                "Could not reach the Captain's Log right now. "
                "Tell the caller they can read the latest trip reports at sanctuarycruises.com/captains-log. "
                "Use seasonal knowledge to answer any species questions."
            ),
        }

    entries = _parse_log(html)

    if not entries:
        return {
            "source": "captains_log",
            "message": "Captain's Log was fetched but no entries could be parsed. Use seasonal knowledge to answer.",
            "entries": [],
        }

    result = {
        "source": "captains_log",
        "url": CAPTAINS_LOG_URL,
        "entries": entries[:6],
    }
    _log_cache = result
    _cache_time = now
    return result


def _strip_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&nbsp;", " ")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )
    return re.sub(r"\s+", " ", text).strip()


def _parse_log(html: str) -> list:
    entries = []

    # Date pattern: "TUESDAY, MAY 19, 2026" anywhere in the page
    date_re = re.compile(
        r"\b(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY),\s+"
        r"(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\s+"
        r"(\d{1,2}),\s+(\d{4})\b"
    )

    # Entry titles: h2 with a /captains-log/entry- href
    title_re = re.compile(
        r'<h2[^>]*>\s*<a[^>]+href="(/captains-log/entry-[^"]+)"[^>]*>(.*?)</a>\s*</h2>',
        re.DOTALL,
    )

    date_matches = list(date_re.finditer(html))
    title_matches = list(title_re.finditer(html))

    if not title_matches:
        return []

    for i, title_m in enumerate(title_matches):
        title = _strip_tags(title_m.group(2))
        path = title_m.group(1)
        url = path if path.startswith("http") else "https://sanctuarycruises.com" + path

        # Most recent date that appears before this title in the document
        title_pos = title_m.start()
        entry_date = ""
        for dm in date_matches:
            if dm.start() < title_pos:
                # Title-case the date: "Tuesday, May 19, 2026"
                entry_date = dm.group(0).title()
            else:
                break

        # Content between this title and the next
        content_start = title_m.end()
        content_end = title_matches[i + 1].start() if i + 1 < len(title_matches) else len(html)
        chunk = html[content_start:content_end]

        # Extract species from the Spotted: section
        species: list[str] = []
        spotted_m = re.search(r"Spotted:(.*?)(?:<p|<div|$)", chunk, re.DOTALL)
        if spotted_m:
            species_html = spotted_m.group(1)
            species = [_strip_tags(s) for s in re.findall(r"<a[^>]+>([^<]+)</a>", species_html)]
            species = [s for s in species if s and len(s) < 60]

        # First substantive paragraph as description
        description = ""
        for p_html in re.findall(r"<p[^>]*>(.*?)</p>", chunk, re.DOTALL):
            text = _strip_tags(p_html)
            if len(text) > 60 and "Spotted:" not in text:
                description = text[:280] + ("..." if len(text) > 280 else "")
                break

        entries.append(
            {
                "date": entry_date,
                "title": title,
                "url": url,
                "species_spotted": species,
                "description": description,
            }
        )

    return entries
