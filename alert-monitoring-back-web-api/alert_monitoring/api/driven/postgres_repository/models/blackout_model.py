import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class BlackoutDB(SQLModel, table=True):
    __tablename__ = "blackout"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    alertmanager_id: str = Field(unique=True, max_length=255)
    matchers: List[dict] = Field(default=[], sa_column=Column(JSON))
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    created_by: Optional[str] = None
    comment: Optional[str] = None
    state: str = Field(default="active")
    source: Optional[str] = None
    app_names: List[str] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
