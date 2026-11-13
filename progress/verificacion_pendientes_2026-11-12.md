# Verificación de M pendientes con datos de producción — 2026-11-12

Investigación de **solo lectura**: Log Analytics (workspace del entorno, `ContainerAppConsoleLogs_CL`),
base `partes` (conexión con `default_transaction_read_only=on`, comprobado `read_only: on` en cada
script) y Sigrid por `sigrid-api /api/sql/read`, base `ruesma`, de la que solo salen `ide` y
cuentas. No se ha escrito nada en Azure, en la base ni en Sigrid. Los scripts están fuera del repo
(`scratchpad/cierre/`: `pg_lectura*.py`, `sigrid_lectura.py`). Las claves solo pasan por variables
de entorno.

## Resumen

| Feature | M | Veredicto | `pendiente` propuesto |
|---|---|---|---|
| F-047 | M2, M3 | **SUPERADA** (M1 sigue siendo del humano) | `M1 (portal, humano)` |
| F-055 | M3 | **AÚN NO VERIFICABLE** (las 15 siguen sin aprobar) + una anomalía aparte | `M3 cuando se aprueben las 15 líneas sin fecha (2026-11-12: aún sin aprobar; 0 en registrado/encolado/dedicacion)` |
| F-058 | M2 | **SUPERADA** | — |
| F-058 | M4 | **Medida; el cierre es del HUMANO** (DA12: tope de 5 s) | `DA12 (humano): decidir el tope OBRA_EXISTE_TIMEOUT_S con la M4 del 2026-11-12 (p50 105 ms, 10 % en 3,6–4,5 s, 3 ReadTimeout de 200)` |
| F-063 | M2, M4 | M2 **SUPERADA**; M4 **NO SUPERADA** frente a la puerta DA3 (máx. ≤ 2 s) | `M4 no cumple DA3 en producción (23 de 200 consultas ≥ 2 s, 3 ReadTimeout a 5 s): decidir (humano) si se abre la feature de reutilizar la conexión (opción B de DA3)` |
| F-060 | M4 | **SUPERADA** (grupos = 0 con rachas reales); `fin_movido` sin casos, explicado | vacío (o, si se quiere ver un `fin_movido` real: `M4: fin_movido aún 0, ninguna racha aprobada día a día`) |
| F-062 | M6 | **SUPERADA** (n = 2 > 0, grupos = 0) | `Vista calendario de Administración` |
| F-038 | M1 | **SUPERADA** | vacío |
| F-048 | M4 | Datos **SUPERADOS**; falta la mirada en el portal (**DEL HUMANO**) | `M4: mirar en el portal la etiqueta «incl. X h extra leídas» (datos OK 2026-11-12, p. ej. documento 2dc2ea16)` |
| F-053 | M4 | **DEL HUMANO** (texto del candado en el portal) | `M4 (humano, portal: candado de una línea registrado con el texto de DA8)` |
| F-046 | M6 | **DEL HUMANO** (escritura en producción con «Aplicar») | `M6 (humano: «Aplicar» en el portal; reparto_pendiente tiene 1 fila pendiente desde el 2026-10-19)` |

---

## F-047 · M2 y M3 — SUPERADA

Criterio (`tasks.md` T13): M2, en la base, `id = recalculo_pedido_id = recalculo_terminado_id`
para un parte nuevo; M3, en sv3, `[parte-repo] guardado` y `parte nuevo repartido … marcado=True`
del mismo `document_id`, y la diferencia mide la espera (antes 22–39 s).

**M2** — `parte_documents` creados desde el despliegue de sv3 (2026-10-31T08:40:44Z): **150**.
- 143 con los tres iguales.
- 6 con `recalculo_pedido_id = recalculo_terminado_id ≠ id`: recálculos pedidos después desde el
  portal (uuid4 de F-042/F-043; uno de ellos, `5ea328f7`, por `deshacer_cambio_fecha` el
  2026-11-12). Coherente: el pedido y el terminado coinciden.
- 1 con pedido nulo (`faefcba6`): parte **manual** (`source_filename = (manual)`), inactivo, borrado
  «sin-lineas» desde el portal. No pasa por la ingesta de sv3: no aplica.
- **0** partes con un pedido sin terminar (ninguno atascado en espera).

**M3** — KQL en `ca-sv3-persistencia` desde 2026-10-31T08:40Z, cruzando por `document_id` el
primer `[parte-repo] guardado` con el primer `parte nuevo repartido`:
`docs=149, con_reparto=149, marcado=True 149, marcado=False 0`; espera **mín 41 s, p50 54 s,
p95 69 s, máx 87 s** (del 2026-11-03 al 2026-11-12).

**Ojo con la cifra**: la espera real es más larga que los 22–39 s medidos el 2026-10-14 (p50 54 s).
No rompe nada (DA13 = A: R19 no cierra cifra y el portal la cubre con «procesando…»), pero si algún
texto de `docs/` o del portal cita «20–40 s», está desfasado.

## F-055 · M3 — AÚN NO VERIFICABLE

Criterio (`design.md` §9): la consulta de M1 unos días después ⇒ ninguna línea sin fecha válida en
`registrado`, `encolado` o `dedicacion`; las que se aprueben salen `omitido` con `fecha_no_valida`.

Consulta de M1 (con `hoy + 62` = 20270113): `sin_fecha / '' = 20`, `sin_fecha / omitido = 2`;
ninguna `anterior`/`posterior`; **0** en `registrado`, `encolado` o `dedicacion`. Líneas con motivo
`fecha_no_valida` en toda la base: **0**.

- Las **15 de la M1** (2 documentos del 2026-10-14, sin fecha de cabecera) siguen **sin aprobar**
  (documento `approved = false`, estado vacío). Mientras nadie las apruebe, la segunda mitad del
  criterio no se puede comprobar. Lo que falta: que Administración las apruebe (o las corrija) en el
  portal; quién: humano.
- Las otras 4 sin estado son de un parte nuevo de hoy (`ed6de051`, sin fecha leída: sv3 lo mandó a
  revisión con `motivos=sin_fecha`). Esperado.
- **Anomalía (fuera de F-055, conviene mirarla)**: las 2 `omitido` son del documento `5ea328f7`, que
  **sí tiene fecha de cabecera** (20261105). Se aprobaron el 2026-11-11 16:30 y sv5 las omitió por
  reglas de código de hora (recurso mensual), no por fecha: en ese lote sv5 **no** registró el
  WARNING `lineas sin fecha valida` (ninguno en Log Analytics desde el 2026-11-01), así que entonces
  tenían fecha. Hoy su `fecha_int` es NULL, como el de una `extra_auto` nueva del mismo documento,
  mientras otra `extra_auto` ya `registrado` conserva 20261105. Entre medias: un
  `[recalculo] … motivo=deshacer_cambio_fecha` el 2026-11-12 08:16 (sv4) y su recálculo en sv3
  (08:17). Hipótesis: **deshacer un cambio de fecha (o el recálculo que pide) deja las líneas sin
  `fecha_int`** aunque la cabecera la conserve. No se ha confirmado en código. Si es así, esas
  líneas, al volver a aprobarse, saldrían `fecha_no_valida` siendo de un día válido.

## F-058 · M2 — SUPERADA; M4 — medida, el cierre es del humano

**M2** (consulta de `design.md` §10 desde 2026-10-26T08:51:31): **200** documentos; 199 sin
`meta.relectura_cabecera` (no se releyeron: el campo solo se escribe si hay relectura) y **1**
`obra_inexistente / aplicada`. Coincide con Log Analytics: un único `[sv2][relectura]`, el
2026-11-12 08:18, `motivo=obra_inexistente` → `gemini/gemini-4-argon`. Ninguna relectura por
`sin_cabecera` en producción en estos 17 días.

**M4** (KQL de `design.md` §10, `[obra-sigrid]` en `ca-sv2-extraccion`, del 2026-10-26 al
2026-11-12): **200 consultas** (una por documento).

| resultado | n | p50 | p95 | máx |
|---|---|---|---|---|
| existe | 196 | 107 ms | 4.064 ms | 4.491 ms |
| no_existe | 1 | 96 ms | 96 ms | 96 ms |
| error (`ReadTimeout`) | 3 | 5.036 ms | 5.039 ms | 5.039 ms |

Distribución bimodal: **176 por debajo de 500 ms**, 1 entre 0,5 y 2 s, **23 ≥ 2 s** (20 entre
3,6 y 4,5 s y los 3 timeouts al tope de 5 s, el 2026-11-04 ×2 y el 2026-11-11 ×1). Las lentas salen
en rachas (p. ej. 2026-11-03 10:15–10:16 y 2026-11-11 08:47–08:48), lo que apunta a conexión nueva o
arranque en frío de sigrid-api más que a la consulta. Con DA12 = A, los 3 errores son «no se sabe»:
no relee por obra y la extracción sigue.

Lo que falta: **decisión del humano sobre DA12** (mantener 5 s, subirlo, o atacar la causa
reutilizando la conexión). El dato de M4 ya está.

## F-063 · M2 y M4 — M2 SUPERADA; M4 NO SUPERADA frente a DA3

Las M2 y M4 de F-063 son las de F-058 (arriba). La puerta DA3 de F-063, enmendada el 2026-10-26, se
aceptó midiendo la consulta con conexión reutilizada y dejando los tiempos reales a esta M4. En
producción la **mediana sí cumple** (≈105 ms ≤ 0,5 s), pero **el máximo no** (≤ 2 s exigido; 23 de
200 ≥ 2 s, máx 5.039 ms, 3 timeouts). La propia DA3 dejaba «reutilizar la conexión en sv2 (opción
B), otra feature si la M4 lo pide»: esta M4 lo pide. Decide el humano.

## F-060 · M4 — SUPERADA

Criterio (`progress/current.md`, bloque F-060): `grupos = 0` (ningún recurso-mes con dos CIZ de
partes desde el encendido) y `fin_movido > 0` cuando se hayan aprobado rachas de varios días.

- Sigrid, `CIZ` con `synckey LIKE 'partes:%'` y `fec >= 20261025`: **4 CIZ en 4 recursos**;
  recursos-mes con más de uno: **grupos = 0**.
- Base `partes`, `sigrid_motivo LIKE 'fin_movido:%'` desde 2026-10-25T12:09:28: **0**.
- Incidencias aprobadas desde el encendido: 8 `registrado`, 5 `omitido` `dia intermedio de la
  incidencia`, 1 `omitido` `incidencia_en_sigrid`. Las tres rachas de varios días (4, 4 y 2 días)
  se aprobaron **de una vez** (todas sus líneas con el mismo `sigrid_registrado_at_utc`): inicio y fin
  `registrado`, intermedios `intermedio`. En ese camino no hay `fin_movido` por diseño (M3 de
  F-060). `fin_movido = 0` es lo correcto, no un fallo; la mecánica de mover ya quedó probada en las
  M1–M3 locales de F-060 y en las de F-062.

El invariante que protege la M4 (un CIZ por recurso-mes) se cumple con datos reales. Si se quiere
ver un `fin_movido` real, hará falta una racha aprobada día a día (no se puede provocar en solo
lectura).

## F-062 · M6 — SUPERADA

Criterio: la M4 de F-060 ⇒ `grupos = 0`, y `synckey LIKE 'partes:%:ciz' AND fec >= 20261026` ⇒
`n > 0` cuando se aprueben incidencias.

- `partes:%:ciz` desde 20261026: **n = 2** (CIZ escritos el mismo día del inicio, de incidencias de
  un día aprobadas el 2026-11-11).
- `grupos` (CIZ de partes, `fec >= 20261026`): **0**.
- Contexto: desde 20261026 hay en Sigrid, con synckey de partes, CIV 3, CIP 1 y CIZ 4.

La «vista calendario de Administración» queda fuera (no es de este encargo).

## F-038 · M1 — SUPERADA

Criterio (`design.md` §9): tamaños reales, sin nombres, con las tres SELECT.

| Consulta | Resultado | Tiempo |
|---|---|---|
| (a) partidas por obra, top 5 (`obrparpar`) | 26.812 · 4.243 · 3.890 · 3.752 · 3.551 | 141 ms |
| (b) líneas por parte, top 5 (`hmores`) | 1.337 · 1.098 · 924 · 743 · 730 | 125 ms |
| (c) máximo de horas por recurso (`reshor`) | 20 | 93 ms |

Todas con `truncated = false` y muy por debajo de 500.000 (la mayor, 26.812: un 5 % del límite;
con el antiguo 1.000 por defecto, (a) y (b) se habrían truncado). La M1 pedía anotarlo también en
`progress/impl_F-038.md`: queda para quien cierre la feature (este informe no toca otros ficheros).

## F-048 · M4 — datos SUPERADOS; la mirada en el portal es del humano

Criterio (`design.md` §9): el siguiente parte con extras leídas en laborable ⇒ en el portal,
`normal` J con la etiqueta «incl. X h extra leídas» y su `extra_auto`; con la SELECT de
`tipo_hora, horas, horas_orig, horas_extra_leidas, extra_auto`.

- Líneas con `horas_extra_leidas > 0`: **173** en **88** partes (del 2026-10-19 al 2026-11-12),
  todas `tipo_hora = normal`. En partes activos, 151, y 110 de ellas con su `extra_auto` del mismo
  trabajador (las demás, presumiblemente, sin exceso sobre la jornada).
- Ejemplo (documento `2dc2ea16`, el más reciente): `normal 8,0 · horas_orig 10,5 ·
  horas_extra_leidas 2,0` + `extra 2,5 extra_auto`; las otras filas, `normal` con su `extra_auto`.
  Es la forma esperada.

Falta solo que una persona abra ese parte en el portal y vea la etiqueta. No la cuento como hecha.

## F-053 · M4 — DEL HUMANO

Criterio: «el candado de una línea `registrado` muestra el texto de DA8». Es una comprobación
visual en el portal; no hay forma de verla en solo lectura desde aquí. Queda para el humano.

## F-046 · M6 — DEL HUMANO

Criterio: «escritura en producción; la autoriza y la hace el humano en el portal: el 14/10
(0678/0704) con «Aplicar» ⇒ R6 en Sigrid y en `partes`». Exige actuar en el portal y escribir en
Sigrid: no se puede dar por hecha. Estado leído: `REPARTO_REAJUSTE = true` en sv3, y
`reparto_pendiente` tiene **1 fila**, `pendiente`, sin decisión, creada el 2026-10-19 (recurso-día
del 2026-10-09; no es la del 14/10 que cita la M6).

## Comprobaciones en el portal de producción (líder, Chrome, 2026-11-12 por la tarde)

Pedidas por el humano («si para cerrar falta alguna prueba en chrome, hazla»). Solo lectura, salvo
F-066 y F-061, que usan un parte manual de prueba en la obra 0404 (recurso de pruebas 2717792, sin
líneas reales en octubre ni noviembre; nada aprobado ni enviado a Sigrid).

| Feature | M | Resultado |
|---|---|---|
| F-066 | M2 | **SUPERADA**: 60 tipos, sin HENC; grupo «Horas extra» = HECAP, HEGR, HEOF, HEPE; HLGR→HEOF ⇒ Extra al recargar; vuelta a HLGR a mano (no con «Deshacer», que es global) ⇒ Ordinaria |
| F-048 | M4 | **SUPERADA**: el parte `2dc2ea16` muestra «incl. 2 h extra leídas» |
| F-053 | M4 | **SUPERADA**: el candado de la línea `registrado` 24289 lleva el texto de DA8 |
| F-050 | M4, M6 | **SUPERADAS**: `emp-` → `rec-`; «Por persona» con Empresa (45 Ruesma, 13 Porsan, 0 «—»; una persona en dos filas, Ruesma y Porsan). M2–M3 sin caso real hoy |
| F-064 | M1 | **SUPERADA** en producción: filtro Empresa=Porsan (7 obras) se mantiene tras detalle y volver, recarga y pestaña nueva; «Limpiar» lo quita y sigue quitado tras recargar. M2 (dos usuarios) es del humano |
| F-061 | M1 pasos 1–3 | **SUPERADOS**: con dos líneas, borrar una ⇒ el parte sigue; borrar la otra ⇒ `parte_retirado`, no sale en `/partes` ni en «Partes borrados» y las dos líneas sí en «Líneas sueltas»; restaurar una ⇒ el parte vuelve. Paso 4 (eliminar definitivamente) pendiente de autorización |

Las líneas de prueba 24451 y 24452 quedan en «Líneas sueltas» de la papelera; el parte `faefcba6`
queda retirado sin líneas.

## Cierres autorizados por el humano («si», 2026-11-13)

- **F-061 · M1 paso 4 SUPERADO.** Eliminadas definitivamente (`/api/registro/{id}/hard-delete`)
  las líneas de prueba 24451 y 24452. Solo lectura después: `parte_documents` con
  `id = 'faefcba6-…'` ⇒ 0; `parte_registros` 24451/24452 ⇒ 0; recurso de pruebas 2717792 en
  oct–nov ⇒ 0. El parte retirado se borró con su última fila (R10).
- **F-052 · M4 SUPERADA.** Sincronizar obra 0678 (`obr-2245328`), nómina 2026-10, modo seco: una
  línea `distinta` (registro 11308, 14/10, HLGR, `registrado`, hmores 410515): portal 8 h,
  Sigrid 4 h. Acción `traer_de_sigrid` ⇒ `aplicados: [11308]`, `recalculo: pedido`. En la base:
  horas 4, sigue `registrado` con el mismo hmores, `sigrid_motivo` «Sincronizado con Sigrid:
  horas 8→4 · <usuario> · <fecha>». Al volver a sincronizar, la línea sale `igual`. No se
  escribió nada en Sigrid.
