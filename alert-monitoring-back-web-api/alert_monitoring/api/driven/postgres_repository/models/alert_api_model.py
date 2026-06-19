import uuid
from typing import List, Optional

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class AlertApiDB(SQLModel, table=True):
    __tablename__ = "alert_api"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    rule_id: str = Field(index=True)
    name: str
    severity: Optional[str] = None
    notification_channel: Optional[str] = None
    apis_alertadas: List[str] = Field(default=[], sa_column=Column(JSON))
    message: Optional[str] = None
