"""Running queries against the flight database."""
import math

from validator import parse_datetime

RECORD_KEYS = ("flight_id", "origin", "destination",
               "departure_datetime", "arrival_datetime", "price")
STRING_KEYS = ("flight_id", "origin", "destination")
ALLOWED_KEYS = set(RECORD_KEYS) | {"min_price", "sort_by", "order", "limit"}


def _is_number(value) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _is_valid(query) -> bool:
    if not isinstance(query, dict):
        return False
    if not set(query) <= ALLOWED_KEYS:
        return False
    for key in STRING_KEYS:
        if key in query and not isinstance(query[key], str):
            return False
    for key in ("departure_datetime", "arrival_datetime"):
        if key in query and parse_datetime(query[key]) is None:
            return False
    for key in ("price", "min_price"):
        if key in query and not _is_number(query[key]):
            return False
    if "sort_by" in query:
        if not isinstance(query["sort_by"], str) or query["sort_by"] not in RECORD_KEYS:
            return False
    if "order" in query:
        if "sort_by" not in query:
            return False
        if not isinstance(query["order"], str) or query["order"] not in ("asc", "desc"):
            return False
    if "limit" in query:
        limit = query["limit"]
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            return False
    return True


def _matches(flight: dict, query: dict) -> bool:
    for key in STRING_KEYS:
        if key in query and flight[key] != query[key]:
            return False
    # Fixed-format datetime strings compare correctly as text.
    if "departure_datetime" in query and flight["departure_datetime"] < query["departure_datetime"]:
        return False
    if "arrival_datetime" in query and flight["arrival_datetime"] > query["arrival_datetime"]:
        return False
    if "price" in query and flight["price"] > query["price"]:
        return False
    if "min_price" in query and flight["price"] < query["min_price"]:
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object.

    Valid query:   {"query": query, "matches": [...]}
    Invalid query: {"query": query, "error": "INVALID_QUERY", "matches": []}
    """
    if not _is_valid(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}
    matches = [dict(f) for f in db if _matches(f, query)]
    if "sort_by" in query:
        # sorted() is stable, also with reverse=True: ties keep database order.
        matches = sorted(matches, key=lambda f: f[query["sort_by"]],
                         reverse=query.get("order", "asc") == "desc")
    if "limit" in query:
        matches = matches[:query["limit"]]
    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list."""
    if not isinstance(queries, list):
        queries = [queries]
    return [run_query(db, q) for q in queries]
