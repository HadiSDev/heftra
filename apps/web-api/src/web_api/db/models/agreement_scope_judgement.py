from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Numeric, String, UniqueConstraint
from sqlmodel import Field, SQLModel

from ._base import _ts, _uuid


class AgreementScopeJudgement(SQLModel, table=True):
    """The LLM's answer to "is this line within this term?", kept so it is asked once.

    `term_key` hashes the term's judged fields and `question_key` the line's text, so an edited
    term or a differently worded line is judged again.
    """

    __tablename__ = "agreement_scope_judgements"
    __table_args__ = (
        UniqueConstraint("term_id", "term_key", "question_key",
                         name="uq_agreement_scope_judgement"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    term_id: str = Field(sa_type=String, foreign_key="agreement_terms.id", nullable=False,
                         index=True)
    term_key: str = Field(sa_type=String, nullable=False)
    question_key: str = Field(sa_type=String, nullable=False)
    in_scope: bool = Field(sa_type=Boolean, nullable=False)
    same_item: Optional[bool] = Field(sa_type=Boolean, nullable=True, default=None)
    units_comparable: Optional[bool] = Field(sa_type=Boolean, nullable=True, default=None)
    confidence: Optional[Decimal] = Field(sa_type=Numeric(4, 3), nullable=True, default=None)
    reason: str = Field(sa_type=String, nullable=False)
    created_at: datetime = Field(sa_column=_ts())
