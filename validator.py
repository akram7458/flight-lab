"""Row validation: airport list loading, single-row checks, record building."""
import math
import re
from datetime import datetime

# re.ASCII matters: without it \d would also match non-ASCII digits.
_FLIGHT_ID_RE = re.compile(r"[A-Za-z0-9]{2,8}", re.ASCII)
_AIRPORT_RE = re.compile(r"[A-Z]{3}", re.ASCII)
_DATETIME_RE = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", re.ASCII)
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def parse_datetime(text: str) -> datetime | None:
    """Parse 'YYYY-MM-DD HH:MM' (strictly zero-padded); None if invalid."""
    if not isinstance(text, str) or not _DATETIME_RE.fullmatch(text):
        return None
    try:
        return datetime.strptime(text, DATETIME_FORMAT)
    except ValueError:
        return None


def load_airports(path: str) -> set[str]:
    """Read an airport list file and return the set of codes.

    One code per line. Strip whitespace; skip blank lines and lines
    starting with '#'.
    """
    airports = set()
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            code = line.strip()
            if not code or code.startswith("#"):
                continue
            airports.add(code)
    return airports


def _parse_price(text: str) -> float | None:
    """float(text) if it converts and is finite, otherwise None."""
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Check one CSV row (fields as returned by csv.reader, not yet stripped).

    Return None if the row is valid, otherwise the error code of the
    FIRST failing check (checks 1-11 in the specification, in order).
    Does not check for duplicates.
    """
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"
    flight_id, origin, destination, departure, arrival, price = (
        f.strip() for f in fields)
    if "" in (flight_id, origin, destination, departure, arrival, price):
        return "MISSING_FIELD"
    if not _FLIGHT_ID_RE.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"
    if not _AIRPORT_RE.fullmatch(origin) or origin not in airports:
        return "INVALID_ORIGIN"
    if not _AIRPORT_RE.fullmatch(destination) or destination not in airports:
        return "INVALID_DESTINATION"
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"
    dep = parse_datetime(departure)
    if dep is None:
        return "INVALID_DEPARTURE"
    arr = parse_datetime(arrival)
    if arr is None:
        return "INVALID_ARRIVAL"
    if arr <= dep:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"
    value = _parse_price(price)
    if value is None:
        return "INVALID_PRICE"
    if value <= 0:
        return "NON_POSITIVE_PRICE"
    return None


def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary.

    Keys: flight_id, origin, destination, departure_datetime,
    arrival_datetime (stripped strings) and price (float).
    """
    flight_id, origin, destination, departure, arrival, price = (
        f.strip() for f in fields)
    return {
        "flight_id": flight_id,
        "origin": origin,
        "destination": destination,
        "departure_datetime": departure,
        "arrival_datetime": arrival,
        "price": float(price),
    }
