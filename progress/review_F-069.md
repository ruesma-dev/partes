<!-- progress/review_F-069.md -->
Revisión completa (pasada 1) · `git diff 0a91941..b938d38` (base = spec aprobada; 20 ficheros)

# Review F-069 · sv3: extras automáticas con ids estables y recálculo en una sola transacción

**Veredicto: APPROVED** (pasada 1). Para pasar a `done` (no depende del implementer), el humano tiene que **aceptar el mutante equivalente n.º 10** (rigor crítico; abajo explico por qué
recomiendo aceptarlo). M2 queda definida y pendiente del líder tras desplegar sv3, como estaba
previsto. Cuatro observaciones, ninguna bloqueante.

**Nivel de rigor: `critico`** (declarado): RED, cobertura ≥ 80 %, mutación completa sin
supervivientes salvo equivalente aceptado por el humano, RM1–RM6.

## Verificación que ejecuté yo

- `bash harness/init.sh` tal cual: **ENTORNO LISTO**, exit 0; raíz 544 passed / 3 skipped;
  `PUERTA COBERTURA` [OK] 100,0 % (211/211); `PUERTA TAMAÑO` OK; avisos previos (F-032, ruff, infra).
- sv3 y sv4 venían de caché; a mano con `python -m pytest -q -p no:cacheprovider`: **sv3 2453
  passed, 2 skipped** (M1 sin `F069_PG_URL`); **sv4 3751 passed, 1 skipped** (330 s).
- Guardianes de gemelos (f010 orm, f024 congelación, f023, f036, f015 r19): **114 passed**. El diff
  no toca `orm_models.py` (ninguno) ni `congelacion.py`, ni menciona `esta_congelado`/`ESTADOS_CONGELADOS`.
- **M1 reproducida por mí** en Docker `postgres:16` (contenedor propio, contraseña aleatoria en
  memoria, parado al final): **2 passed** (20 pasadas sin violaciones, secuencia quieta, `UPDATE`
  bloqueado hasta `lock_timeout`). Árbol limpio después.

## Mutación (C4 bis, RM1–RM6)

- Recálculo puro (`alcance_de_feature("F-069", base="0a91941")` + `generar_mutantes`): **5 ficheros,
  466 líneas, 72 mutantes** (3 + 2 + 8 + 0 + 59), igual que el informe. Los supervivientes
  1, 2, 10 y 11 existen con el mismo operador y el mismo texto original→mutado.
- «Tiempo total» 3806,6 s > 60 s ⇒ **campaña no reejecutada (63 min según el informe)**.
- **RM1**: SHA medido `bae6363`. Desde ahí hasta HEAD solo cambian `progress/*`, `tasks.md` y
  `tests/test_f069_mutacion.py`: ningún fichero del alcance. La medición vale.
- **RM2**: líneas base de 65–70 s (sv3) y unos 1050 s (sv4); media de 52,9 s por mutante;
  72 × 52,9 ≈ 3809 s, que cuadra con el total. No hay ningún salto de orden de magnitud. Sin
  cabecera «CAMPAÑA NO VÁLIDA», «Sin veredicto (base rota)» = 0 y línea base declarada.
- **RM3**: ningún muerto sospechoso de equivalencia; los 10 supervivientes cambian algo observable.
- **RM4**, sobre una copia de sv3 en mi scratchpad y con `sys.executable -m pytest`:
  `test_f069_mutacion.py` sin mutar ⇒ 6 passed. Con los mutantes n.º 1 (`round(...,7)`), 2
  (`LOTE_IN = 1001`), 3 (`frozen=False`), 8 (`borradas = 1`) y 11 (`!= "postgresql"`), cada uno
  da **1 failed** (el 11, 2 failed). Cinco de los diez «cazados» confirmados.
- **RM5, el equivalente n.º 10** (`zip(..., strict=True→False)` en `leer_pasada`). Lo reproduje:
  la suite entera de sv3 en la copia da **2 failed / 2451 passed con el mutante y lo mismo sin él**.
  Esos 2 fallos son de la copia: dos tests de gemelos leen ficheros de sv4, que no copié. Por
  construcción, `vista` y `quedan` salen de las mismas filas crudas menos los mismos ids de
  `plan.borrar`, en el mismo orden, así que las dos listas siempre miden lo mismo. **Lo doy por
  equivalente y recomiendo al humano aceptarlo.**
- **RM6**: no se quitó ninguna guarda; los diez se mataron con tests nuevos.

## Los puntos que pidió el líder

1. **Gemelos intactos**: confirmado arriba (diff vacío en esos ficheros, 114 passed).
2. **`FOR UPDATE` y rollback**: `escribir_pasada` = una sesión, `_escribir`, `commit`; si algo
   lanza, `rollback` y se relanza, y `_log_plan_revert` solo corre tras el commit.
   `test_f069_r16_*` (un split roto detrás de uno bueno: la foto no cambia) y `r8_*_unico_commit`
   lo vigilan; M1 R15 demuestra el bloqueo en PostgreSQL (por documento y por `id`, DA6).
3. **Pareja editada por sv4**: `test_f069_r13_pareja_cambiada_no_se_toca` cubre 13 cambios; la
   pareja queda como la dejó sv4, la otra se escribe, sale un WARNING por clave y no aparece el DNI
   sintético en el log. Lo que pasa después del bloqueo, en O1.
4. **422 sin inexistentes**: igualdad exacta del JSON contra `TEXTO_DE_HOY`, que coincide con el
   literal de `0a91941:app.py:2532-2535`. Sin ids fuera no se consulta nada (R21).
5. **Mutación y M1 reales**: secciones anteriores.

## Desviaciones del implementer

- **D1** (`fetch_registros_para_recurso` conserva su cuerpo y `leer_pasada` se construye encima, en
  vez de lo contrario): **justificada**. El design §4.1 y la T4 lo pedían al revés, pero así se
  rompía el contrato crudo que usan `test_f037_r9_*` y `test_f003_r26_*` (R18). Además, R11 se prueba
  sin circularidad. No cambia ningún requisito, así que no hace falta volver a la spec.
- **D2** (el plan sale solo de las filas con `extra_auto` o `horas_orig`, como hace hoy
  `revert_extras_auto`): **justificada y necesaria**. Es justo lo que exige R11, y la variante p4
  de `f069_comun.py` lo demuestra.
- **D3** (`tests/f069_comun.py`): trivial, correcta.
- Comparar huellas solo en los partes que aparecen a la vez en la lectura y en el bloqueo es una
  consecuencia directa de R13, no una desviación.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base presentes.
- **C2** [x] una sola `in_progress` (F-069) · [x] rama `feature/F-069-extras-ids-estables`.
  [x] `current.md` describe F-069. El bloque de F-066 que sigue ahí ya venía de `dev` y lo
  mantiene el líder (O4) · [x] el `history.md` de las `done` no cambia.
- **C3** [x] hexagonal: el núcleo puro va en `application/services/pareja_extra.py`, sin imports de
  infraestructura, y SQL y bloqueo en `infrastructure/` · [x] primera línea con ruta en los 8
  ficheros nuevos · [x] sin `print`, sin TODO y sin secretos: la URL de M1 lleva `<local>` ·
  [x] trampas de dominio: no toca recurso/empleado ni incidencias, y el esquema queda igual en
  sv3 y sv4.
- **C3 bis** N/A: la feature no trae ningún documento de fuera.
- **C4** [x] trazabilidad (tabla abajo) · [x] los unit tests van en SQLite en memoria; M1 se salta
  sin `F069_PG_URL` · [x] MANUAL listadas: M1 hecha (y reproducida por mí), M2 definida en
  `requirements.md` y en T18.
- **C4 bis** [x] rigor declarado `critico` · [x] RED con trazas reales por tarea, incluida la de M1
  contra la base (5170 lecturas de «pareja a medias») · [x] cobertura al 100 % · [x] informe de
  mutación completo, sin `PENDIENTE` · [x] muertos comprobados con recálculo y RM4 sobre 5 de los
  10 · [x] tiempo coherente · [x] sin cabecera inválida · [x] RM1 · [x] RM2 · [x] RM5: muestra del
  único equivalente, reproducida · [x] RM6: N/A de hecho, no se quitó código defensivo ·
  [x] la campaña es automática, no manual · [x] cada superviviente tiene su análisis ·
  [x] «Evidencias» con los cuatro números · [x] ningún N/A sin motivo.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`, solo el ejemplo.
- **C5** [x] T1–T17 y T19 en `[x]`, cada una con su commit `F-069 Tn:`. T18 es la M2 manual y
  posterior al despliegue, abierta a propósito · [x] sin artefactos sin trackear ·
  [x] `features.json` en `in_progress`, que es el estado real.

## Cobertura requisito → test (sv3 `tests/`, sv4 `services/partes-front/tests/`)

| Req. | Test(s) |
|---|---|
| R1-R6 | `test_f069_ids_estables` (r1×2, r2×2, r3×3, r4×4, r5, r6), puros `test_f069_pareja_puro` (r2-r5), `test_f069_mutacion::r6_*`, M1 (secuencia) |
| R7-R11 | `test_f069_una_transaccion` (r7, r8×2, r9 invariante por commit, r10 sin red, r11×2), puros r7/r11, `mutacion::r8_lotes_de_1000`, M1 lector; dorados F-003 R15 / F-045 sin tocar |
| R12, R19 | `test_f046_r18_la_pasada_entera_va_bajo_el_candado` (orden), suite F-046 |
| R13-R14 | `test_f069_concurrencia_sv4` (13 cambios parametrizados + 4 de control + r14), puros de huella, `mutacion::r13_septimo_decimal` |
| R15-R16 | M1 `test_f069_m1_r15_*`, `mutacion::r15_for_update_solo_en_postgresql`, `test_f069_r16_*` |
| R17-R18 | guardianes de gemelos (114 passed), suite F-037, `test_f069_r18_*` ×2, F-015 R31 |
| R20-R21 | sv4 `test_f069_r20_inexistentes` (r20×4 con endpoints, r21×3) |

## Observaciones (no bloquean)

- **O1 · Lo que el bloqueo no cubre.** `FOR UPDATE OF parte_registros` bloquea filas que ya
  existen. No bloquea un `INSERT` de sv4 en la pareja (`parte_repository.py:1935`, `:2075`) ni el
  `approved` de `parte_documents` (`:4671`) si llegan entre la comprobación de huellas y el commit.
  La ventana es de milisegundos, y `_exigir_sin_recalculo` (F-043) ya frena las ediciones de un
  parte en recálculo. En cualquier caso, el resultado es una pareja completa, nunca a medias. R15
  se cumple en su letra. Si M2 enseña `parejas_cambiadas` > 0 a menudo, conviene valorar
  `FOR UPDATE OF parte_documents`.
- **O2** `_PISA` duplicada (clase y local de `apply_recurso_matches`, la misma tupla): que la
  local use la de clase en la próxima feature que toque el repositorio. **O3** Las extras
  explícitas no entran en la huella (alcance de `CAMPOS_HUELLA` en la spec): un cambio de sv4 en
  ellas durante la pasada lo corrige la siguiente. **O4** `current.md` conserva el cierre de F-066,
  que viene de `dev`: el líder lo pasa a `history.md`. Hallazgo del implementer, fuera de alcance:
  la `extra_auto` negativa en laborable (F-045 DA6) merece entrada en el backlog si no la tiene.

## Cambios requeridos

Ninguno. Para cerrar: el humano acepta el equivalente n.º 10; M2 del líder tras desplegar.

## Automejora (propuesta, no aplicada)

En RM4, el protocolo debería decir que la copia del scratchpad tiene que incluir **también los
servicios gemelos** (o comparar siempre contra la línea base de esa misma copia). Aquí, dos tests
de gemelos de sv3 leen ficheros de sv4 y fallaban en la copia con mutante y sin él. Sin la línea
base, eso parecería un «MATA» falso del equivalente.
