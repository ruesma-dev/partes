<!-- specs/F-083-ciz-solo-fin-de-racha/design.md -->
# F-083 · Una racha de incidencia solo lleva CIZ en su último día — Diseño

**Rigor: `critico`.** Disparador 2 de «Niveles de rigor» (`CHECKPOINTS.md`): **escribe en
producción**. sv5 (`services/partes-transfer/`) escribe en `hmores` de Sigrid (`ruesma`) a
través de sigrid-api, y F-083 cambia cuándo escribe un CIZ (fin de racha) y cuándo no.

## 1. Contexto y límite de servicio

Hoy, con `MOVER_CIZ` encendido (F-060 y F-062), sv4 decide el rol de cada día con el histórico
de `partes` y manda los ids de la racha. sv5 lee de Sigrid las líneas con esas synckeys
(`lineas_de_racha`, **ya trae cualquier código**), pero solo mira las que son CIZ. Por eso una
racha cuyo CIZ final pasó a mano a CIV parece «sin fin», y el siguiente `fin` que llega escribe
un CIZ en medio (caso 0730, `requirements.md`).

F-083 cambia una sola idea: **el fin está más adelante si la racha tiene CUALQUIER línea suya en
Sigrid en un día posterior**. Si además es CIZ, todo sigue como hoy.

**Límite de servicio (D1 = a).** La regla vive solo en **sv5**: es quien ve Sigrid, que es lo
que decide (un CIZ cambiado a mano solo se ve allí). sv4 decide el rol con `partes`, y su
`registrado` no dice qué código quedó en Sigrid: duplicar la regla en sv4 sería copiar lógica
entre servicios para nada. sv4, sv1, sv2 y sv3 no se tocan, y la lista cerrada de
duplicaciones no crece.

## 2. Ficheros

**Crear**: `services/partes-transfer/tests/test_f083_ciz_solo_fin_de_racha.py`, puro (R1–R9,
R19, R20) y de pipeline con `SigridFake` de `tests/dobles.py` (R10–R18).

**Modificar**:
- `services/partes-transfer/application/services/racha_ciz.py`: §3 y docstring del módulo.
- `services/partes-transfer/application/pipelines/registro_pipeline.py`: dos WARNING en
  `_ciz_de_racha` (§4) y una frase en el docstring del paso 6 bis.
- `services/partes-transfer/tests/test_f060_racha_ciz.py` y `tests/test_f062_ciz_mismo_dia.py`:
  solo el subcaso de R22, con un comentario `# F-083 R2` o `# F-083 R8`.
- Docs de §9.

**NO se tocan**:
- `infrastructure/sigrid/sigrid_write_client.py` (`lineas_de_racha` ya lee todo código y
  ninguna sentencia cambia), `reglas_registro.py`, `config/settings.py` (sin variable nueva) y
  `domain/models/registro_models.py`;
- sv4 entero (`racha_incidencia.py`, `parte_repository.py`, `app.js`, plantillas), sv1–sv3.

## 3. Regla pura (`racha_ciz.py`, capa application)

```python
#: F-083 (R8): el inicio no escribe hermano: la racha sigue despues sin CIZ.
MOTIVO_POSTERIOR_SIN_CIZ = "posterior_sin_ciz"

@dataclass(frozen=True)
class DecisionFin:
    ...                      # campos de hoy, sin cambios
    sin_ciz: bool = False    # F-083 (R7): intermedio por una linea que no es CIZ

def es_linea_de_la_racha(ls, recurso_ide, marca_pruebas) -> bool:
    """F-083: mismo recurso, `can` nulo o 0 y, en pruebas, la marca. Cualquier codigo."""

def es_ciz_del_recurso(ls, recurso_ide, marca_pruebas) -> bool:
    # misma semantica que hoy, reescrita como:
    return es_linea_de_la_racha(...) and codigo == CODIGO_FIN

def ultima_posterior(candidatas, fecha_int, recurso_ide, marca_pruebas,
                     solo_ciz: bool) -> LineaSigrid | None:
    """La de mayor (fecha, ide) con fecha > D; None si no hay."""

def motivo_intermedio_racha(ide: int, fecha_int: int, cod: str | None) -> str:
    return (f"{MOTIVO_INTERMEDIO} (la racha sigue en Sigrid el dia {fecha_iso(fecha_int)}, "
            f"linea {ide} con {cod or 'sin codigo'}, sin CIZ despues; no se escribe un fin "
            f"en medio)")[:LIMITE_MOTIVO]
```

**`decidir_fin`**, en este orden:
1. Hay CIZ posterior: `INTERMEDIO` con `motivo_intermedio_ciz`, como hoy (R1).
2. Hay una línea de la racha posterior: `INTERMEDIO` con `motivo_intermedio_racha` y
   `sin_ciz=True` (R2, R7).
3. Si no, lo de hoy (R6).

El paso 2 va antes de mirar las anteriores, así que gana a mover, `enlazada` y `parte_cerrado`
(R3). El enlace o el parte de la posterior no se miran (R4).

**`decidir_mismo_dia`**, en este orden: `ya_existe`, luego `posterior` (CIZ), luego
`posterior_sin_ciz`, y si no, `None` (R9).

Ejemplo de motivo (R19), 184 caracteres que el portal agrupa con los intermedios: «dia
intermedio de la incidencia: solo se registran el inicio y el fin (la racha sigue en Sigrid el
dia 2026-11-20, linea 416319 con CIV, sin CIZ despues; no se escribe un fin en medio)».

## 4. Pipeline (`_ciz_de_racha`, paso 6 bis)

Mismas lecturas y mismo sitio que hoy (R12): bajo el lock en `registrar` y consultivo en
`preflight` (R17). Dos cambios, los dos solo de log:

- en el bucle de `fines`, si `d.sin_ciz`:
  `logger.warning("[registro] racha_fin_no_ciz registro_id=%s motivo=%s", ...)` y después
  `_omitir` como hoy (R10);
- en el bucle de `inicios`, si `motivo == MOTIVO_POSTERIOR_SIN_CIZ`: el mismo WARNING con
  `motivo=posterior_sin_ciz`, y `_sin_hermano` como hoy (R11).

Las omisiones ya existían. No hay sentencia nueva ni modificada, ni ningún `DELETE` (R20). La
`omitida` viaja a sv4 por el camino de siempre: estado `omitido` y `sigrid_motivo`.

## 5. Casos

| Situación en Sigrid al llegar D | Hoy | Con F-083 |
|---|---|---|
| CIZ de la racha posterior a D | `intermedio` | igual (R1) |
| Solo CI* u otro código posterior (0730) | `crear`: CIZ en medio | `intermedio` + WARNING (R2) |
| CIZ anterior y CIV posterior | `mover` el CIZ a D | `intermedio`; el CIZ no se toca (R3) |
| Posterior con horas (Administración lo hizo trabajo) | `crear` | igual (R5): la racha acaba antes |
| Nada posterior | mover, crear, enlazada o cerrado | igual (R6) |
| `inicio` con CI* posterior y sin CIZ | CI* + hermano CIZ en D | solo CI* + WARNING (R8) |

**La racha queda sin fin (D6 = a).** Si Administración quitó a mano el CIZ del último día,
ningún día de la racha escribe un CIZ, ni D ni el último: manda lo hecho a mano. El WARNING
`racha_fin_no_ciz` y el motivo del portal lo dejan a la vista.

## 6. Interacciones

- **sv4 (R21)**:
  - `decidir` sigue dando `fin` al día con días anteriores de la racha, aunque los posteriores
    ya estén registrados: lo corrige sv5;
  - el ↻ de un «omitido · intermedio» se mantiene (D3): con F-083 reaprobar es inocuo, y hace
    falta si la racha cambió en `partes` (por ejemplo, el día siguiente pasa a ser trabajo).
- **`racha_desordenada` (F-060 R10, D4 = a)**: sin cambios. Sigue avisando de un trabajo o un
  `inicio` aprobado antes de una incidencia ya registrada. Si lo de delante es un CIZ, F-083 no
  hace nada (y F-062 ya no escribía el hermano), así que el aviso sobra pero no engaña. Si lo de
  delante es un CI* escrito como `inicio`, la racha sí queda con dos CI* y el aviso hace falta.
- **Papelera (F-060 DA13)**: una línea de la papelera `registrado`/`encolado` del tramo que ya
  vive en Sigrid cuenta como línea de la racha. Es coherente: está escrita.
- **F-062 R12 (CIZ ajeno el día D)**, **F-053**, **F-034**, **F-072** y la marca de pruebas
  (F-060 R19): sin cambios. F-083 solo convierte `crear`/`mover`/hermano en omisiones.

## 7. Tests (sin red ni BBDD; fase RED con traza en R1–R17 y R19)

- **Puro**:
  - `_ls` como en `test_f060_racha_ciz.py`, con `hora` libre;
  - R2 con CIV y con `hora=None`;
  - R3 con un CIZ anterior en un parte abierto, en uno cerrado y enlazado;
  - R4 y los cinco descartes de R5, cada uno parametrizado;
  - R9 con todas las combinaciones de orden;
  - R19: motivo de 255 exactos con un `cod` largo, sin tildes (`unicodedata`), prefijo
    `MOTIVO_INTERMEDIO`.
- **Pipeline con `SigridFake`**:
  - R13: la aprobación conjunta real y, en `cli.lineas`, `horide` de d3 cambiado a CIV;
  - R14, R15 y R16;
  - R17 con `preflight`;
  - R18: apagado, sentencias comparadas con las de hoy;
  - R10 y R11 con `caplog` (sin DNI ni nombre en el texto);
  - R12: el doble cuenta las llamadas a `lineas_de_racha` y `estados_de_partes`.
- **Caracterización**: suites de sv5 y sv4 sin cambios (R21), salvo las enmiendas de R22.

## 8. Verificaciones manuales (`MANUAL (humano)`)

`$KEY` es la function key de sigrid-api, que el humano saca del Key Vault (nunca en un fichero).
Llamada de lectura S:
`Invoke-RestMethod -Method Post -Uri "$env:SIGRID_API_BASE_URL/api/sql/read" -Headers
@{ 'x-functions-key' = $KEY } -ContentType 'application/json' -Body $q`.

- **M0 (producción, solo lectura, antes de desplegar)**: el estado del caso real.
  - Consulta:
    `$q = @{ database='ruesma'; max_rows=10; parameters=@('partes:25090','partes:25091',
    'partes:25092'); sql='SELECT h.ide, h.fec, a.cod, h.can, h.synckey FROM hmores h LEFT JOIN
    auxhor a ON a.ide = h.horide WHERE h.synckey IN (?, ?, ?)' } | ConvertTo-Json`.
  - Esperado: 416318, 416319 y 416356, las tres con CIV y `can` 0; se anota en `progress/`.
- **Preparación de M1–M3 (local, modo pruebas)**: la de F-062 `design.md` §9, con F-083 en
  `dev`, ANTES de desplegar sv5.
  - sv5 con `OBRA_PRUEBAS_FORZAR=true` y `MOVER_CIZ=true`; `/health` debe dar
    `modo_pruebas: True`, y si no, **PARA**.
  - sv4 con `MOVER_CIZ=true`.
  - Obra 0404, marca PRUEBA-IA, recurso de pruebas.
  - Un mes sin parte de la 0404 (`estado` ⇒ `NO existe parte`) y nunca 2026/06–2026/11.
- **M1 · caso 0730 (`<M1>`)**: V los días 1–3 y 8 h el 4.
  1. Aprobar 1–3 juntos. S debe dar CIV el 01 y CIZ el 03 (`partes:<id3>`).
  2. El humano cambia **a mano en Sigrid** esa línea de pruebas de CIZ a CIV. Es una edición
     de una línea PRUEBA-IA de la 0404, la acción concreta que autoriza al aceptar M1. Si no la
     autoriza, M1 queda cubierta por R13 y se hacen M2 y M3.
  3. ↻ en el día 2. En L, el día 2 debe salir `omitido` con «la racha sigue en Sigrid el dia
     …03, linea <ide3> con CIV». S no debe tener `partes:<id2>` ni `partes:<id2>:ciz`. La
     consola de sv5 debe dar `racha_fin_no_ciz`.
- **M2 · regresión (`<M2>`)**: lo mismo sin el paso 2. El día 2 sale `omitido` con «el fin, CIZ
  linea <ide3>, ya esta el dia …03», y sin escrituras.
- **M3 · inicio desordenado (`<M3>`)**: V los días 1–3.
  1. Aprobar el 3 solo: CIZ el 03.
  2. Cambio manual a CIV, como en M1.
  3. Aprobar el 1: solo CIV el 01, sin `partes:<id1>:ciz`. La consola debe dar
     `ciz_mismo_dia_omitido … motivo=posterior_sin_ciz` y `racha_fin_no_ciz`.
- **Limpieza**: la de F-062 §9 (`prueba_escritura_sigrid.py limpiar`, DRY-RUN revisado y
  `--ejecutar`, `estado` ⇒ `NO existe parte`, `git checkout -- prueba_escritura_sigrid.py`).
- **M4 (producción, solo lectura, tras desplegar sv5)**: lista los CIZ de partes escritos desde
  el despliegue que tienen después otra línea de partes del mismo recurso.
  - Consulta:
    `$q = @{ database='ruesma'; max_rows=50; parameters=@(<IDE_MAX_AL_DESPLEGAR>);
    sql='SELECT z.ide, z.fec, x.ide AS ide_post, x.fec AS fec_post, b.cod FROM hmores z JOIN
    auxhor a ON a.ide = z.horide JOIN hmores x ON x.reside = z.reside AND x.fec > z.fec AND
    x.synckey LIKE ''partes:%'' AND ISNULL(x.can, 0) = 0 JOIN auxhor b ON b.ide = x.horide
    WHERE a.cod = ''CIZ'' AND z.synckey LIKE ''partes:%'' AND z.ide > ? AND b.cod LIKE ''CI%''
    ORDER BY z.ide' } | ConvertTo-Json`.
  - Esperado: ninguna fila con `fec_post` en el día siguiente de la misma racha. Las de una
    racha posterior distinta son legítimas: el humano las mira una a una.

## 9. Documentación

Cada documento recibe una frase nueva: «desde F-083, cualquier línea de la racha posterior en
Sigrid, sea cual sea su código, deja el día como intermedio, y un CIZ cambiado a mano deja la
racha sin fin».
- `docs/ARCHITECTURE.md`, semántica 4, tras «Un CIZ ya posterior ⇒ `intermedio`».
- `docs/referencia/partes-proyecto.md` §3.5 3c (l.216–232).
- `C:\Users\pgris\PycharmProjects\azure-apps\partes.md`, paso 3c («CIZ ya en un día posterior
  ⇒…») y 3d. Protocolo del ecosistema: `git pull --rebase`, solo `partes.md`, commit aparte y
  sin push.
- Docstrings de `racha_ciz.py` y del paso 6 bis.

## 10. Riesgos y alternativas descartadas

- **Racha sin CIZ** cuando Administración lo quita a mano (D6): es a propósito. Lo hacen visible
  el WARNING y el motivo.
- **No se arregla lo ya escrito** (D8): la 416356 ya es CIV, la cambió Administración. Un barrido
  de CIZ en medio, si se quiere, sería otra feature de solo lectura.
- **Fuera**: un CI* escrito en medio de la racha. Pasa cuando un día posterior se aprobó como
  `inicio` antes de ingerirse los anteriores. F-083 solo gobierna el CIZ, así que ese caso sigue
  como hoy, con el aviso `racha_desordenada` cuando aplica.
- **Vuelta atrás**: la imagen anterior de sv5. F-083 solo escribe menos, nunca más ni distinto:
  volver atrás no deja nada a medias.
- **Descartadas**:
  - regla también en sv4 (D1 b): duplica lógica y no ve Sigrid;
  - solo códigos CI* (D5 b): una línea nuestra con otro código sigue siendo de la racha;
  - un CIZ nuevo en el último día (D6 b): contradice lo hecho a mano y escribe con la synckey de
    otro registro;
  - variable nueva (D7 b): cuatro combinaciones más para una regla que solo quita escrituras.

## 11. Frontera

**¿Cruza la frontera del proyecto? Sí, sin cambiar ningún contrato.** No cambia ningún
endpoint, tabla, columna, cola ni variable. Lo que cambia es **qué escribe sv5 en `hmores` de
Sigrid**, un recurso compartido a través de sigrid-api: menos CIZ, nunca uno en medio de una
racha. Se actualiza `azure-apps/partes.md` (§9). Ni sigrid-api ni los demás proyectos cambian.

## 12. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| D1 Servicios | (a) solo sv5: la regla mira Sigrid; (b) sv5 + sv4: `decidir` da `intermedio` si hay días posteriores de la racha `registrado`; (c) solo sv4 | (a) | |
| D2 Motivo que ve el portal | (a) prefijo de intermedio + detalle (línea, día, código, «sin CIZ despues»), agrupado con los intermedios; (b) prefijo nuevo `racha_sin_ciz:` que lo separe en el modal | (a) | |
| D3 ↻ en un «omitido · intermedio» | (a) se mantiene (con F-083 es inocuo); (b) se oculta para ese motivo; (c) se mantiene con una confirmación de aviso | (a) | |
| D4 Aviso `racha_desordenada` (F-060 R10) | (a) sin cambios; (b) también en el `fin` con días posteriores registrados; (c) quitarlo | (a) | |
| D5 Qué línea posterior cuenta | (a) cualquier código, `can` nulo o 0, mismo recurso y marca en pruebas; (b) solo códigos CI* | (a) | |
| D6 CIZ quitado a mano del último día | (a) respetar: la racha queda sin fin, con WARNING y motivo; (b) escribir un CIZ nuevo en el último día | (a) | |
| D7 Interruptor | (a) bajo `MOVER_CIZ`, sin variable nueva (desplegar sv5 = activar); (b) variable propia | (a) | |
| D8 CIZ ya escritos en medio (0730: 416356) | (a) nada retroactivo: Administración ya los corrigió a mano; (b) script de corrección (otra feature) | (a) | |
