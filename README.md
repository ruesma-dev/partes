# partes — monorepo del pipeline de partes de trabajo

Monorepo creado el **2026-08-13** a partir de los repositorios de origen,
mediante **volcado limpio**: cada origen se importa en un commit propio que
cita repositorio, rama y HEAD de procedencia. Los repositorios de origen
quedan **archivados en solo lectura** (cada uno lleva un `ARCHIVADO.md`).

| Carpeta | Origen | Rol |
|---|---|---|
| `services/partes-email` | repo `partes-email` | sv1 · poller del buzón Graph → `q-extraccion` |
| `services/partes-api` | repo `partes-api` | sv2 · extracción IA (Gemini) del PDF |
| `services/partes-persistencia` | repo `partes-persistencia` | sv3 · conciliación Sigrid + PostgreSQL + SharePoint |
| `services/partes-front` | repo `partes-front` | sv4 · portal de revisión (Easy Auth) |
| `services/partes-transfer` | repo `partes-transfer` | sv5 · escritura en Sigrid |
| `infra/` | carpeta `partes-infra` (no estaba en git) | scripts de despliegue Azure + manifests |

En `infra/` los secretos están redactados: los valores reales van en
`infra/*.local.ps1` y `infra/graphkey_nobom.json`, sin versionar.

El documento maestro de integración (qué expone, qué consume, cómo se
despliega) está en `azure-apps/partes.md`.
