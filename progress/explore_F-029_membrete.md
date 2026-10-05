# Exploración F-029 · qué escribe sv2 en `cabecera.empresa_membrete`

Fecha: 2026-10-05. Solo lecturas. No se ha publicado en colas ni escrito en
la base `partes`, en Blob ni en SharePoint. Sin datos de trabajadores.

## Cómo se ejecutó

- Pipeline real de sv2: `build_app(Settings()).state.pipeline.run(...)`,
  igual que `main_worker.py`, desde un script del scratchpad con
  `PYTHONPATH=.` en `services/partes-api`. No se ha cambiado código de sv2.
- El `.venv` de la raíz no trae ni `google-genai` ni `anthropic`. Como en
  `progress/evals_F-023.md`, se creó un venv temporal en el scratchpad
  instalando `infra/manifests/sv2/requirements.txt` (google-genai 2.28.0) y
  se borró al terminar.
- `GEMINI_API_KEY` se leyó del Key Vault (`GEMINI-API-KEY`) a una variable
  de entorno del proceso y se borró al terminar. Además, solo para ese
  proceso: `GEMINI_MODEL=gemini-3.7-flash` y
  `GEMINI_MEDIA_RESOLUTION=default`, que es lo que hay en producción
  (`meta.model=gemini-3.7-flash` en los cuatro). El resto viene del `.env`
  local, incluido el catálogo auxhor de sigrid-api (solo lectura).
- La normalización se hizo con `text_match.normalize` de sv3. Para casar
  se usa la regla de `empresa_membrete.py`:
  `f" {alias} " in f" {normalizado} "`.

## Resultados

| PDF | `empresa_membrete` (repr) | normalize (sv3) | obra | plantilla |
|---|---|---|---|---|
| 0678 - Ruesma.pdf | `'ruesma'` | `'ruesma'` | `'678'` | rev. 0 (sin DNI) |
| 0678 - Porsan.pdf | `'PORSAN E HIJOS CONSTRUCCIONES, S.L.'` | `'porsan e hijos construcciones s l'` | `'0678'` | rev. 0 (sin DNI) |
| 0694 - Ruesma.pdf | `'ruesma'` | `'ruesma'` | `'0694'` | rev. 0 (sin DNI) |
| 0694 - Porsan.pdf | `'PORSAN E HIJOS CONSTRUCCIONES, S.L.'` | `'porsan e hijos construcciones s l'` | `'694'` | rev. 0 (sin DNI) |

La plantilla se comprobó mirando la página 1: no hay columna DNI, que es lo
que distingue la rev. 0. Las columnas son Nº, Categoría, Nombre y Horas
Ord./Extraord. sv2 devolvió `dni=None` en todas las líneas.

## Casa con los alias actuales (RUESMA → 1, PORSAN → 28)

- **Ruesma: sí casa con la empresa 1.** En el PDF el logotipo está impreso
  como «ru≡sma», con una E de tres barras. Aun así, Gemini 3.7 flash lo
  transcribió como `'ruesma'` en los dos partes, sin caracteres raros.
- **Porsan: sí casa con la empresa 28.** El membrete trae la razón social
  completa y `porsan` aparece en ella como palabra completa.

## Lo que afecta a F-029

- `normalize` cambia por espacio tanto «Ξ» como «≡»: `'RUΞSMA'`,
  `'RU≡SMA'`, `'ruΞsma'` y `'ru≡sma'` quedan en `'ru sma'`. Por eso el alias
  `RUΞSMA` que ya está en `config/empresas_membrete.yaml` de la rama
  (commit f1961c4) cubre también la variante con «≡». En esta muestra no
  hizo falta: el modelo devolvió `ruesma`. Es una red de seguridad para
  otras lecturas, no la solución de lo observado aquí.
- Con 4 PDFs y un solo modelo, la muestra es pequeña. No se ha visto que la
  IA escriba la variante con Ξ/≡, pero tampoco queda descartado: el
  logotipo la invita a hacerlo.

## Observación al margen (fuera de F-029)

Los PDFs tienen varias páginas escaneadas: 6, 6, 5 y 4. Solo se ha mirado
la página 1 de cada uno, así que no está comprobado si cada página es un
día distinto. Aun así, sv2 devuelve una sola cabecera por documento.
Habría que comprobar si el flujo previsto divide los documentos de varias
páginas antes de sv2.
