from typing import Optional
from pydantic import BaseModel, Field


class CatalogApp(BaseModel):
    object_id: str = Field(..., description="ID del objeto en el catálogo de aplicaciones (devhub)")
    name: str = Field(..., description="Nombre de la aplicación")
    csw_code: Optional[str] = Field(default=None, description="Código CSW de la aplicación")
