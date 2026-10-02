"""The benchmark's commands: build a company, grow it, and measure an analysis.

    python apps/ai-api/scripts/agreement_benchmark --database-url URL build --lines 100000
    python apps/ai-api/scripts/agreement_benchmark --database-url URL analyse --company-id ID
    python apps/ai-api/scripts/agreement_benchmark --database-url URL grow --company-id ID --lines 5000

It writes only to the database it is given, and refuses the one the app uses.
"""
from __future__ import annotations

import argparse
import os

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlmodel import Session

from ai_api.compliance.run import analyse_company
from ai_api.rag.embedding import embed
from web_api.fx.service import FxService

from dataset import build, grow
from measure import Cost, measured, stub_answer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark agreement analysis.")
    parser.add_argument("--database-url", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    built = commands.add_parser("build")
    built.add_argument("--lines", type=int, default=1_000_000)
    built.add_argument("--items", type=int, default=20_000)
    built.add_argument("--seed", type=int, default=7)
    analysed = commands.add_parser("analyse")
    analysed.add_argument("--company-id", required=True)
    grown = commands.add_parser("grow")
    grown.add_argument("--company-id", required=True)
    grown.add_argument("--lines", type=int, default=5_000)
    grown.add_argument("--seed", type=int, default=8)
    args = parser.parse_args(argv)

    if _is_app_database(args.database_url):
        print("Refusing to benchmark against the app's own database; pass another URL.")
        return 2
    engine = create_engine(args.database_url)
    with Session(engine) as session:
        if args.command == "build":
            dataset = build(session, lines=args.lines, items=args.items, seed=args.seed)
            print(f"company {dataset.company_id}, agreement {dataset.agreement_id}, "
                  f"{dataset.items} items, {args.lines} lines")
        elif args.command == "grow":
            grow(session, args.company_id, args.lines, args.seed)
            print(f"added {args.lines} lines")
        else:
            cost = measured(engine, Cost(), embed, stub_answer,
                            lambda ask, embed_fn: analyse_company(
                                session, args.company_id, ask=ask, embed_fn=embed_fn,
                                fx=FxService(session)))
            print(cost.as_json())
    return 0


def _is_app_database(url: str) -> bool:
    app_url = os.environ.get("DATABASE_URL")
    if not app_url:
        return False
    given, app = make_url(url), make_url(app_url)
    return (given.host, given.port, given.database) == (app.host, app.port, app.database)
