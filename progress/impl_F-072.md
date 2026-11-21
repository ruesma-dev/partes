# F-072 · Informe del implementer (`critico`), PARCIAL: feature `blocked` en T16

> Informe a medias, escrito al bloquear para no perder las trazas RED. El motivo y las opciones
> están en `progress/current.md` («F-072 · BLOCKED 2026-11-21»). Se completará al retomar.

## Estado

- **Hechas y commiteadas, T1–T15**: de `f49c474` (T1) a `f4ea30d` (T15), en la rama
  `feature/F-072-postventa-var-como-obras`.
- **Pendientes**: T16–T27 y T32.
- **Para el líder y el humano**: T28 (mutación) y T29–T31 (manuales).

## Ficheros tocados (hasta T15)

- Gemelo `application/services/obras_agrupadas.py`, byte-idéntico en sv2, sv3, sv4 y sv5. Sus
  tests:
  - `services/partes-persistencia/tests/test_f072_obras_agrupadas.py`;
  - `tests/test_f072_obras_agrupadas_gemelos.py` (R11);
  - `tests/test_f072_equivalencia_porcentajes.py` (R10).
- Los cuatro `config/settings.py`, con R1 y R2, y sus `tests/test_f072_settings.py`.
- **sv2**: `obra_sigrid.py` (`marcas`), `app.py`, `prompts.yaml` y `tests/test_f072_marca_sv2.py`.
- **sv3**, con los tests `tests/f072_comun.py` y `test_f072_{entrada_agrupada,pipeline,conciliacion}.py`:
  - `entrada_agrupada.py` (nuevo);
  - `obra_matcher.py`, `parte_records.py`, `persist_parte_pipeline.py`;
  - `sqlalchemy_parte_repository.py`, `partida_conciliador.py`, `app.py`.
- **sv5**, con los tests `tests/f072_comun.py` y `tests/test_f072_guarda.py`:
  - `registro_models.py`: `partida_metodo`, `PartidaHoja` y `LineaSigrid.paride`;
  - `sigrid_write_client.py`: `partidas_de_obra`;
  - `reglas_registro.py`: `motivo_partida_agrupada`;
  - `registro_pipeline.py`: paso 2d y `_obra_agrupada`.

## Decisiones e interpretaciones

Las mismas seis de `progress/current.md`, de la (i) a la (vi). La (iv) es una desviación
justificada: el reemplazo del mismo día de `save_parte` cuenta también la entrada.

## Fase RED (trazas reales)

Cada comando es el de la columna «Verificación» de su tarea en `tasks.md`. Se lanzó antes de
escribir el código, desde la carpeta del servicio y con `python -m pytest <fichero> -q`.

- **T1**, `tests/test_f072_obras_agrupadas.py` (sv3):
  `E   ModuleNotFoundError: No module named 'application.services.obras_agrupadas'` ·
  `1 error in 0.37s`.
- **T2**: la traza guardada no vale. Recogió un error de colección ajeno (`test_f077_cliente_hr.py`),
  así que no se aporta como RED. T2 es la implementación de T1, y su RED es la de T1.
- **T4**, `tests/test_f072_settings.py`:
  - `8 × Failed: DID NOT RAISE ValidationError`;
  - `7 × AttributeError: 'Settings' object has no attribute 'obras_agrupadas'`;
  - `15 failed in 1.63s`.
- **T6**, `tests/test_f072_marca_sv2.py` (sv2):
  - `15 × TypeError: ComprobadorObra.__init__() got an unexpected keyword argument 'marcas'`;
  - `assert 'separador' in 'el "nº obra" tal cual (p.ej. "672").'`, y lo mismo con `posicion`,
    `no quites` y `no expandas`.
- **T8**, `tests/test_f072_entrada_agrupada.py` (sv3):
  `E   ImportError: cannot import name 'entrada_agrupada' from 'application.services'` ·
  `1 error in 0.37s`.
- **T10**, `tests/test_f072_pipeline.py` (sv3):
  - primero `E   ImportError: cannot import name 'EntradaPartida' from 'domain.models.parte_records'`;
  - con el dataclass, `29 × TypeError: PersistPartePipeline.__init__() got an unexpected keyword
    argument 'entradas'` · `29 failed, 1 passed in 2.31s`.
- **T12**, `tests/test_f072_conciliacion.py` (sv3):
  - `4 × TypeError: PartidaConciliador.__init__() got an unexpected keyword argument 'ajustes'`;
  - `1 × KeyError: 'obra_codigo'`;
  - `5 failed, 3 passed in 1.82s`.
- **T14**, `tests/test_f072_guarda.py` (sv5):
  `E   ImportError: cannot import name 'MOTIVO_PARTIDA_AGRUPADA' from
  'application.services.reglas_registro'` · `1 error in 0.52s`.

## Salida de los tests (hasta T15)

| Suite | Resultado |
|---|---|
| sv5, completa | 1665 passed in 10.39s, con `tests/test_f072_guarda.py` 22/22 |
| sv3 | 2943 passed, 2 skipped |
| sv2 | 465 passed |
| Raíz `test_f038_lectores_sigrid.py` | 24 passed |

`bash harness/init.sh` todavía **no se ha ejecutado al cierre**: la feature está `blocked`.

## Verificaciones MANUAL pendientes

Son T29–T31, del humano. Sus comandos se completan al retomar.

## Evidencias

PENDIENTE: la feature está `blocked`. Se rellena al terminar T32. La campaña de mutación (T28) la
lanza el líder.
