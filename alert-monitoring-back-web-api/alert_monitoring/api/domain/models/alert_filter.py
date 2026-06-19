from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class AlertFilter(BaseModel):
    name: Optional[str] = Field(None, description="Filtro por nombre (coincidencia parcial, case-insensitive)")
    source_tool: Optional[Literal["Prometheus", "Elastic"]] = Field(None, description="Herramienta origen de la alerta")
    severity: Optional[Literal["warning", "critical", "principal"]] = Field(None, description="Nivel de severidad")
    environments: Optional[List[Literal["dev", "itg", "pre", "pro"]]] = Field(None, description="Entornos donde aplica la alerta")
    solution: Optional[str] = Field(None, description="PI fabricado (coincidencia parcial)")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="Número máximo de alertas a devolver")
    offset: Optional[int] = Field(None, ge=0, description="Número de alertas a omitir")
