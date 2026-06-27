"""Almacenamiento en memoria (sin base de datos).

El estado vive a nivel de modulo y se reinicia con cada arranque del proceso.
Es suficiente para el MVP y para que las herramientas DevSecOps tengan
endpoints con datos que escanear.
"""
from app.models import Item, ItemCreate

_items: list[Item] = []
_next_id: int = 1


def list_items() -> list[Item]:
    """Devuelve todos los items almacenados."""
    return list(_items)


def add_item(data: ItemCreate) -> Item:
    """Crea un item con id autoincremental y lo guarda en memoria."""
    global _next_id
    item = Item(id=_next_id, name=data.name, price=data.price)
    _items.append(item)
    _next_id += 1
    return item


def reset() -> None:
    """Reinicia el almacenamiento (util para tests)."""
    global _items, _next_id
    _items = []
    _next_id = 1


def count() -> int:
    """Cantidad de items almacenados."""
    return len(_items)
