# F-048 · Informe del implementer

Rama `feature/F-048-solo-extras-en-laborable-como-jornada` (worktree `partes-wt-f048`),
sobre `dev` dc03468. Rigor **crítico**. Estado: **T1–T10 hechas**. La campaña de mutación (T8) la lanzó el
líder en este worktree: 11 mutantes, **11 muertos, 0 supervivientes**
(`progress/mutacion_F-048.md`). T0
**aplazada**: `dev` no tiene F-046 ni F-047 (ver «Lo que falta»).

## Qué cambió

**sv3 (ingesta)**
- `application/services/parte_normalizer.py`: una fila con `horas_extraordinarias` > 0 es
  «sumable». Sus extras se suman a las ordinarias (`ord_pos += extra_pos`,
  `extra_pos = 0`), así que el reparto por partidas de siempre emite solo registros
  `normal` (primero las ordinarias) y **ningún** registro `extra`. Cada `normal` lleva en
  `horas_extra_leidas` el valor `min(h, acumulado − ordinarias_leídas)` si es > 0, y si
  no `None` (R2). Las filas con extras ≤ 0 o nulas no cambian (R3). El código propuesto es
  siempre `cod_ord` (R4). El INFO `[parte-normalizer]` termina en
  `filas_extra_sumadas=<n> horas_extra_sumadas=<h con 2 decimales>` (R7). Comentarios de
  la cabecera y del bloque reescritos.
- `domain/models/parte_records.py`: `RegistroNormalizado.horas_extra_leidas = None`.
- `infrastructure/database/orm_models.py` (sv3 y sv4, **byte-idénticos**): columna
  `horas_extra_leidas: Float` nula, sin defecto, tras `horas_orig` (R21, R24).
  `ddl_complementario` la añade sola:
  `ALTER TABLE parte_registros ADD COLUMN IF NOT EXISTS horas_extra_leidas FLOAT`.
- `infrastructure/database/sqlalchemy_parte_repository.py`: `save_parte` la guarda (R6).
  `apply_extras_splits` no cambia, así que la `extra_auto` nace con la columna nula.

**sv4 (portal)**
- `infrastructure/database/parte_repository.py`: `RegistroView.horas_extra_leidas`, que
  rellena `_registro_view`. Esa función sirve a las **tres** vistas (parte, obra y
  trabajador). El design decía que el detalle de parte lee el ORM directamente; en
  realidad también pasa por `_registro_view`, así que basta un sitio.
- `templates/parte_detail.html`, `obra_detail.html` y `trabajador_detail.html`: tras las
  etiquetas de método, `<span class="tag-auto" title="La IA leyó estas horas como extra;
  … (F-048)">incl. {{ r.horas_extra_leidas|horas }} extra leídas</span>`, solo si el valor
  es > 0. Usa el filtro `horas` del portal (`5 h`, `2,50 h`) y no añade CSS (R22).
  `update_registro` y `set_registro_hora` no tocan la columna (R23, sin cambio de código).

**Tests existentes que cambian: enmienda de design §5 por decisión del humano** («en
f48 opcion A»). Nueve guardianes fijaban `parte_registros` en 56 columnas. Ahora
`"horas_extra_leidas"` va en `COLUMNAS_PARTE_REGISTROS` tras `"horas_orig"` y las cuentas
pasan de 56 a 57, con mensajes y docstrings. Los nombres de las funciones no cambian; su
docstring explica que conservan la cuenta de su feature. Son:

- en la raíz, `tests/test_f010_orm_models_gemelos.py` (r4, r29 de F-015 y r29 de F-019) y
  `tests/test_f015_r29_guardian_cinco_tablas.py`;
- en sv3, `test_f015_r18_orm_empleado_jornada.py`, `test_f015_r21_hora_candef_intacto.py` y
  `test_f019_orm_bandeja.py`;
- en sv4, `test_f015_r18_orm_empleado_jornada_sv4.py` y `test_f019_bandeja.py`.

El bloqueo listó seis. Al aplicar A salieron tres más: el de `guardian_cinco_tablas` solo
falla cuando la lista crece, y los dos de F-019 no los cazó el `grep` (aserción `== 56`
sin «columnas» en la línea). Llevan el mismo cambio, sin aserciones de comportamiento,
anotado en design §5 y en `progress/current.md`.

**Documentación** (R25): `docs/ARCHITECTURE.md` (semántica 3 y el esquema, 57 columnas) y
`docs/referencia/partes-proyecto.md` (las dos menciones de «Cómputo de extras»).
`azure-apps/partes.md` §3.3 y §4.2, con **commit local `2cf42ec`** en `azure-apps` (solo
`partes.md`, sin push).

**Tests nuevos**: en sv3, `tests/test_f048_esquema.py` (5), `test_f048_normalizer.py` (28,
con la tabla de design §7 entera) y `test_f048_conciliar.py` (23); en sv4,
`tests/test_f048_traza_portal.py` (12). Los cuatro pasan ruff sin avisos.

## Decisiones de diseño

- Se suma **antes** del reparto entre partidas (`rem_ord = total`, `rem_extra = 0`), como
  pide design §3. El cálculo de `horas_extra_leidas` va aparte, por acumulado, y no toca
  el bucle de partidas, así que las filas no sumables siguen exactamente igual.
- La petición literal del humano («por día solo hay una fila de extras y otra de
  ordinarias») tiene su propio test parametrizado:
  `test_f048_r9_r11_exactamente_dos_lineas_una_normal_y_una_extra_auto[caso-1|caso-2|4+2]`.
  Comprueba exactamente 2 líneas activas, una `normal` y una `extra_auto`, y 0 `extra`
  explícitas.
- `features.json` sigue en `in_progress` mientras se espera la mutación: no es un
  bloqueo de spec ni de herramienta.

## Fase RED (trazas reales)

**T1 · R6, R24**: desde `services/partes-persistencia`, antes del código:
`python -m pytest -q --tb=line -p no:cacheprovider tests/test_f048_esquema.py`
```
E   assert 'ALTER TABLE parte_registros ADD COLUMN IF NOT EXISTS horas_extra_leidas FLOAT' in ("ALTER TABLE dedicacion_bandeja ...
E   KeyError: 'horas_extra_leidas'
...test_f048_esquema.py:48: ValueError: 'horas_extra_leidas' is not in list
E   AssertionError: assert 'horas_extra_leidas' in {'line_index': Field(name='line_index',...), ...}
E   TypeError: RegistroNormalizado.__init__() got an unexpected keyword argument 'horas_extra_leidas'
5 failed in 5.56s
```

**T2 · R1–R5, R7**: `python -m pytest -q --tb=line -p no:cacheprovider tests/test_f048_normalizer.py`
```
E   AssertionError: assert [('extra', 10.0, None, None)] == [('normal', 10.0, 10.0, None)]
E   AssertionError: assert [('normal', 4..., None, None)] == [('normal', 9.0, 5.0, None)]
E   AssertionError: assert [('normal', 4..., None, 'P2')] == [('normal', 6...0, 3.0, 'P2')]
E   AssertionError: assert [('extra', 2...., None, 'P2')] == [('normal', 2...0, 4.0, 'P2')]
E   AssertionError: assert {'extra', 'normal'} == {'normal'}
E   AssertionError: assert [('normal', 4..., None, None)] == [('normal', 7.0, 2.5, None)]
18 failed, 10 passed in 0.56s
```
Las 10 que ya pasaban son de caracterización de R3 y R5: filas sin extras positivas y
fila vacía, que no deben cambiar.

**T3 · R8–R18**: los tests de conciliación se ejecutaron con el normalizador
**anterior** (`git show fc3b1f7:…/parte_normalizer.py`, ya con la columna pero sin la
suma) y después se restauró el normalizador:
`python -m pytest -q --tb=line -p no:cacheprovider tests/test_f048_conciliar.py`
```
E   AssertionError: assert [('extra', 10... None, False)] == [('normal', 8..., None, True)]
E   AssertionError: assert [('normal', 8... None, False)] == [('normal', 8..., None, True)]
E   AssertionError: assert 1 == 2
E   AssertionError: assert 3 == 2
E   AssertionError: assert 3 == 2
E   AssertionError: assert [('extra', 6.0, False)] == [('normal', 8..., -2.0, True)]
22 failed, 1 passed in 8.07s
```
Cómo se leen: caso 1, hoy una sola `extra` de 10; los dos `3 == 2`, el caso 2 y el 4+2,
que hoy dejan **tres** líneas. El que pasa es
`test_f048_r3_extra_negativa_leida_sigue_explicita` («lo que no cambia»).

**T4 · R22–R23**: desde `services/partes-front`:
`python -m pytest -q --tb=line -p no:cacheprovider tests/test_f048_traza_portal.py`
```
E   AssertionError: assert [] == ['incl. 5 h e...extra leídas']
E   AssertionError: assert [] == ['incl. 5 h e...extra leídas']
E   AssertionError: assert [] == ['incl. 5 h e...extra leídas']
E   AttributeError: 'RegistroView' object has no attribute 'horas_extra_leidas'
E   KeyError: 'horas_extra_leidas'
5 failed, 7 passed, 1 warning in 16.14s
```
Las 7 que pasaban son el parseo de las plantillas, «sin la columna, nada nuevo», «sin CSS
nuevo» y R23 (las ediciones no la tocan). Son caracterizaciones de lo que no debe cambiar.

## Verificaciones por tarea (resultado real)

- T1: `test_f048_esquema.py` + `test_f010_r6_ddl_complementario.py` ⇒ 20 passed; gemelos
  y guardián de la raíz ⇒ 25 passed; sv4 DDL ⇒ 14 passed; `cmp` de las dos copias del ORM ⇒ idénticas.
- T2: `test_f048_normalizer.py` ⇒ 28 passed; suite completa de sv3 ⇒ 1424 passed.
- T3: `test_f048_conciliar.py test_f045_conciliar.py test_f037_dos_pasadas.py` ⇒ 66 passed,
  **sin tocar el conciliador**.
- T4: `test_f048_traza_portal.py` ⇒ 12 passed.
- T5: `git diff dev --stat` de sv2, sv5, sv1, `infra/`, `static/` de sv4,
  `recurso_conciliador.py`, `reparto_ponderado.py`, `pareja_extra.py`, `jornada_resolver.py`
  (las dos copias) y `congelacion.py` ⇒ **vacío**. Lo mismo `tipo_hora_resolver.py` y
  `persist_parte_pipeline.py`. En `sqlalchemy_parte_repository.py` el único cambio es la
  línea de `save_parte`. Gemelos F-024, F-015 R19 y F-010 ⇒ 78 passed.
- T6: `tests/test_documentos_del_arnes.py` ⇒ 17 passed.
- T7: `git -C azure-apps log -1 --stat` ⇒ solo `partes.md` (13+, 2−).
- T10: `bash harness/init.sh` ⇒ **ENTORNO LISTO** (abajo).

## `bash harness/init.sh` (2026-10-16, en el worktree)

- Raíz: 487 passed, 3 skipped (222 s). sv3: **1447 passed** (65 s). sv4: **2080 passed,
  1 skipped** (1463 s). sv1, sv2 y sv5 en verde por caché (árbol sin cambios).
- `PUERTA COBERTURA: 100.0% de 16 líneas cambiadas cubiertas (16/16, umbral 80%, nivel critico)`.
- `PUERTA TAMAÑO`: dentro de los topes. Rama correcta.
- Avisos previos, ajenos a F-048: F-014 y F-032 `blocked`, 700 avisos de ruff de deuda
  previa, e `infra` sin tests. El normalizador tiene los mismos 2 avisos de ruff que en
  `dev` (I001 y C408, previos).
- Nota: init.sh se lanzó una vez con la salida redirigida a un fichero del scratchpad
  para poder leerla; el comando fue el de siempre.

## Lo que falta y fuera de alcance

- **Mutación (T8)**: hecha, lanzada por el líder el 2026-10-16 con
  `python -m harness.mutacion --feature F-048 --workers 6` (HEAD medido `8b616b3`).
  Resultado: 11 mutantes, 11 muertos, 0 supervivientes y 0 timeouts, así que no hay
  ningún superviviente que analizar. Detalle en `progress/mutacion_F-048.md`.
- **T0 / fusión con F-046 y F-047**: hay conflictos previstos en las dos copias de
  `orm_models.py` (F-046 añade una tabla y puede tocar `TABLAS` del guardián) y en
  `save_parte` (F-047 cambia la firma; F-048 solo añade un argumento al constructor de
  `ParteRegistroOrm`). Se resuelven al fusionar y hay que volver a pasar init.sh.
- **MANUAL (humano)**: M1–M5 de design §9, anotadas en `progress/current.md`. El
  despliegue de sv3 y sv4 lo pide el humano.
- Fuera de alcance (DA6): no se tratan las líneas ya guardadas. Tampoco los casos reales
  del 15/10 (0678) y del 02/10 (0686, ya en Sigrid): requieren una feature aparte sobre F-046.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | raíz 487 ok / 3 skip; sv3 1447 ok; sv4 2080 ok / 1 skip (init.sh); nuevos de F-048: 68 (5 + 28 + 23 + 12) |
| Cobertura de líneas cambiadas | **100,0 %** (16/16), puerta de init.sh, umbral 80 % |
| Mutantes generados / supervivientes | **11 generados, 11 muertos, 0 supervivientes, 0 timeouts** (`progress/mutacion_F-048.md`; 6 workers, timeout por mutante 120 s, 235,4 s en total; HEAD medido `8b616b3`) |
| Tiempo de las suites | raíz 222 s; sv3 65 s; sv4 1463 s |
