<!-- progress/spec_F-072.md -->
# F-072 · Resumen de la spec (spec-author, 2026-11-20)

Spec: `specs/F-072-postventa-var-como-obras/`: requirements 149/150, design 250/250 (al tope), tasks
T1–T32, de las que T29–T31 son manuales. Rama `feature/F-072-postventa-var-como-obras`. Rigor
`critico` (disparador 2: sv5 decide la obra y la partida que escribe en Sigrid, que es
producción). F-072 queda lista para `spec_ready`, pendiente de aprobación. El estado lo pone el
líder.

## Qué propone

- **Entrada = obra agrupada + partida.** Una línea de postventa o de VAR va a la obra agrupada
  de su empresa: `POSTVENTA_OBRA_COD` (POSTV2) o `VAR_OBRA_COD` (VAR).
  - Lleva la partida de la entrada y la marca `partida_match_method` = `postventa`/`var`.
  - **Sin columnas nuevas ni DDL** (DA5). La entrada se deduce de la propia línea.
- **Casado (las reglas P5 y VAR de porcentajes, reimplementadas):**
  - Postventa: código entero normalizado (0656 ≠ 656) o el código seguido solo de letras, la
    más corta. Solo hojas activas y de forma determinista.
  - VAR: hojas activas con número inicial ≥ `VAR_PARTIDA_DESDE`.
  - Todo vive en un **módulo puro gemelo** (`obras_agrupadas.py`), igual en sv3, sv4 y sv5
    (DA4). Lo vigilan dos tests: uno de gemelos y otro de equivalencia con el repo de
    porcentajes, que se salta si ese repo no está al lado.
- **Papel → IA → sv3:**
  - El encargado marca el «Nº OBRA»: `VAR-29`, `POSTVENTA 578`, o solo `VAR`/`POSTV2` con la
    partida en la sección de partidas (DA1).
  - sv2 copia la marca y no relee por «obra inexistente» (DA3).
  - sv3 elige la obra agrupada de la empresa (F-023), casa la entrada y deja la partida en las
    líneas.
  - Sin entrada, el parte queda **sin obra y a revisión**, con un motivo de una lista cerrada.
    Nunca se elige al azar.
- **Portal (sv4):**
  - Un catálogo de entradas por empresa alimenta el selector, el cambio de obra y el parte
    nuevo.
  - Clave de vista `agr-<obra>-<partida>`, con rótulos `Postv-0578` y `VAR-29`.
  - La partida queda fija (409 si se intenta cambiar). VAR y POSTV2 ya no se ofrecen como obra
    normal (DA7).
  - Aprobar manda una petición por entrada.
- **sv5:**
  - Guarda antes de escribir: en una obra agrupada omite la línea sin marca, sin partida, con
    capítulo, de baja o (en VAR) fuera del universo. El motivo empieza por
    `partida_agrupada:`.
  - En las obras agrupadas el conflicto exige además la misma partida (DA8).
- **Jornada, extras y franquicia: sin cambio.** La unidad del reparto sigue siendo la obra de
  Sigrid.
- **Configuración:** sin valores en el código; vacío = apagado (DA11). Los valores salen de lo
  que porcentajes tiene **versionado**, sin abrir ningún `.env`: `POSTV2`, `VAR`, `29`.
  - Orden de despliegue: el código con todo vacío primero; luego se enciende sv5 → sv3 → sv2 →
    sv4.
  - `azure-apps/partes.md` se actualiza en un commit aparte.

## Enmienda del humano (2026-11-20): «V y número, POST y número, y variantes»

- **Marcas nuevas**: `V` + número vale como VAR y `POST` + número como postventa. Son alias
  configurables (`VAR_ALIAS`, `POSTVENTA_ALIAS`), no código (DA2).
- **Variantes (R41)**: un conjunto cerrado y determinista.
  - No distingue mayúsculas ni tildes.
  - La marca puede ir delante o detrás del número.
  - Separadores admitidos: ninguno, espacios, guion, punto o barra.
  - Gana la marca más larga.
  - Un alias de una letra (`V`) solo vale seguido de un resto que empiece por dígito, y nunca
    va solo.
  - Ejemplos que valen: `V29`, `v-29`, `V.29`, `V/29`, `29 V`, `POST578`, `post-578`,
    `578/POST`, `Postventá 578`. No valen: `V`, `VALENCIA 3`, `POSTE`.
- **Comprobado en Sigrid** (sigrid-api, solo lectura, 927 obras, 2026-11-20):
  - `POSTV2` y `VAR` existen en las empresas **1 y 28**, no solo en la 1. Esto corrige la nota
    anterior; la elección entre gemelas de F-023 la decide el membrete.
  - Existe una obra antigua `POSTV` en la empresa 1.
  - Ningún otro código empieza por `V`, `POST` ni `PV`.
  - Solo una obra acaba en `-V`: **`150702-V`** (empresa 1).
- **Colisión (R42, DA13)**: si lo leído, sin separadores, es el código de una obra real que no
  es una marca, gana la obra, con el WARNING `marca_colisiona`. Así `150702-V` es esa obra y no
  la VAR. Si lo leído es exactamente una marca, es la forma base: `POSTV` va a postventa, como
  hizo porcentajes con la `POSTV` antigua (D6).
- **La `V` de vacaciones (R43)**: la marca solo se busca en `cabecera.obra_numero`. Las
  incidencias de las filas de personal no intervienen nunca.
- **La IA (R12)**: copia el «Nº OBRA» tal cual, sin expandir `V` ni `POST`, sin quitar
  separadores y sin añadir ceros. sv2 usa el mismo `leer_forma` del gemelo para no releer.
- **Tamaño**: ha cabido comprimiendo texto, sin quitar requisitos. design queda en 250/250, sin
  margen: otra ampliación obligaría a partir la feature o a mover detalle fuera de `design.md`.

## Hallazgos que el humano debe conocer

1. **«Una obra cerrada del universo solo se ofrece como postventa» no tiene equivalente hoy en
   partes.** partes no filtra obras por estado; porcentajes sí (`estados_excluidos`). Lo decide
   DA6. La recomendación es no aplicarlo en esta feature.
2. **«Se tratan los capítulos como obras».** Las reglas de porcentajes imputan siempre a una
   **partida hoja**, nunca a un capítulo. La spec sigue las reglas: cada entrada es una hoja
   activa.
3. **Falsos conflictos en sv5.** Hoy un choque es por recurso, día y código de hora, sin la
   partida. Con una petición por entrada, dos entradas VAR del mismo día se verían como
   conflicto pisable entre sí: el usuario podría poner a 0 una línea buena (DA8).
4. **La extra del popup de sv4 no clona la partida** (`parte_repository.py`, hacia la l. 1956).
   En una entrada cambiaría de vista; R31 lo corrige.
5. **porcentajes toma `exactas[0]`** en el orden de sus filas. Partes desempata por menor `ide`.
   No se conoce ningún caso real con dos exactas.
6. **Qué escribe hoy el encargado en el papel es una incógnita.** M0 (T29, una consulta de
   solo lectura a la base `partes`) lo mide. Conviene tenerla antes de cerrar DA1 y DA9, pero
   no bloquea.

## Decisiones para el humano (todas abiertas)

| Decisión | Recomendado |
|---|---|
| DA1 Qué escribe el encargado en el papel | (a) marca en «Nº OBRA», delante o detrás; con solo la obra agrupada, la sección de partidas |
| DA2 Alias (enmienda) | (a) `POSTVENTA_ALIAS=POSTVENTA,POSTV,POST` y `VAR_ALIAS=V`, sin `PV` (no se pidió; ninguna obra empieza por `PV`; añadirlo es solo configuración) |
| DA3 sv2 con marca | (a) no consulta ni relee |
| DA4 Dónde vive la lógica común | (a) gemelo en sv2, sv3, sv4 y sv5 (sv2 solo usa `leer_forma`), nuevo en la lista cerrada de `CLAUDE.md`, con test de equivalencia con porcentajes |
| DA5 Cómo se guarda la entrada | (a) en la línea, sin columnas nuevas |
| DA6 Obra cerrada solo como postventa | (a) no aplica en partes; (b)/(c) en otra feature |
| DA7 VAR y POSTV2 como obra normal | (a) ninguna de las dos se ofrece |
| DA8 Conflictos en sv5 | (a) en las obras agrupadas solo choca la misma partida |
| DA9 Partes ya guardados | (a) no se recasan; se corrigen con «cambiar obra» |
| DA10 Bandeja de dedicación | (a) sin columnas nuevas; aviso a porcentajes |
| DA11 Valores de configuración | (a) sin valores por defecto en el código |
| DA12 Sincronizar una entrada | (a) fuera, «no sincronizable» con motivo |
| DA13 Marca que coincide con una obra real | (a) gana la obra real si lo leído es su código sin separadores y no es exactamente una marca (`150702-V`); lo que es exactamente una marca es forma base aunque la obra exista (la antigua `POSTV` ⇒ postventa); (b) toda coincidencia a revisión |

Opciones completas en `design.md` §13.

## Qué queda fuera

- El filtro por estado (DA6).
- Sincronizar por entrada (DA12).
- La regla de seis dígitos de porcentajes.
- Columnas nuevas en la bandeja.
- Recasar lo ya ingerido.
