from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Integer, Numeric, String, UniqueConstraint
from sqlmodel import Field, SQLModel

from ._base import _uuid


class AgreementTermSpend(SQLModel, table=True):
    """A confirmed term's in-scope spend in one month, with or without the agreement's supplier.

    Recalculated from the lines and their item judgements, never adjusted, so it can't drift.
    """

    __tablename__ = "agreement_term_spend"
    __table_args__ = (
        UniqueConstraint("term_id", "month", "from_supplier", name="uq_agreement_term_spend"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    term_id: str = Field(sa_type=String, foreign_key="agreement_terms.id", nullable=False,
                         index=True)
    month: date = Field(sa_type=Date, nullable=False)
    from_supplier: bool = Field(sa_type=Boolean, nullable=False)
    amount: Decimal = Field(sa_type=Numeric(16, 2), nullable=False)
    lines: int = Field(sa_type=Integer, nullable=False)
