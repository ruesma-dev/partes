# F-072 · Verificaciones manuales T29–T31 (M0–M2)

Las ejecutó el implementer el 2026-11-24, a petición expresa del humano («haz tú las pruebas»).
Rama `feature/F-072-postventa-var-como-obras`, HEAD 06148a8. Resultado: **las tres en verde**,
sin fallos del código. Ningún secreto en este fichero: credenciales del Key Vault solo en memoria
del proceso; el `.env` de los servicios no se leyó ni se tocó.

## T29 (M0) · partes ya guardados en POSTV2/VAR (solo lectura, base `partes`)

Consulta de T29 tal cual (solo cambia la conexión `default_transaction_read_only=on`):

```
obra_codigo | leida | count
---
```

**0 filas.** Contexto, también solo lectura: 457 documentos activos (456 con obra leída y 456 con
obra casada); la lectura más repetida es `678` (67). Fuera del filtro `is_active` solo hay **4
documentos inactivos** con `obra_numero_leido = 'VAR-30'` y sin obra casada (pruebas antiguas).
Para DA1, DA2, DA9 y DA13: hoy no hay ningún parte activo en POSTV2/VAR ni con marca leída, así
que el encendido no deja líneas «sin entrada» heredadas (DA9) ni marcas por casar.

## T30 (M1) · universos contra porcentajes

sv4 local (`127.0.0.1:8014`) con `POSTVENTA_OBRA_COD=POSTV2 VAR_OBRA_COD=VAR VAR_PARTIDA_DESDE=29`
y el comando de T30 sobre `/api/sigrid/obras` (1014 elementos):

```
Counter({(None, 1): 782, (None, 28): 103, ('postventa', 1): 88, (None, 18): 8, (None, 11): 6,
 (None, 20): 3, (None, 39): 3, (None, 14): 2, (None, 12): 2, (None, 15): 2, (None, 25): 2,
 (None, 32): 2, ('var', 1): 2, (None, 8): 1, (None, 9): 1, (None, 26): 1, (None, 27): 1,
 (None, 29): 1, (None, 31): 1, (None, 34): 1, (None, 22): 1, ('var', 28): 1})
```

**Qué se comparó.** El preview de dedicación no se pudo leer: la lectura de la base `dedicacion`
de porcentajes (donde su sync guarda `admite_postventa` y `postventa_partida_ide` por obra) la
**denegó el control de permisos** de la sesión, y no se llamó a la API desplegada de porcentajes.
Se usó la vía de respaldo: el universo de porcentajes **recalculado con sus propias funciones**
(`resolver_postventa`, `construir_catalogo`, `partidas_hoja` y `es_partida_var` de
`porcentajes/services/dedicacion-transfer`, repo solo leído) sobre los datos de Sigrid leídos por
sigrid-api (solo lectura, `truncated` comprobado): las 927 obras (`obr` + `con`, sin filtro, como
`sync.obras` de porcentajes) y el presupuesto de las 4 obras agrupadas (POSTV2 y VAR en las
empresas 1 y 28), con el mismo SQL que `capitulos_de_obra` de porcentajes.

**Resultado.**
- **Postventa, por partida**: porcentajes casa **88 partidas** distintas (todas de la empresa 1;
  la POSTV2 de la empresa 28 tiene 8 hojas y no casa ninguna obra) y partes ofrece **88
  entradas**: los dos conjuntos `(empresa, partida_ide)` son **idénticos** (0 de porcentajes sin
  entrada en partes, 0 de partes sin obra en porcentajes).
- **Postventa, por código**: porcentajes rotula por la obra origen (91 `Postv-<obra>`) y partes
  por la partida (R24, `Postv-<partida_cod>`). La diferencia son 3 partidas que casan con dos obras
  cada una: 311285 `0578B` (obras 0578 y 0578-B), 399711 `0654-B` (0654 y 0654-B) y 421951
  `0676-B` (0676 y 0676-B). Es de rotulado, no de universo.
- **Seis dígitos**: las 4 obras de Sigrid que partes no lista como obra normal, además de las
  cuatro agrupadas, son `160310`, `160316`, `160319` y `161113` (6 dígitos); ninguna entra en el
  universo de porcentajes.
- **VAR**: idénticos. Porcentajes y partes dan `VAR-29` (417055) y `VAR-30` (422189) en la empresa
  1 y `VAR-30` (422196) en la empresa 28.

**Qué NO se comparó.** El preview real de porcentajes (su último sync guardado y la API
desplegada). Que el preview coincida con lo recalculado depende de que porcentajes despliegue el
mismo código que su repo local; eso lo vigila `tests/test_f072_equivalencia_porcentajes.py` solo
contra el repo. Si el humano quiere el cotejo con el preview real: la consulta de solo lectura
`SELECT ide, cod, empresa, postventa_partida_ide FROM obra WHERE admite_postventa` en la base
`dedicacion` (y las entradas con `registro_obra_ide`) frente a la tabla de arriba.

## T31 (M2) · portal y escritura en modo pruebas

**Montaje** (lanzadores en el scratchpad de la sesión; variables por proceso, pisan el `.env`):
- **sv5 local** `127.0.0.1:8005`: `OBRA_PRUEBAS_FORZAR=true`, `OBRA_PRUEBAS_COD=0404`,
  `MARCA_PRUEBAS=PRUEBA-IA`, las tres variables de obras agrupadas, `SIGRID_API_MAX_ROWS=500000`
  (el `.env` local traía 1000; Azure usa el defecto) y `COLAS_*`/`BLOBS_*` **vacías**. Log:
  `[transfer-cola] DESACTIVADO (faltan COLAS_*): sv5 atiende solo por HTTP`. `/health`:
  `{"ok":true,"modo_pruebas":true,"obra_pruebas":"0404","database":"ruesma"}`.
- **sv4 local** `127.0.0.1:8014`, base `partes`, `TRANSFER_BASE_URL=http://127.0.0.1:8005` y
  colas vacías. Log: `[transfer][wiring] CABLEADO base_url=http://127.0.0.1:8005` y
  `[transfer-cola][wiring] DESACTIVADO` (registro síncrono, nada a la cola de Azure).
- La rama no cambia el esquema de la base (sin diferencias en `infrastructure/database` que
  creen o alteren tablas).

**Partes de prueba creados** (alta manual `/api/partes/nuevo`, recurso 2717792, MO/0753, gruista,
HLGR+HEGR, empresa 1, mayo de 2026, con la 0404 sin parte mensual ese mes):

| Documento | Día | Entrada | Líneas (`parte_registros.id`) |
|---|---|---|---|
| `bbe7372e-097c-405b-8905-20038ccc860e` | 2026-05-12 | `VAR-29` (VAR 683806, partida 417055) | 25207 (8 h), 25208 (1 h extra) |
| `f1cd59f4-e51b-4a80-bb2a-045bdb8d1c19` | 2026-05-13 | `Postv-0342` (POSTV2 1659588, partida 303927) | 25209 (8 h), 25210 (1 h extra) |
| `0e722058-72c1-4886-b365-c3fe2b793fa9` | 2026-05-14 | POSTV2 **sin marca** | 25206 (2 h, partida `CI.1.10` por `auto_categoria`) |

El tercero se creó con sv4 arrancado con las variables **vacías** (el caso DA9: parte guardado
antes de encender), y sv4 se reinició encendido para el resto. De paso, R28: con todo encendido,
el alta en POSTV2 sin entrada da `HTTP 422: Es una obra agrupada (postventa o VAR): elige una de
sus entradas.`

**Preflight y aprobación** (`/api/aprobar/preflight` y `/api/aprobar/ejecutar`, los 5 ids):
tres grupos, `agr-1659588-303927`, `agr-683806-417055` y `obr-1659588`, todos con
`obra_destino` 0404 y `forzada_pruebas: true`. Ejecución: `ok: true, parcial: false`; parte
**PT26/00417** creado (`hmo` 2879051, 2026/05), 4 escritas (`hmores` 416375–416378) y 1 omitida:

```
{"registro_id":25206,"motivo":"partida_agrupada: sin entrada postventa: la linea no trae la marca de una entrada de la obra POSTV2"}
```

**Verificación en Sigrid.** `prueba_escritura_sigrid.py` tiene el periodo fijo (`ANO, MES = 2026,
8`, el mes reservado de PT26/00375): se ejecutó una **copia en el scratchpad** que solo cambia esa
línea a `2026, 5` (`diff --strip-trailing-cr`: una línea); el script del repo no se tocó.
`verificar`: `Parte PT26/00417 (ide=2879051)`, 4 líneas, 18 h, 528,00 €. Ese script no muestra
`paride` ni `tex`, así que se leyeron por sigrid-api (solo lectura):

| hmores | Día | Hora | can | `paride` | Partida (obra) | `tex` | `synckey` |
|---|---|---|---|---|---|---|---|
| 416375 | 13/05 | HLGR | 8 | 303927 | `0342` (POSTV2) | PRUEBA-IA | `partes:25209` |
| 416376 | 13/05 | HEGR | 1 | 303927 | `0342` (POSTV2) | PRUEBA-IA | `partes:25210` |
| 416377 | 12/05 | HLGR | 8 | 417055 | `29` (VAR) | PRUEBA-IA | `partes:25207` |
| 416378 | 12/05 | HEGR | 1 | 417055 | `29` (VAR) | PRUEBA-IA | `partes:25208` |

`obride` = 828942 (0404) en las cuatro; cabecera `Parte CUBIERTA NAVE 14 - JOHN DEERE (PRUEBA-IA)`.

**Limpieza en Sigrid.** `limpiar --ejecutar` (misma copia de mayo): 3 sentencias,
`affected_rows` 4 + 1 + 1 (líneas, `hmo` y `con`), `committed: true`; `verificar` después: `No
existe el parte del mes.`

**Limpieza en `partes`.** «Mover a la papelera» (`/documents/{id}/delete`): el del 14/05 entró a
la primera; los otros dos los paró la congelación de F-004 (`El parte tiene lineas ya registradas
en Sigrid…`), que es lo esperado. La comprobación de F-024 (`/api/sigrid/comprobar`, `forzar`)
marcó las 4 como `borrado_sigrid` (`borradas: 4`) y entonces entraron en la papelera. Estado final
(solo lectura): los tres documentos `is_active = false`, líneas en `borrado_sigrid` (4) y
`omitido` (1); la consulta de T29 vuelve a dar 0 filas.

**Estado final de la 0404 en Sigrid**: idéntico al de antes de la prueba (mismos 9 partes
mensuales, nada en 2026/05). Siguen las **7 líneas `PRUEBA-IA` anteriores** a esta sesión (2 en
PT26/00376 de 06, 1 en PT26/00375 de 08 y 4 en PT26/00373 de 10): no son de esta prueba y no se
tocaron, porque 08 está reservado y las otras no constan como limpiables.

## Observaciones para el humano

- `prueba_escritura_sigrid.py` tiene el mes fijo y su `ENV_PATH` apunta al `.env` del antiguo
  repo suelto `partes-transfer`; su `verificar` no enseña `paride`. Mejoras posibles (periodo por
  argumento, `paride` y `tex` en la salida), fuera del alcance de F-072.
- Servicios locales parados al terminar; logs y lanzadores solo en el scratchpad de la sesión.
