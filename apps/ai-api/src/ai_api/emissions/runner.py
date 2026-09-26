"""Match a company's lines to emission sectors: `python -m ai_api.emissions.runner --company-id <id>`."""
from __future__ import annotations

import argparse
import logging
import sys

from sqlmodel import Session

from web_api.db.models import Company
from web_api.db.session import engine

from .lines import match_company

LABELS = {
    "agent": "matched by the agent",
    "fallback": "matched by the fallback",
    "unmatched": "nothing fits",
    "cached": "answered from the cache",
    "failed": "failed",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Match a company's invoice lines to the emission sectors their spend is "
                    "estimated with. A sector a person chose is never changed.",
    )
    parser.add_argument("--company-id", required=True)
    parser.add_argument("--limit", type=int, default=None,
                        help="Match at most this many lines, to pace a large backlog")
    parser.add_argument("--rematch", action="store_true",
                        help="Forget the AI's sectors and cached answers for this company, and "
                             "ask again")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    with Session(engine) as session:
        if session.get(Company, args.company_id) is None:
            print(f"No company with id {args.company_id}.")
            return 1
        counts = match_company(session, args.company_id, limit=args.limit, rematch=args.rematch)

    print("=== emission sectors ===")
    if "skipped" in counts:
        print(f"Nothing matched: {counts['skipped']}. Import emission factors first.")
        return 0
    for key, label in LABELS.items():
        print(f"{label}: {counts[key]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
