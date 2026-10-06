"""Checking that seeding left every other company's rows as they were."""
from __future__ import annotations

from sqlmodel import Session, select

from web_api.db.models import Company
from web_api.db.session import engine

from ..ids import COMPANY_ID
from .counts import table_counts

Snapshot = dict[str, dict[str, int]]


def other_companies() -> Snapshot:
    """Each other company's row counts, by company name."""
    with Session(engine) as session:
        companies = session.exec(select(Company).where(Company.id != COMPANY_ID)).all()
        return {f"{company.name} ({company.id})": table_counts(session, company.id)
                for company in companies}


def changes(before: Snapshot, after: Snapshot) -> list[str]:
    """What differs between two snapshots, one line per changed count."""
    found = []
    for company, counts in before.items():
        for table, count in counts.items():
            now = after.get(company, {}).get(table)
            if now != count:
                found.append(f"{company}: {table} {count} -> {now}")
    return found
