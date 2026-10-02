from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlmodel import Field, SQLModel

from ._base import _ts, _uuid


class MarketplaceQuery(SQLModel, table=True):
    """A question put to a marketplace connector, and until when its answer is reused.

    Public data, shared by every organization; a product page read is a query whose text is the
    page's URL.
    """

    __tablename__ = "marketplace_queries"
    __table_args__ = (
        UniqueConstraint("connector", "market", "query", name="uq_marketplace_query"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    connector: str = Field(sa_type=String, nullable=False)
    market: str = Field(sa_type=String, nullable=False)
    query: str = Field(sa_type=String, nullable=False)
    status: str = Field(sa_type=String, nullable=False)
    error: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    fetched_at: datetime = Field(sa_column=_ts())
    expires_at: datetime = Field(sa_type=DateTime(timezone=True), nullable=False)
