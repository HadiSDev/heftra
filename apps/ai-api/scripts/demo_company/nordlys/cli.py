"""The demo company's command line: seed it, reset it, or remove it."""
from __future__ import annotations

import argparse
import logging

from .ids import COMPANY_ID
from .seed import SeedOutcome, remove, seed
from .verify.guard import changes, other_companies
from .verify.report import print_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Seed the fictional demo company Nordlys Byg A/S into the dev database.")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--reset", action="store_true",
                        help="also delete and rewrite the demo's suppliers before seeding")
    action.add_argument("--remove", action="store_true",
                        help="delete the demo company, its tree and its suppliers, and stop")
    parser.add_argument("--no-fx-warm", action="store_true",
                        help="don't fill the shared ECB rate cache for the seeded days")
    parser.add_argument("--no-report", action="store_true",
                        help="don't read the company back through the app's reports")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)

    before = other_companies()
    if args.remove:
        if remove():
            print(f"Removed the demo company {COMPANY_ID}.")
        else:
            print("The demo company wasn't there.")
    else:
        outcome = seed(reset=args.reset, warm_fx=not args.no_fx_warm)
        _print_outcome(outcome)
        if not args.no_report:
            print_report(COMPANY_ID)
    changed = changes(before, other_companies())
    if changed:
        print("Other companies changed:\n  " + "\n  ".join(changed))
        return 1
    print("Other companies' rows are unchanged.")
    return 0


def _print_outcome(outcome: SeedOutcome) -> None:
    print(f"Seeded Nordlys Byg A/S ({COMPANY_ID}): {outcome.invoices} invoices, "
          f"{outcome.lines} lines, {outcome.items} items, {outcome.alternatives} alternatives, "
          f"{outcome.findings} findings {outcome.findings_by_kind}.")
    if outcome.storage_error is not None:
        print(f"Agreement PDFs were not stored: {outcome.storage_error}")
    if outcome.days_without_rate:
        print(f"{outcome.days_without_rate} seeded days have no EUR rate in the cache.")
