"""Flight Schedule Parser and Query Tool - command-line entry point.

Run from the project folder, for example:
    python flight_parser.py -i data/db.csv -a data/airports.txt
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

# TODO: fill in your details: plain ASCII, no spaces or underscores.
STUDENT_ID = "251ADB131"
FIRST_NAME = "Akram"
LAST_NAME = "Mammadov"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flight_parser.py",
        description="Validate flight CSV files, store them as a JSON "
                    "database and answer queries.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE", help="parse a single CSV file")
    source.add_argument("-d", metavar="FOLDER", help="parse every .csv file in a folder")
    source.add_argument("-j", metavar="FILE", help="load an existing JSON database")
    parser.add_argument("-a", metavar="FILE", help="airport list (required with -i/-d)")
    parser.add_argument("-o", metavar="FILE", help="output database path (default: db.json)")
    parser.add_argument("-q", metavar="FILE", help="JSON file with queries")
    parser.add_argument("-r", metavar="FOLDER", default=".",
                        help="folder for the response file (default: current directory)")
    return parser


class RuntimeProblem(Exception):
    """An expected runtime problem; reported as 'Error: ...' with exit code 1."""


def read_json(path: str):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except OSError as exc:
        raise RuntimeProblem(f"cannot read {path}: {exc.strerror or exc}")
    except ValueError as exc:  # JSONDecodeError and UnicodeDecodeError
        raise RuntimeProblem(f"{path} is not valid JSON: {exc}")
    except RecursionError:
        raise RuntimeProblem(f"{path} is nested too deeply")


def write_json(path: str, data) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as exc:
        raise RuntimeProblem(f"cannot write {path}: {exc.strerror or exc}")


def csv_paths(args) -> list[str]:
    if args.i is not None:
        if not os.path.isfile(args.i):
            raise RuntimeProblem(f"file not found: {args.i}")
        return [args.i]
    if not os.path.isdir(args.d):
        raise RuntimeProblem(f"folder not found: {args.d}")
    try:
        names = sorted(n for n in os.listdir(args.d) if n.endswith(".csv")
                       and os.path.isfile(os.path.join(args.d, n)))
    except OSError as exc:
        raise RuntimeProblem(f"cannot read folder {args.d}: {exc.strerror or exc}")
    if not names:
        raise RuntimeProblem(f"no .csv files in {args.d}")
    return [os.path.join(args.d, n) for n in names]


def build_database(args) -> list[dict]:
    """Parse CSV files (writing db and errors.log) or load a JSON database."""
    if args.j is not None:
        db = read_json(args.j)
        if not isinstance(db, list) or not all(isinstance(r, dict) for r in db):
            raise RuntimeProblem(f"{args.j} must contain a JSON array of objects")
        return db

    paths = csv_paths(args)
    try:
        airports = load_airports(args.a)
    except OSError as exc:
        raise RuntimeProblem(f"cannot read {args.a}: {exc.strerror or exc}")
    except ValueError as exc:
        raise RuntimeProblem(f"{args.a} is not valid UTF-8 text: {exc}")
    try:
        records, errors = parse_files(paths, airports)
    except OSError as exc:
        raise RuntimeProblem(f"cannot read input file: {exc.filename or ''} {exc.strerror or exc}".replace("  ", " "))
    except ValueError as exc:
        raise RuntimeProblem(f"input file is not valid UTF-8 text: {exc}")

    db_path = args.o if args.o is not None else "db.json"
    write_json(db_path, records)

    log_path = os.path.join(os.path.dirname(db_path), "errors.log")
    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    try:
        handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    except OSError as exc:
        raise RuntimeProblem(f"cannot write {log_path}: {exc.strerror or exc}")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    try:
        for message in errors:
            logger.warning("%s", message)
        logger.info("%d valid rows, %d invalid rows", len(records), len(errors))
    finally:
        logger.removeHandler(handler)
        handler.close()

    print(f"{len(records)} valid flights written to {db_path}; "
          f"{len(errors)} invalid rows logged to {log_path}")
    return records


def answer_queries(args, db: list[dict]) -> None:
    queries = read_json(args.q)
    if not isinstance(queries, (dict, list)):
        raise RuntimeProblem(f"{args.q} must contain a query object or an array of them")
    response = run_queries(db, queries)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"
    path = os.path.join(args.r, name)
    write_json(path, response)
    print(f"{len(response)} query result(s) written to {path}")


def main(argv: list[str] | None = None) -> int:
    """Run the whole program and return the exit code (0, 1 or 2).

    argv is the argument list without the program name.
    None means use sys.argv[1:] (argparse does this for you).
    Do not call sys.exit() inside main(); return the code instead.
    """
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse exits on -h (0) and usage errors (2)
        return exc.code if isinstance(exc.code, int) else 0

    try:
        if args.j is None and args.a is None:
            parser.error("-a is required with -i and -d")
        if args.j is not None and args.o is not None:
            parser.error("-o cannot be used with -j")
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    try:
        db = build_database(args)
        if args.q is not None:
            answer_queries(args, db)
    except RuntimeProblem as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
