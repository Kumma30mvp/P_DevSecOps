"""API minima en FastAPI para demostracion DevSecOps.

Endpoints:
  GET  /              -> info y links (health, docs)
  GET  /health        -> healthcheck
  GET  /items         -> lista items
  POST /items         -> crea item (validado con Pydantic)
  GET  /admin/status  -> estado "administrativo" (VULNERABILIDAD SIMULADA)

NOTA DE SEGURIDAD (intencional / academico):
  /admin/status NO tiene autenticacion ni autorizacion. Esto es un hallazgo
  controlado y deliberado (Broken Access Control - OWASP A01, STRIDE:
  Elevation of Privilege / Information Disclosure) para que SAST/DAST y la
  revision manual produzcan evidencia. NO usar este patron en produccion.
"""
import time

from fastapi import FastAPI, Request, status

from app import storage
from app.models import Item, ItemCreate

app = FastAPI(
    title="DevSecOps MVP API",
    version="0.1.0",
    description="API minima para demostrar pipeline DevSecOps (SAST/DAST/SCA/STRIDE).",
)

_START_TIME = time.time()

# Cabeceras de seguridad aplicadas a TODAS las respuestas.
# Mitigan hallazgos tipicos del escaneo DAST (OWASP ZAP):
#   - Anti-clickjacking (X-Frame-Options / CSP frame-ancestors)
#   - X-Content-Type-Options (evita MIME sniffing)
#   - Content-Security-Policy (reduce superficie XSS)
# La CSP permite el CDN de Swagger para que /docs siga funcionando.
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' https://cdn.jsdelivr.net; "
        "frame-ancestors 'none'"
    ),
}


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Inyecta cabeceras de seguridad en cada respuesta HTTP."""
    response = await call_next(request)
    for header, value in _SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    return response


@app.get("/", tags=["info"])
def root() -> dict:
    """Endpoint informativo con enlaces utiles."""
    return {
        "service": "DevSecOps MVP API",
        "version": "0.1.0",
        "links": {"health": "/health", "docs": "/docs", "openapi": "/openapi.json"},
    }


@app.get("/health", tags=["info"])
def health() -> dict:
    """Healthcheck simple usado por Docker y el pipeline."""
    return {"status": "ok"}


@app.get("/items", response_model=list[Item], tags=["items"])
def get_items() -> list[Item]:
    """Devuelve todos los items en memoria."""
    return storage.list_items()


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED, tags=["items"])
def create_item(item: ItemCreate) -> Item:
    """Crea un item validado con Pydantic y lo guarda en memoria."""
    return storage.add_item(item)


@app.get("/admin/status", tags=["admin"])
def admin_status() -> dict:
    """Estado administrativo SIN autenticacion (vulnerabilidad simulada).

    Expone informacion sensible simulada a proposito para generar hallazgos
    en los escaneos. Ver nota de seguridad en el docstring del modulo.
    """
    return {
        "uptime_seconds": round(time.time() - _START_TIME, 2),
        "items_count": storage.count(),
        "debug": True,
        "warning": "Endpoint sin autenticacion - vulnerabilidad simulada para fines academicos",
    }
