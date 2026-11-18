# AI Usage Disclosure

## Tools used

- Claude (Anthropic), Claude Sonnet 5.5 via claude.ai


## What I used them for

- Writing the first complete version of the four modules from the assignment text and the starter skeleton.
- Running the public test script and checking edge cases (non-ASCII letters/digits, non-zero-padded dates, CRLF, nan/inf prices).
- Explaining the code to me.

## Which parts of the code were AI-generated or substantially AI-assisted

| File | Function or part | How (generated / modified / explained) |
| --- | --- | --- |
| validator.py | load_airports, validate_row, to_record, parse_datetime | generated |
| csv_loader.py | parse_files | generated |
| query.py | run_query, run_queries | generated |
| flight_parser.py | main, argparse setup, logging setup, response file | generated |

## Key prompts

1. Uploaded the assignment text and starter zip and asked: "help me finish the last Python lab of my programming languages course".
2. TODO - add your own follow-up prompts here.

## What I changed or verified myself

TODO - write what YOU did: e.g. read through every function, ran python tests/run_public_tests.py, tried my own edge cases, set my student constants.
