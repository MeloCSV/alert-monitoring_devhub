import uuid
from typing import List, Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


class DefaultAlertDB(SQLModel, table=True):
    __tablename__ = "default_alert_app"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    raw_name: str = Field(unique=True)
    display_name: str
    raw_description: Optional[str] = Field(default=None)
    display_description: Optional[str] = Field(default=None)
    severity: Optional[str] = Field(default=None)
    notification_channel: Optional[str] = Field(default=None)
    excluded_namespaces: List[str] = Field(default=[], sa_column=Column(JSON))
    included_namespaces: List[str] = Field(default=[], sa_column=Column(JSON))
    excluded_jobs: List[str] = Field(default=[], sa_column=Column(JSON))
