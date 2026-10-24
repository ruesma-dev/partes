<!-- progress/review_F-060.md -->
Revisión completa (pasada 1) · `git diff 0926857...4f102aa` (base dev 0926857, HEAD 4f102aa)

# Review F-060 · Racha de incidencia con CIZ móvil

**Veredicto: CHANGES_REQUESTED**

**Nivel de rigor: `critico`** (declarado en `features.json`): C1–C5, C3 bis, C4 bis con fase RED,
cobertura ≥ 80 %, mutación completa con 0 supervivientes salvo los que acepte el humano, RM1–RM6
(RM5 de `critico`) y MANUAL en `current.md` con comando exacto.

El código cumple la spec al pie de la letra (sin `DELETE`, `UPDATE` con `WHERE` optimista y doble
guarda, CAS idempotente, interruptor apagado). Se rechaza por: (1) M1–M3 sin comando exacto en
`current.md` (el motivo de F-038 y F-059); (2) una divergencia de R26 de extremo a extremo que la
documentación vende como «vuelta atrás»; (3) papeleo desfasado y equivalentes sin demostración
versionada.

## Hallazgo principal · `MOVER_CIZ=false` no es «como antes de F-060»

R26 se cumple en sv5 (`test_f060_r26_*`). Pero el cambio de sv4 **no va tras el interruptor**: R4
quita la mirada hacia delante de `_rol_incidencia`. Lo reproduje con el mismo script en base
(0926857, `git archive` al scratchpad) y en F-060: V los días 1–4 y trabajo el 5 ya ingeridos,
aprobando solo el 2, luego solo el 3 y luego solo el 4:

```
base 0926857:  2 intermedio · 3 intermedio · 4 fin            => 1 CIZ en Sigrid
F-060       :  2 fin [1,3,4] · 3 fin [1,2,4] · 4 fin [1,2,3]  => apagado: 3 CIZ; encendido: 1 (movido)
```

Encendido, bien. Apagado —como se despliega y como queda hasta que Administración dé el visto bueno
a DA3/DA6— la aprobación día a día con días posteriores ya ingeridos escribe **más** CIZ que hoy, y
apagarlo no es la vuelta atrás que dicen `config/settings.py:44-47`, `partes-proyecto.md:546-547`,
`azure-apps/partes.md:607` («como antes de F-060») ni la M4 de `current.md`. El implementer es fiel
a la spec (R4 lo pide; `test_f060_r4_racha_abierta_es_fin_sin_mirar_delante` lo fija): es un hueco
de la spec que decide el humano.

## Checkpoints

- **C1** [x] `init.sh` exit 0 (ver «Ejecución») · [x] ficheros del arnés.
- **C2** [x] solo F-060 `in_progress` (F-038 en paralelo por decisión del humano) · [x] rama de la
  feature · [x] `current.md` con la sesión · [x] `history.md` sin cambios (no está `done`).
- **C3** [x] hexagonal: `racha_ciz.py` y `racha_incidencia.py` puros en `application/`; SQL solo en
  `infrastructure/` · [x] primera línea con ruta (20 ficheros) · [x] sin `print`, TODOs, secretos ni
  dependencias nuevas · [x] trampas: (1) sv5 solo mueve un CIZ del mismo `reside` y sv4 cruza por
  `persona_de`; (2) `can = 0`, CI* + un CIZ, intermedios sin escribir; (3) sin esquema.
  **LÍMITE DE SERVICIO** [x]: sv4 no lee Sigrid y sv5 no lee `partes`; ninguna copia de la lista
  cerrada tocada (`congelacion`, `recurso_conciliador`, `seleccion_sigrid`, `coherencia_recurso`,
  `jornada_resolver`, `estado_parte`, `cuenta_analitica`).
- **C3 bis** (toca `partes-proyecto.md`, sin documento nuevo) [x] cabecera N/A: no hay documento
  nuevo · [x] `git log --diff-filter=A` sin PDF ni ofimática · [x] barrido mío de todas las líneas
  añadidas: correos, IPv4, GUID, DNI `\b\d{8}[A-Z]\b`, `password|secret|api_key|token|functions-key|
  AccountKey|sig=`: **nada sensible** (solo `@pytest` y `$KEY`/`secretref`) · [x] nada redactado.
- **C4** [x] R1–R30 con tests `test_f060_rN_*` en verde (tabla abajo); R31 revisado contra §10
  (ARCHITECTURE, partes-proyecto §3.5/§4.4, azure-apps c914caa sin push) · [x] sin red ni BBDD ·
  **[ ] MANUAL con comando exacto**: la M4 está con su `Invoke-RestMethod` y su `SELECT` literales,
  pero **M1, M2 y M3** solo figuran como «T14: M1–M3 (humano, local, modo pruebas)» y remiten a
  `design.md` §9. Cambio 1.
- **C4 bis**
  - [x] `rigor: critico` · [x] fase RED con trazas reales T1–T11 (R27 caracterización, declarado).
  - [x] `PUERTA COBERTURA` [OK] 99,7 % (323/324).
  - [x] recálculo puro (`alcance_de_feature` + `generar_mutantes`): **11 ficheros, 776 líneas, 221
    mutantes**, igual que el informe. Muestreé #4 (`racha_incidencia.py:136`), #7 (`:197`), #10
    (`parte_repository.py:2358`), #11 (`registro_pipeline.py:481`) y #12 (`:699`): existen con el
    mismo operador y texto.
  - [x] «Tiempo total» 22.626 s > 60 s: **campaña no reejecutada (377 min según el informe)**; me
    quedo en el recálculo puro y RM1–RM6.
  - [x] coste por mutante 22.626 × 4 ÷ 221 = 409,5 s · [x] sin «NO VÁLIDA», base rota 0, 8 bases.
  - [x] **RM1**: mide `1009cdb`; `1009cdb..HEAD` solo toca tests, `progress/` y `tasks.md`.
  - [x] **RM2**: 102,4 s × 4 = 409,6 s/mutante frente a ~461 s a suite completa (140 de sv4 a
    ~717 s, 81 de sv5 a ~22 s): coherente con `-x`. 221 × 102,4 ≈ 22.626.
  - [x] **RM3**: los `or 0 → or 1` con invariante en origen sobreviven todos; sin señal de suite roja.
  - **[ ] RM5**: muestra mía, **#12** (`hmoide or 0 → or 1`), que no traía demostración. Escribí una:
    200.000 llamadas a `decidir_fin` con `partes` construido como en `registro_pipeline.py:472`,
    130.359 entradas con algún CIZ sin parte, 12.899 `mover` ⇒ en todas la elegida trae `hmoide`
    verdadero: **equivalente confirmado**. También corrí el diferencial del implementer (#4, #6,
    #7, #8): 80.000 comparaciones iguales. Pero #11 y #12 no traen demostración y el diferencial
    vive solo en el scratchpad de la sesión. Cambio 4.
  - [x] **RM6**: sin cambios de producción tras la campaña; ninguna guarda quitada.
  - [x] 16 supervivientes analizados: 10 con test nuevo (verificados con el mutante aplicado), 6
    equivalentes **aceptados por el humano** (2026-10-24, «acepto»); 1 timeout (`:191`, detectado).
  - [x] «Evidencias» con los cuatro números y **workers 4**.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T1–T13 y T15 `[x]` con commit `F-060 Tn:`; T14 `[ ]` legítimo (MANUAL) · [x] sin
  artefactos · [x] `features.json` coherente. Desfase: `tasks.md` T13, `current.md:21` e
  `impl_F-060.md:166` siguen con «6 equivalentes PENDIENTES DE ACEPTAR». Cambio 3.

## Puntos críticos pedidos por el líder

- **R22** [x]: ni `DELETE` ni `INSERT` en las líneas añadidas de producción; `stmt_mover_linea` es
  `UPDATE hmores SET …`; una acción `mover` no llega a `stmt_insert_linea` (`continue`) ni lleva
  pisadas (las incidencias que chocan se omiten con `incidencia_en_sigrid`).
- **R21** [x]: `WHERE` con `ide, reside, fec, ISNULL(horide,0), synckey, ISNULL(can,0)=0, NOT
  enlazada` + `UPDLOCK, HOLDLOCK` sobre `hmores.hmoide` (origen) y `?` (destino); los 18 parámetros
  cuadran con el SQL; 0 filas ⇒ relectura de F-034 (R23).
- **R28/R29** [x]: CAS `id = X AND sigrid_estado='registrado' AND sigrid_hmores_ide = :ide` en la
  misma sesión y commit que D; reaplicar no avisa; cadena 2→3→4.
- **Logs** [x]: `ciz_duplicados`, `ciz movido`, `fin_movido_sin_cas` solo con ids, partes y fechas.

**Requisito → nº de tests `test_f060_rN_*`**: R1 4 · R2 5 · R3 8 · R4 4 · R5 2 · R6 6 · R7 8 · R8 2 · R9 14 · R10 12 · R11 3 · R12 2 · R13 12 ·
R14 6 · R15 7 · R16 3 · R17 5 · R18 4 · R19 7 · R20 11 · R21 2 · R22 3 · R23 6 · R24 2 · R25 1 ·
R26 4 · R27 7 · R28 9 · R29 3 · R30 1 · R31 revisión · R32 MANUAL.

**Ejecución**: `bash harness/init.sh` (pasada 1): raíz 498 passed, 3 skipped · sv4 2698 passed, 1 skipped (638 s) ·
sv5 980 passed (14 s) · sv1–sv3 verdes · `PUERTA COBERTURA` 99,7 % · exit 0 (tras recortar este informe).

## Cambios requeridos

1. **`progress/current.md`, F-060**: M1, M2 y M3 con su comando exacto, como la M4 y sin remitir a
   `design.md`: arranque de sv5 en local con `OBRA_PRUEBAS_FORZAR=true` y `MOVER_CIZ=true` (literal),
   pasos en el portal, `python .\prueba_escritura_sigrid.py verificar` (qué `ANO`/`MES` del CONFIG),
   lo esperado tras cada día (M1: CIV el 1; CIZ el 2; el MISMO `ide` con fecha 3 y 4; nada el 5; 2 y 3
   `omitido` `fin_movido`. M2: mismo `ide` de un mes al otro, `verificar` con los dos meses. M3: CIV
   el 1, CIZ el 4, 2 y 3 `intermedio`) y la limpieza (`limpiar` y `limpiar --ejecutar`).
2. **Divergencia de R26**: el líder la lleva al humano y anota su decisión literal en `current.md` y
   `design.md` §7/§11. (A) aceptarla y desplegar sv4 solo cuando se vaya a encender `MOVER_CIZ` (o
   asumir CIZ de más mientras tanto), con un test de caracterización en sv4 con días posteriores
   ingeridos que fije `fin`; o (B) enmendar la spec para que sv4 conserve el `intermedio` cuando la
   racha sigue en días ya ingeridos. En ambos casos, corregir las frases que venden el apagado como
   vuelta atrás completa: `config/settings.py:44-47`, `partes-proyecto.md:546-547`,
   `azure-apps/partes.md:607` (commit local) y la «Vuelta atrás» de la M4.
3. **Papeleo**: «PENDIENTES DE ACEPTAR» ⇒ «aceptados por el humano (2026-10-24, «acepto»)» en
   `tasks.md` T13, `current.md:21` e `impl_F-060.md:166` y su «Pendiente» (T13).
4. **RM5**: versionar las demostraciones de los 6 equivalentes en `progress/` (p. ej.
   `progress/equivalentes_F-060.py`, como `equivalentes_F-045.py`): el diferencial de #4/#6/#7/#8 y
   una para #11 y #12 que ejercite la rama (para #12 vale la invariante de `decidir_fin` de arriba);
   citarlas en `mutacion_F-060.md` en vez del scratchpad.

## Observaciones (no bloquean)

- **Papelera entre días de la racha**: un día con todas sus líneas en la papelera se salta y no entra
  en `racha`, así que su CIZ `registrado` no viaja en `racha_registro_ids` (R9: «de esos días»). Si el
  CIZ estaba ahí, el siguiente `fin` escribe otro. Raro (lo registrado está congelado); que el humano
  diga si «esos días» incluye los saltados.
- El prefiltro SQL por DNI quita `-` y espacios; `persona_de` quita todo blanco (`split()`): un DNI
  con tabulador perdería histórico (saldría `inicio`). Sin casos conocidos.
- R23 con el origen cerrado en carrera da `no_escrita` + ERROR, no `parte_no_abierto` (desviación 4
  del implementer): aceptable.
