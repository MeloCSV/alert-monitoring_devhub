import uuid
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON

class AlertDB(SQLModel, table=True):
    __tablename__ = "alert_app"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True)
    description: str
    source_tool: str
    severity: str
    chips: List[str] = Field(default=[], sa_column=Column(JSON))
    environments: List[str] = Field(default=[], sa_column=Column(JSON))
    solution: Optional[str] = None
    notification_channel: Optional[str] = None
