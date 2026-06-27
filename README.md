# DevSecOps MVP API

API mínima en **Python + FastAPI** creada como base para un proyecto final de
DevOps/DevSecOps. Está diseñada para **compilar, correr y ser escaneable** por
herramientas de seguridad (SAST, DAST, SCA, secret scanning, container scanning)
y para servir de insumo a un análisis **STRIDE** y a **DefectDojo**.

- Almacenamiento **en memoria** (sin base de datos).
- **Sin autenticación real** (decisión de MVP).
- Validación de entradas con **Pydantic**.

## Estructura

```
app/
  __init__.py
  main.py          # FastAPI app + endpoints
  models.py        # Modelos Pydantic (validación)
  storage.py       # Almacenamiento en memoria
tests/
  __init__.py
  test_main.py     # Tests con pytest + TestClient
Dockerfile
docker-compose.yml
requirements.txt
README.md
```

## Endpoints

| Método | Ruta            | Descripción                                              |
|--------|-----------------|----------------------------------------------------------|
| GET    | `/`             | Info del servicio y enlaces (`/health`, `/docs`).        |
| GET    | `/health`       | Healthcheck. Devuelve `{"status":"ok"}`.                 |
| GET    | `/items`        | Lista los items en memoria.                              |
| POST   | `/items`        | Crea un item. Valida `name` y `price` con Pydantic.      |
| GET    | `/admin/status` | Estado administrativo. **Vulnerabilidad simulada** (ver abajo). |

Documentación interactiva (Swagger UI): `http://localhost:8000/docs`
Esquema OpenAPI (insumo para DAST/OWASP ZAP): `http://localhost:8000/openapi.json`

## ⚠️ Vulnerabilidad simulada y controlada (intencional)

El endpoint **`GET /admin/status` no tiene autenticación ni autorización a
propósito**. Es un hallazgo **deliberado y controlado** con fines académicos
para generar evidencia en los escaneos y en el análisis STRIDE:

- **OWASP A01:2021 – Broken Access Control.**
- **STRIDE:** *Information Disclosure* y *Elevation of Privilege*.

Expone información sensible simulada (uptime, conteo, flag `debug=true`).
**No usar este patrón en producción.** En una fase posterior del proyecto se
puede remediar agregando autenticación/autorización y documentar el antes/después.

## Ejecución local

> **Requisito de versión de Python:** usa **Python 3.11 o 3.12**. En Python 3.14
> las dependencias fijadas no tienen *wheels* precompilados y `pip` intentaría
> compilar `pydantic-core` desde Rust (falla sin las MSVC Build Tools). El
> contenedor Docker ya usa `python:3.12-slim`, así que esto solo aplica al venv
> local. Si tienes el *py launcher*, fuerza la versión: `py -3.11 -m venv venv`.

### 1. Instalar dependencias

**Git Bash:**
```bash
py -3.11 -m venv venv     # o: python -m venv venv  (si python ya es 3.11/3.12)
source venv/Scripts/activate
pip install -r requirements.txt
```

**PowerShell (Windows):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Correr tests

```bash
pytest -v
```

### 3. Levantar la app

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Luego abre `http://localhost:8000/docs`.

Prueba rápida del healthcheck:
```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### 4. Docker

Construir y correr la imagen:
```bash
docker build -t devsecops-api .
docker run -p 8000:8000 devsecops-api
```

O con Docker Compose:
```bash
docker compose up --build
```

## Notas para el pipeline DevSecOps

- **SCA:** dependencias con versiones fijadas en `requirements.txt`.
- **Container scanning:** imagen `python:3.12-slim`, usuario no-root, `.dockerignore`.
- **DAST:** OpenAPI en `/openapi.json` para alimentar OWASP ZAP / similar.
- **SAST / revisión manual:** `/admin/status` como hallazgo de control de acceso.
- **HEALTHCHECK** definido en el `Dockerfile` con `urllib` (Python puro, sin `curl`).
