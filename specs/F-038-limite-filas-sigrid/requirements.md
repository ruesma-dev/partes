<!-- specs/F-038-limite-filas-sigrid/requirements.md -->
# F-038 · Límite de filas de las lecturas de Sigrid a 200.000 y `truncated` siempre error — requisitos

> Pedida por el humano el 2026-10-07 (viene de `porcentajes`; petición literal en
> `harness/features.json`). Toca **sv2, sv3, sv4 y sv5** (los cuatro leen Sigrid por
> `sigrid-api`); sv1 no lee Sigrid. Inventario, diseño y DA1–DA7 en `design.md`.

> **Aprobación del humano (2026-10-24, literal)**: «sigrid lee 500k, hay que cambiar donde este ese limite de 100 ya mismo. se supone que estaba arreglado» y, a la propuesta del líder (tope 500.000, resto A, en paralelo con F-060), «si». ⇒ **DA1 = B: 500.000** (donde esta spec dice 200.000 como valor por defecto, léase 500.000; el rango de DA2 sigue 1–500.000); DA2–DA7 = A (DA6: se borra `consulta_reshor_recursos.py`; la purga del historial es aparte y no está decidida). Excepción expresa a «una feature en curso»: F-060 sigue en mutación y review.

## Qué hay hoy (resumen; inventario completo en `design.md` §1)

- `sigrid-api` desplegada admite hasta **500.000 filas** por petición
  (`MAX_ALLOWED_ROWS`) y `timeout_seconds` hasta **230 s**, que es también el corte
  del balanceador (`azure-apps/sigrid_api.md` §3.4 y §4.1).
- **Partidas por obra**: en partes NO se truncan hoy. sv3 y sv4 las leen
  **paginadas** (páginas de 5.000 con `max_rows` 5.001, `truncated` = error); sv5
  no lee partidas por obra, solo las de sus líneas, por `ide`.
- **Truncan EN SILENCIO** (no miran `truncated`): sv2 `fetch_tipos_hora` (catálogo
  `auxhor` para la IA) y dos scripts manuales, `consulta_reshor_recursos.py` (sv4)
  y `prueba_escritura_sigrid.py` (sv5). En la práctica sus lecturas son pequeñas,
  pero nada lo garantiza.
- **Fallan con error (no en silencio) por el tope**: las lecturas sin paginar de
  sv5 piden `max_rows` 1.000 fijo; `lineas_existentes`, `horas_de_recursos` y
  `recursos_por_dni` no van en lotes y un parte grande puede pasar de 1.000 filas
  ⇒ el registro en Sigrid falla. sv4 (`fetch_dnis_sin_extra`,
  `fetch_hora_extra_recurso`) pide 10.000 fijo.
- `SIGRID_API_MAX_ROWS` existe solo en sv3 (10.000) y no lo usa ninguna lectura:
  todas las de sv3 van paginadas.

## Glosario

- **Lectura paginada**: `ORDER BY` por clave única + `OFFSET ? ROWS FETCH NEXT ?
  ROWS ONLY`, páginas de `PAGINA_FILAS` (5.000) pedidas con `max_rows` =
  `PAGINA_FILAS + 1` (`_leer_paginado` de sv3 y sv4).
- **Lectura no paginada**: cualquier otra petición a `POST /api/sql/read`.
- **Lector de Sigrid**: fichero `.py` de `services/` (fuera de `tests/`) con una
  cadena de código (no docstring) que contiene `/api/sql/read`.

## Requisitos

### Límite de filas configurable

R1. El sistema debe enviar en toda lectura no paginada de sv2, sv3, sv4 y sv5 un
`max_rows` igual al `SIGRID_API_MAX_ROWS` efectivo del servicio.

R2. MIENTRAS `SIGRID_API_MAX_ROWS` no esté definida, el sistema debe usar
**200.000** en los cuatro servicios (settings y valor por defecto del constructor
del cliente, que deben coincidir).

R3. SI `SIGRID_API_MAX_ROWS` es menor que 1, mayor que 500.000 o no es un entero,
ENTONCES el servicio debe negarse a arrancar (error de validación de settings).

R4. El sistema debe seguir pidiendo las lecturas paginadas de sv3 y sv4 con
`max_rows` = `PAGINA_FILAS + 1` (5.001), sea cual sea `SIGRID_API_MAX_ROWS`.

R5. CUANDO se construye el cliente de Sigrid de un servicio desde su cableado
(sv2 `app.py`; sv3 `app.py` y `medir_casado_recursos.py`; sv4 `app.py`; sv5
`app.py`, `main.py` y `comprobar_asiento_analitico.py`), el sistema debe pasarle
`settings.sigrid_api_max_rows`.

R6. CUANDO se instancia un cliente de Sigrid, el sistema debe registrar en INFO su
`max_rows` y su `timeout_s` efectivos, sin la clave de la función.

### `truncated` siempre es error

R7. SI una respuesta de `POST /api/sql/read` trae `truncated: true`, ENTONCES el
cliente de sv2 debe lanzar `RuntimeError` con «truncada» y la etiqueta de la
lectura, sin devolver filas.

R8. CUANDO la lectura del catálogo `auxhor` de sv2 falla por `truncated`, sv2 debe
comportarse como ante cualquier otro fallo de Sigrid: catálogo de la caché
anterior o vacío, con WARNING, y la extracción sigue (DA3).

R9. SI una respuesta trae `truncated: true`, ENTONCES los clientes de sv3, sv4 y
sv5 deben seguir lanzando excepción en todas sus lecturas, paginadas o no (hoy
ya lo hacen; se fija con tests en las lecturas no paginadas de sv4 y sv5).

R10. SI `prueba_escritura_sigrid.py` recibe `truncated: true`, ENTONCES debe
terminar con `SystemExit` y un mensaje con «truncada», sin escribir nada.

### Guardián de lectores

R11. El sistema debe tener un test que recorra `services/` y exija que el
conjunto de lectores de Sigrid sea exactamente la lista cerrada de `design.md` §6:
un lector nuevo rompe el test hasta que se añade a la lista conscientemente.

R12. El guardián debe exigir que cada lector compruebe `truncated` (una llamada
`.get("truncated")` en código, no en docstring).

R13. El guardián debe fallar si en un lector aparece un entero literal menor que
200.000 asociado a `max_rows` (clave `"max_rows"` de un dict, argumento
`max_rows=` o valor por defecto de un parámetro `max_rows`).

### Timeouts frente a los 230 s

R14. SI `SIGRID_API_TIMEOUT_S` es ≤ 0 o > 200, ENTONCES sv2, sv3, sv4 y sv5 deben
negarse a arrancar (DA4). Los valores por defecto no cambian (30, 30, 30 y 60).

R15. CUANDO sv5 lee con `SIGRID_API_TIMEOUT_S` = 200, el sistema debe usar como
plazo HTTP 230 s (`timeout + 30`, como hoy) y mandar `timeout_seconds` 200.

### Diagnóstico obsoleto y documentación

R16. DONDE el humano elija DA6 = A, el sistema no debe contener
`services/partes-front/consulta_reshor_recursos.py` ni su mención en
`docs/ARCHITECTURE.md`.

R17. El sistema debe documentar en `docs/ARCHITECTURE.md` («Acceso a datos») y en
`azure-apps/partes.md` (§3.3 y §5.6) el tope real de la instancia (500.000),
`SIGRID_API_MAX_ROWS` (opcional, 200.000) en sv2–sv5, el rango de
`SIGRID_API_TIMEOUT_S` y que `truncated` es siempre error. Lo verifica el reviewer.

## Fuera de alcance

- Trocear en lotes las lecturas de sv5 con `IN (...)` sin lote: el límite de
  ~2.100 parámetros de SQL Server es otro problema (DA7).
- Cambiar `PAGINA_FILAS` (DA5), la configuración de `sigrid-api` o sus límites.
- Purgar del historial de git los datos personales del script de DA6.
- Las lecturas nuevas de F-060 (`lineas_de_racha`): usan `_read` de sv5 y heredan
  el límite y el guardián sin cambios (ver `design.md` §8).

## Criterios de aceptación (de `harness/features.json`)

| Criterio | Requisitos |
|---|---|
| Ninguna lectura queda limitada por debajo de 200.000 salvo las paginadas | R1–R5, R13 |
| Toda lectura comprueba `truncated` y lo trata como error | R7–R12 |
| `bash harness/init.sh` en verde y APPROVED del reviewer | T12 de `tasks.md` |
