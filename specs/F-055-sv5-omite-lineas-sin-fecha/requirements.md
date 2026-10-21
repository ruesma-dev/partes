<!-- specs/F-055-sv5-omite-lineas-sin-fecha/requirements.md -->
# F-055 · sv5 omite las líneas sin fecha válida — Requisitos

**Servicio**: solo **sv5** (`services/partes-transfer`), que es quien escribe en Sigrid y el
último punto antes del ERP. sv4, sv3, el esquema y las colas no cambian (DA3). Rigor
**crítico** (DA9): cambia lo que sv5 escribe en Sigrid.

**Origen**: DA5 de F-054, aprobada por el humano el 2026-10-21 («apruebo F-054 y la DA5»).
Una línea de un parte sin fecha viaja de sv4 a sv5 con `fecha_int = 0` (`int(r.fecha_int or
0)` en `lineas_para_registro`) y sv5 la acepta: hoy daría de alta en Sigrid un parte
**`PT0/00001` del periodo 0/00** y escribiría la línea con `fec = 0` (sonda en `design.md`
§1.2). No ha pasado (M1 de F-054: 25 líneas sin fecha, ninguna enviada), pero hay 15 con obra
en 3 documentos que se pueden aprobar hoy, y en Sigrid no se borra (F-053).

## Glosario

- **Fecha válida** (DA2 B): `fecha_int` entero (no booleano), fecha real del calendario
  `AAAAMMDD`, no anterior a `FECHA_MINIMA` = 20260101 y no posterior a hoy +
  `DIAS_FUTURO` (31) días, ambos límites incluidos.
- **Motivo `fecha_no_valida`**: el texto con el que sv5 devuelve la línea omitida; el modal
  de resultado de sv4 agrupa por lo que va antes de los primeros dos puntos (F-034 R19).

## Requisitos

### La regla (función pura)

- **R1.** El sistema debe considerar válida una fecha solo si cumple el glosario: `None`, `0`,
  negativos, booleanos y no enteros son «sin fecha»; `20261340`, `20260230` o `20261000`
  «no es una fecha del calendario»; `20251231` «anterior al 01/01/2026»; hoy + 32 días
  «posterior»; `20260101`, hoy y hoy + 31 días son válidas.
- **R2.** El motivo debe ser `fecha_no_valida: <detalle>; corrige la fecha en el portal y
  reaprueba`, con el detalle de R1 (`la linea no tiene fecha`, `<valor> no es una fecha del
  calendario`, `<dd/mm/aaaa> es anterior al 01/01/2026`, `<dd/mm/aaaa> es posterior al
  <dd/mm/aaaa>`), sin tildes como el resto de motivos de sv5, sin nombres ni DNIs, sin otros
  dos puntos antes del detalle y de 255 caracteres como mucho (`sigrid_motivo` de sv4).

### En el pipeline de registro

- **R3.** SI una línea llega sin fecha válida, ENTONCES sv5 debe darle la acción `omitir` con
  el motivo de R2, y esa línea no debe escribirse, ni abrir o elegir parte de su periodo, ni
  consultarse por synckey, ni entrar en conflictos o pisados.
- **R4.** La omisión por fecha debe mandar sobre todas las demás: una línea sin fecha válida
  sale `fecha_no_valida` aunque su recurso no exista, sea de otra empresa, esté de baja, no
  traiga recurso ni DNI, no tenga horas o, con `MENSUALES_A_DEDICACION`, sea de un mensual
  (no sale `dedicacion`).
- **R5.** sv5 no debe pedir a Sigrid nada por una línea sin fecha válida: no entra en
  `recursos_por_dni`, `datos_recursos` ni `horas_de_recursos`, y su periodo no provoca
  `partes_del_periodo`, `siguiente_cod_pt` ni alta de parte.
- **R6.** CUANDO una petición mezcla líneas con y sin fecha válida, las válidas deben tener
  exactamente las mismas acciones, partes, conflictos y escritas que si viajaran solas.
- **R7.** CUANDO ninguna línea de `ejecutar` tiene fecha válida, sv5 no debe llamar a
  `escribir` y debe devolver `ok: true` con todas en `omitidas` (y `escritas` vacía).
- **R8.** El mismo trato en los tres caminos: `POST /api/registro/preflight` (en `acciones`,
  y contada en `resumen.omitir`), `POST /api/registro/ejecutar` y la cola `q-transfer` (en
  `omitidas` del resultado publicado).
- **R9.** CUANDO `fecha_int` llega `null` o no llega (DA4 B), el HTTP no debe responder 422 ni
  la cola fallar la petición: la línea se omite con `la linea no tiene fecha` y las demás
  siguen. `LineaEntrada.ano` y `.mes` deben dar 0 con `fecha_int` nulo.
- **R10.** CUANDO el reajuste (F-046) pide una extra nueva con `fecha_int` no nulo y no válido,
  su veredicto no debe ser editable y su motivo debe contener `fecha_no_valida`; nada se
  escribe. Las líneas existentes del reajuste no cambian (su fecha es la de Sigrid).
- **R11.** CUANDO una petición trae líneas sin fecha válida, sv5 debe dejar un WARNING con la
  obra destino, cuántas son y sus `registro_id`, sin nombres ni DNIs.

### Lo que no cambia

- **R12.** Con todas las fechas válidas, el comportamiento debe ser el de hoy: la suite de sv5
  existente pasa sin tocar ningún `assert`. F-034 (relectura, `parte_abierto.py`), F-053
  (pisado a 0), F-031 (parte y complementario), F-021 (cuenta) y F-019 no cambian.
- **R13.** sv4, sv3, sv1, sv2, `orm_models.py`, el contrato de respuesta (mismas claves) y las
  colas no deben cambiar; la duplicación tolerada de `CLAUDE.md` no crece.

### Documentación

- **R14.** `docs/ARCHITECTURE.md` (semántica 6) y `azure-apps/partes.md` (lo que devuelve sv5)
  deben nombrar la guarda y el motivo `fecha_no_valida`; en `azure-apps/partes.md`, una nota a
  `porcentajes` (DA7) sin tocar su repositorio.

## Ejemplos (hoy = 2026-10-22; detalle en `design.md` §8)

| Línea (`fecha_int`) | Hoy | F-055 |
|---|---|---|
| `0` (parte sin fecha, sv4) | escribe en `PT0/00001` (periodo 0/00) | `omitir`: `la linea no tiene fecha` |
| `null` por HTTP | 422, la petición entera | `omitir`: `la linea no tiene fecha` |
| `20261340` | parte de 2026/13 | `omitir`: `20261340 no es una fecha del calendario` |
| `20160315` (año mal tecleado) | parte de 03/2016 o su complementario | `omitir`: `15/03/2016 es anterior al 01/01/2026` |
| `20620315` | parte `PT62/…` | `omitir`: `15/03/2062 es posterior al 22/11/2026` |
| `20261014` | se escribe | se escribe (igual) |
| `0` de un mensual con el interruptor encendido | `dedicacion` con fecha 0 | `omitir` (R4) |
| Extra nueva del reajuste con `20261340` | se escribe en el parte de la base | no editable (R10) |

## Fuera de alcance

- Líneas **sin obra**: hoy ya fallan cerradas (`RuntimeError` «obra no encontrada», nada
  escrito; DA5 A).
- Que sv4 no envíe o avise de las líneas sin fecha (DA3 B/C): F-054 ya manda el parte a
  revisión; el motivo vuelve en el resultado.
- Comparar la fecha con la del documento (DA2 C) y corregir lo ya escrito (M1 lo mide).
