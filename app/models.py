"""Modelos Pydantic para validacion de entrada/salida.

La validacion con constraints (min_length, gt, etc.) es evidencia tecnica
para el analisis STRIDE (Tampering) y para reducir superficie de ataque.
"""
from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """Cuerpo de entrada para crear un item (POST /items)."""

    name: str = Field(..., min_length=1, max_length=100, description="Nombre del item")
    price: float = Field(..., gt=0, description="Precio, debe ser mayor que 0")


class Item(ItemCreate):
    """Item almacenado, incluye el id asignado por el servidor."""

    id: int = Field(..., description="Identificador unico autogenerado")
