# Informe Técnico Final — Proyecto DevSecOps

**Título:** Diseño e implementación de un pipeline DevSecOps para una API FastAPI contenerizada, con integración de escaneo de seguridad y gestión centralizada de vulnerabilidades en DefectDojo.

**Autor:** [Estudiante]
**Asignatura:** [DevOps / DevSecOps]
**Fecha:** 2026-07-03
**Repositorio:** `P_DevSecOps`

---

## Tabla de contenido

1. Introducción
2. Objetivos
3. Arquitectura
4. Tecnologías
5. Pipeline DevSecOps
6. GitHub Actions
7. Docker
8. FastAPI
9. PostgreSQL (arquitectura objetivo)
10. Herramientas utilizadas
11. Gitleaks
12. Semgrep
13. Trivy Filesystem
14. Trivy Image
15. OWASP ZAP
16. DefectDojo
17. STRIDE
18. Hallazgos
19. Mitigaciones
20. Evidencias
21. Resultados
22. Conclusiones
23. Trabajo futuro
24. Referencias (APA 7)

---

## 1. Introducción

El presente informe documenta el diseño, la implementación y la evaluación de un
*pipeline* de integración y entrega continua con seguridad integrada (DevSecOps)
sobre una API REST desarrollada con **FastAPI** y empaquetada en un contenedor
**Docker**. El proyecto adopta el principio *shift-left security*, es decir, la
incorporación de controles de seguridad de forma temprana y automatizada dentro
del ciclo de vida de desarrollo del software (SDLC), en línea con el marco *Secure
Software Development Framework* del NIST (NIST, 2022).

El objetivo central del trabajo no es la complejidad funcional de la aplicación,
sino demostrar una **cadena completa de controles de seguridad automatizados**:
análisis de secretos, análisis estático de código (SAST), análisis de composición
de software (SCA), escaneo de contenedores, análisis dinámico (DAST) y la
**centralización de la evidencia** en una plataforma de gestión de vulnerabilidades
(DefectDojo). Para mantener el foco en la automatización de seguridad y la
estabilidad del pipeline, la aplicación utiliza **almacenamiento en memoria** en
lugar de una base de datos persistente (véanse las secciones 3 y 9).

## 2. Objetivos

**Objetivo general.** Implementar un pipeline DevSecOps funcional, reproducible y
auditable que integre controles de seguridad automatizados sobre una API
contenerizada y centralice sus hallazgos para su análisis.

**Objetivos específicos.**

- Desarrollar una API mínima con FastAPI que exponga endpoints escaneables.
- Contenerizar la aplicación siguiendo buenas prácticas de seguridad de imágenes.
- Construir un workflow de GitHub Actions con etapas de validación, construcción,
  escaneo de seguridad y pruebas.
- Integrar herramientas de secret scanning (Gitleaks), SAST (Semgrep), SCA y
  container scanning (Trivy) y DAST (OWASP ZAP).
- Generar reportes en formatos interoperables e importarlos a DefectDojo.
- Elaborar un modelo de amenazas STRIDE de la arquitectura real.
- Ejecutar un ciclo de mitigación (detección → corrección → reducción de hallazgos).

## 3. Arquitectura

La arquitectura real implementada en el MVP se compone de los siguientes elementos
y fronteras de confianza (*trust boundaries*):

- **Cliente HTTP (no confiable).** Consume la API por HTTP. Representa tanto a un
  usuario legítimo como a un potencial atacante.
- **Plano de GitHub (SCM + CI/CD).** El repositorio aloja el código y el workflow;
  GitHub Actions ejecuta el pipeline en *runners* efímeros `ubuntu-latest`.
- **Runtime del contenedor (Docker host).** Ejecuta el proceso FastAPI servido por
  Uvicorn. La persistencia es **en memoria** (una estructura de datos del proceso
  en `app/storage.py`); no existe base de datos.
- **Gestión de vulnerabilidades (DefectDojo).** Recibe e integra los reportes de
  los escáneres para su triage y seguimiento.

> **Nota de arquitectura (coherencia).** El MVP **no** implementa PostgreSQL. El
> almacenamiento es en memoria y volátil (se reinicia con cada arranque del
> proceso). PostgreSQL se contempla únicamente como **arquitectura objetivo para
> producción** (véase la sección 9 y el apartado 23, Trabajo futuro). Esta
> decisión es deliberada: el objetivo prioritario del proyecto fue implementar un
> pipeline DevSecOps completo y funcional, priorizando la automatización de los
> controles de seguridad sobre la persistencia de datos, y evitando introducir
> componentes que pusieran en riesgo la estabilidad del pipeline antes de la
> entrega.

El diagrama de modelado de amenazas correspondiente se entrega en
[`docs/stride.drawio`](stride.drawio) (editable en draw.io / diagrams.net).

## 4. Tecnologías

| Capa | Tecnología | Rol |
|---|---|---|
| Lenguaje | Python 3.12 | Runtime de la aplicación |
| Framework | FastAPI + Pydantic | API REST y validación de entradas |
| Servidor ASGI | Uvicorn | Servir la aplicación |
| Contenerización | Docker | Empaquetado e imagen reproducible |
| Orquestación local | Docker Compose | Ejecución del servicio |
| CI/CD | GitHub Actions | Automatización del pipeline |
| Pruebas | pytest | Pruebas unitarias/funcionales |
| Secret scanning | Gitleaks | Detección de secretos |
| SAST | Semgrep | Análisis estático de código |
| SCA + Container | Trivy | Vulnerabilidades de dependencias e imagen |
| DAST | OWASP ZAP (Baseline) | Análisis dinámico de la app en ejecución |
| Gestión de hallazgos | DefectDojo | Centralización y triage de vulnerabilidades |

## 5. Pipeline DevSecOps

El pipeline se define en un único workflow declarativo,
[`.github/workflows/devsecops-pipeline.yml`](../.github/workflows/devsecops-pipeline.yml),
disparado por eventos `push` y `pull_request` sobre la rama `main`. El **orden
lógico** de las etapas —ajustado según la revisión docente— sitúa las pruebas
**después** de la validación de seguridad:

1. **Validate** — Compila e importa el código (falla rápido ante errores básicos).
2. **Build image** — Construye `devsecops-api:latest` y la exporta como artifact.
3. **Secret Scan (Gitleaks)** — Búsqueda de secretos.
4. **SCA Scan (Trivy FS)** — Vulnerabilidades en dependencias y sistema de archivos.
5. **SAST Scan (Semgrep)** — Análisis estático (reglas `p/ci` y `p/python`).
6. **Container Scan (Trivy Image)** — Vulnerabilidades de la imagen construida.
7. **DAST Scan (OWASP ZAP)** — Escaneo dinámico contra la app en ejecución.
8. **Test (pytest)** — Pruebas unitarias/funcionales, tras validar la seguridad.
9. **Security Summary** — Consolida todos los reportes y genera un resumen.

**Estrategia de tolerancia a fallos.** Las etapas de seguridad (3–7) se declaran
con `continue-on-error: true` para **recolectar evidencia aunque existan
hallazgos**, sin marcar en rojo el pipeline por vulnerabilidades. El *gate* real
sigue siendo `pytest`: una prueba fallida sí detiene la entrega.

**Reportes y evidencia.** Cada job escribe su salida en `reports/` y la publica
como *artifact*. La etapa `Security Summary` descarga todos los artifacts, los
consolida y produce `reports/security-summary.md`, que además se inyecta en la
página de resumen del run (`$GITHUB_STEP_SUMMARY`).

## 6. GitHub Actions

El workflow aplica varias **buenas prácticas** de CI/CD y seguridad de la cadena
de suministro:

- **Mínimo privilegio.** `permissions: contents: read` a nivel global; el pipeline
  no requiere permisos de escritura.
- **Concurrencia.** `concurrency` con `cancel-in-progress` evita ejecuciones
  solapadas sobre la misma referencia y ahorra minutos de *runner*.
- **Grafo de dependencias explícito** mediante `needs`, con paralelización de los
  escáneres que solo dependen de `validate` o `build`.
- **Aislamiento de la imagen entre jobs.** La imagen se comparte vía `docker
  save`/`docker load` sobre un artifact (`image.tar`), garantizando que el
  *container scan* y el *DAST* usen exactamente la misma imagen construida.
- **Caché de dependencias.** `actions/setup-python` con `cache: pip` reduce el
  tiempo de instalación en `validate` y `test`.
- **Límites de ejecución.** `timeout-minutes` por job para evitar *runners*
  colgados.
- **Versionado de acciones.** Se referencian versiones fijas de las acciones
  (`checkout@v4`, `setup-python@v5`, `upload-artifact@v4`, `trivy-action@v0.36.0`,
  `zaproxy:stable`), lo que mejora la reproducibilidad.

## 7. Docker

La imagen se construye desde `python:3.12-slim` y aplica prácticas de
*container security* alineadas con NIST SP 800-190 (Souppaya, Morello & Scarfone,
2017):

- **Actualización del SO base** (`apt-get upgrade`) para reducir CVEs del sistema
  operativo detectados por Trivy.
- **Usuario no-root** (`appuser`, UID 10001) para reducir el impacto de una
  eventual explotación.
- **Cacheo de capas** instalando dependencias antes de copiar el código.
- **HEALTHCHECK** implementado con `urllib` (Python puro) para no depender de
  `curl`, ausente en la imagen *slim*.
- **`.dockerignore`** para reducir el contexto de build y la superficie de la
  imagen.

El servicio se orquesta con `docker-compose.yml` (build local, puerto 8000,
`restart: unless-stopped`).

## 8. FastAPI

La API expone cinco endpoints:

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Información y enlaces (`/health`, `/docs`). |
| GET | `/health` | Healthcheck para Docker y el pipeline. |
| GET | `/items` | Lista los ítems almacenados en memoria. |
| POST | `/items` | Crea un ítem; valida `name` y `price` con Pydantic. |
| GET | `/admin/status` | Estado administrativo **sin autenticación** (hallazgo intencional). |

**Validación de entradas.** El modelo `ItemCreate` (Pydantic) exige `name` no
vacío (1–100 caracteres) y `price > 0`, mitigando *Tampering* de entradas y
devolviendo `422` ante datos inválidos.

**Cabeceras de seguridad.** Se incorporó un *middleware* que añade `X-Content-Type-Options`,
`X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` y `Content-Security-Policy`
a todas las respuestas, mitigando hallazgos típicos de DAST (véase sección 19).

**Hallazgo intencional.** El endpoint `/admin/status` se mantiene deliberadamente
sin autenticación como caso de estudio de *Broken Access Control* (OWASP A01;
CWE-284). Es un hallazgo académico controlado, documentado en el código y en el
resumen de seguridad, y **no** debe replicarse en producción.

## 9. PostgreSQL (arquitectura objetivo)

El MVP **no** implementa PostgreSQL; el almacenamiento es en memoria. No obstante,
PostgreSQL se documenta como el **motor de persistencia objetivo** para una
evolución a producción, por su robustez, soporte transaccional ACID y su amplio
ecosistema (PostgreSQL Global Development Group, 2024).

**Justificación técnica.** El objetivo principal del proyecto fue implementar un
pipeline DevSecOps completo y funcional. Se priorizó deliberadamente la
automatización de los controles de seguridad sobre la persistencia de datos, ya
que introducir una base de datos habría añadido complejidad operativa (migraciones,
gestión de credenciales, disponibilidad del servicio en CI) sin aportar valor al
objetivo evaluado, y con riesgo para la estabilidad del pipeline. La migración a
PostgreSQL se detalla como trabajo futuro (sección 23).

## 10. Herramientas utilizadas

Las herramientas se seleccionaron por ser estándar de la industria, de código
abierto y con formatos de reporte interoperables con DefectDojo. Las secciones
11–16 detallan cada una.

## 11. Gitleaks

**Categoría:** Secret scanning. **Propósito:** detectar credenciales, tokens y
claves filtradas en el código y su historial. En el pipeline se ejecuta sobre el
árbol del repositorio y emite `reports/gitleaks-report.json`. Aporta cobertura
frente a *Information Disclosure* por secretos versionados (Gitleaks, 2024).

## 12. Semgrep

**Categoría:** SAST. **Propósito:** análisis estático basado en reglas para
detectar patrones inseguros en el código fuente. Se ejecuta con los conjuntos de
reglas `p/ci` y `p/python` y produce salida en **SARIF** y **JSON**
(`reports/semgrep-report.sarif` / `.json`), facilitando tanto la interoperabilidad
como la importación a DefectDojo (Semgrep, 2024).

## 13. Trivy Filesystem

**Categoría:** SCA. **Propósito:** identificar vulnerabilidades conocidas (CVE) en
dependencias y en el sistema de archivos del proyecto. Emite
`reports/trivy-fs-report.json`. Cubre riesgos de la cadena de suministro de
software (Aqua Security, 2024).

## 14. Trivy Image

**Categoría:** Container scanning. **Propósito:** analizar la imagen Docker
construida en busca de CVEs en paquetes del sistema operativo base y en las
bibliotecas. Emite `reports/trivy-image-report.json`. Es la fuente principal de
hallazgos por volumen, al inspeccionar el SO base (Aqua Security, 2024; Souppaya
et al., 2017).

## 15. OWASP ZAP

**Categoría:** DAST. **Propósito:** analizar la aplicación **en ejecución**
mediante *OWASP ZAP Baseline*, detectando problemas observables desde el exterior
(cabeceras de seguridad, exposición de información, etc.). El pipeline levanta el
contenedor, espera el `/health` y ejecuta ZAP con `--network host`, generando
reportes HTML, JSON y XML (`reports/zap-report.*`). El fichero `.zap/rules.tsv`
estabiliza la ejecución degradando a `WARN` alertas no bloqueantes (OWASP
Foundation, 2024).

## 16. DefectDojo

**Categoría:** Gestión de vulnerabilidades. **Propósito:** centralizar, deduplicar
y priorizar los hallazgos de todas las herramientas. El flujo de importación
manual se organiza como *Product Type → Product → Engagement → Import Scan
Results*, seleccionando el *scan type* adecuado por herramienta (Gitleaks Scan,
Semgrep JSON Report, Trivy Scan y ZAP Scan). El reporte ZAP se importa a partir de
su salida **XML** (formato nativo del *parser*), ahora generada por el pipeline
(DefectDojo, 2024).

## 17. STRIDE

Se elaboró un modelo de amenazas **STRIDE** (Spoofing, Tampering, Repudiation,
Information Disclosure, Denial of Service, Elevation of Privilege) sobre la
arquitectura real (Microsoft, 2009; Shostack, 2014). El diagrama, entregado en
`docs/stride.drawio`, incluye las cuatro fronteras de confianza, los flujos de
datos y las amenazas etiquetadas por categoría. Amenazas principales:

| # | Elemento / flujo | STRIDE | Mitigación | Estado |
|---|---|---|---|---|
| 1 | `/admin/status` sin auth | I, E | Autenticación/autorización | Intencional (académico) |
| 2 | Cliente → FastAPI | S, T, I, D | Validación Pydantic + cabeceras de seguridad; auth + rate-limit | Parcial (implementado T/I) |
| 3 | FastAPI → Memoria | T, R, I | Logging/auditoría; persistencia | Objetivo |
| 4 | Desarrollador → Repositorio | S, T, R | Commits firmados, branch protection | Objetivo |
| 5 | Imagen Docker | T, I | Usuario no-root + `apt upgrade` + Trivy | Implementado |
| 6 | Reportes → DefectDojo | T, I | Artifacts con retención, importación controlada | Implementado |

## 18. Hallazgos

Resultados de la **primera ejecución** (antes de mitigaciones):

| Herramienta | Tipo | Hallazgos |
|---|---|---|
| Gitleaks | Secret | 0 |
| Semgrep | SAST | 0 |
| Trivy Filesystem | SCA | 1 |
| Trivy Image | Container | 125 |
| OWASP ZAP | DAST | 3 |

**Interpretación.** La ausencia de hallazgos en Gitleaks y Semgrep es coherente
con una base de código pequeña, sin secretos y sin patrones inseguros evidentes.
El grueso de hallazgos (125) proviene de **CVEs del SO base** de la imagen —
comportamiento normal en imágenes que no actualizan sus paquetes—. Los 3 hallazgos
de ZAP corresponden a **cabeceras de seguridad ausentes**. El *Broken Access
Control* de `/admin/status` se documenta como hallazgo manual intencional.

## 19. Mitigaciones

Se aplicaron mitigaciones de bajo riesgo y alto valor para habilitar el flujo
*detección → corrección → reducción*:

**M1 — Cabeceras de seguridad (DAST).** *Middleware* en FastAPI que añade
`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy`
(con `frame-ancestors 'none'`), `Referrer-Policy` y `Permissions-Policy`.
*Impacto esperado:* desaparición de los hallazgos ZAP de *anti-clickjacking*,
*X-Content-Type-Options* y *CSP* (≈3 → 0–1). *Findings que deberían desaparecer en
DefectDojo:* «Missing Anti-clickjacking Header», «X-Content-Type-Options Header
Missing», «CSP Header Not Set».

**M2 — Actualización del SO base (Container).** `apt-get upgrade` en el Dockerfile.
*Impacto esperado:* reducción del número de CVEs del SO en Trivy Image (de 125
hacia un valor menor, según parches disponibles en el índice base). *Findings que
deberían reducirse en DefectDojo:* CVEs de paquetes del sistema con versión
corregida disponible.

**No mitigado (intencional).** `/admin/status` se mantiene sin autenticación como
evidencia académica del control *Broken Access Control*.

Cada mitigación quedó cubierta por pruebas (`test_security_headers`) para evitar
regresiones.

## 20. Evidencias

Evidencias recomendadas para la entrega:

- **Pipeline:** captura de la pestaña *Actions* con los 9 jobs y el nuevo orden
  (Test tras los escáneres); log de `Test` con «11 passed».
- **Artifacts:** descarga de `devsecops-reports` y de los reportes individuales.
- **Resumen:** `security-summary.md` renderizado en la página del run.
- **DefectDojo:** *Product* creado; *Engagement* con los tests importados; vista de
  *All Findings* con el conteo total y el *dashboard* de severidades.
- **Segunda ejecución:** comparación del conteo de ZAP y Trivy Image antes/después
  de M1 y M2.

## 21. Resultados

- Pipeline DevSecOps **funcional y reproducible**, con nueve etapas y cobertura de
  las cinco familias de escaneo (secret, SAST, SCA, container, DAST) más pruebas.
- **11/11 pruebas** en verde tras las mitigaciones.
- Evidencia consolidada e **importable a DefectDojo**, incluida la salida ZAP en
  formato XML nativo.
- Modelo de amenazas STRIDE **coherente con la arquitectura real** (sin base de
  datos), con amenazas y mitigaciones mapeadas.
- Ciclo de mitigación preparado para demostrar **reducción de hallazgos** en una
  segunda ejecución.

## 22. Conclusiones

El proyecto demuestra que es posible integrar controles de seguridad automatizados
de extremo a extremo en un pipeline de CI/CD manteniendo la simplicidad de la
aplicación. La aproximación *shift-left* permite detectar problemas de forma
temprana y objetiva, mientras que la centralización en DefectDojo transforma
salidas heterogéneas en una vista única y accionable. La separación entre
*hallazgos informativos* (seguridad, con `continue-on-error`) y el *gate* de
pruebas equilibra visibilidad y control de calidad. Finalmente, el ejercicio de
mitigación evidencia el valor del ciclo iterativo de seguridad: medir, corregir y
volver a medir.

## 23. Trabajo futuro

- **Persistencia con PostgreSQL** (SQLAlchemy/psycopg), con gestión de credenciales
  mediante *secrets* y migraciones.
- **Autenticación y autorización** (OAuth2/JWT) y remediación de `/admin/status`.
- **Rate limiting** y *hardening* adicional de cabeceras.
- **Fijación de imágenes por digest** y **firma de artefactos** (supply chain).
- **Integración automática con DefectDojo** vía API desde el pipeline (fase
  posterior, no incluida en esta entrega).
- **Gate de severidad** configurable (por ejemplo, fallar ante CVEs *Critical*).

## 24. Referencias (APA 7)

Aqua Security. (2024). *Trivy documentation*. https://trivy.dev/latest/docs/

DefectDojo. (2024). *DefectDojo documentation*. https://documentation.defectdojo.com/

Docker, Inc. (2024). *Docker documentation*. https://docs.docker.com/

GitHub. (2024). *GitHub Actions documentation*. GitHub Docs. https://docs.github.com/en/actions

Gitleaks. (2024). *Gitleaks: Protect and discover secrets*. https://github.com/gitleaks/gitleaks

Microsoft. (2009). *The STRIDE threat model*. Microsoft Learn. https://learn.microsoft.com/en-us/previous-versions/commerce-server/ee823878(v=cs.20)

MITRE. (2024). *CWE — Common Weakness Enumeration*. https://cwe.mitre.org/

MITRE. (2024). *CVE — Common Vulnerabilities and Exposures*. https://www.cve.org/

National Institute of Standards and Technology. (2022). *Secure Software Development Framework (SSDF) version 1.1: Recommendations for mitigating the risk of software vulnerabilities* (NIST Special Publication 800-218). https://doi.org/10.6028/NIST.SP.800-218

OWASP Foundation. (2021). *OWASP Top 10:2021*. https://owasp.org/Top10/

OWASP Foundation. (2024). *OWASP ZAP documentation*. https://www.zaproxy.org/docs/

PostgreSQL Global Development Group. (2024). *PostgreSQL documentation*. https://www.postgresql.org/docs/

Ramírez, S. (2024). *FastAPI documentation*. https://fastapi.tiangolo.com/

Semgrep, Inc. (2024). *Semgrep documentation*. https://semgrep.dev/docs/

Shostack, A. (2014). *Threat modeling: Designing for security*. Wiley.

Souppaya, M., Morello, J., & Scarfone, K. (2017). *Application container security guide* (NIST Special Publication 800-190). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-190
