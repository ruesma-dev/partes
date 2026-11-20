# F-078 · Informe del implementer (`express`)

## Hecho
sv3 reconoce el membrete «Dorsan S.L. E HIJOS CONSTRUCCIONES» (lectura errónea del OCR
en partes de Porsan de la obra 0730, 11-13/11/2026) como la empresa 28. Es un cambio
de configuración: se añade el alias `DORSAN` a la 28 en la tabla de F-023, con su motivo.
No cambia código de producción.

## Ficheros
- `services/partes-persistencia/config/empresas_membrete.yaml`: alias `DORSAN` en la 28,
  con su comentario.
- `services/partes-persistencia/tests/test_f078_alias_dorsan.py` (nuevo): usa el
  `ResolutorEmpresa` real con la tabla real del YAML (`parsear_alias`), igual que F-029.
- `tests/test_f023_empresa_membrete.py` y `tests/test_f023_wiring_sv3.py`: fijan la tabla
  entera. Se actualizan a `28: ["PORSAN", "DORSAN"]`, como hizo F-029. Es una consecuencia obligada.

Commits: `1243867` (YAML, test nuevo y test_f023_empresa_membrete) y `e284816` (wiring).

## Tests por `acceptance`
- «Dorsan S.L. E HIJOS CONSTRUCCIONES» da la 28: `test_f078_dorsan_y_porsan_son_la_empresa_28`.
- «Porsan S.L. E HIJOS CONSTRUCCIONES» y «PORSAN E HIJOS CONSTRUCCIONES, S.L.» siguen dando la
  28: el mismo test, parametrizado.
- El alias no choca con la empresa 1:
  - `test_f078_dorsan_no_es_alias_de_la_empresa_1`: DORSAN está en la 28 y no en la 1.
  - `test_f078_ruesma_sigue_siendo_la_empresa_1`: «ruΞsma» y «Construcciones Ruesma S.A.»
    siguen dando la 1.
  - `test_f078_ruesma_con_dorsan_da_varias`: con las dos marcas en el texto sale `varias`.
- Suite de sv3 completa: 2739 passed, 2 skipped (21,5 s).

## Salida de `init.sh`
- Pasada 1: ROJO por la tabla fijada en `test_f023_wiring_sv3.py`. Arreglado en `e284816`.
- Pasada 2: ROJO por `tests/test_f019_prueba_de_verdad.py::test_f019_r30_…`. Agotó su plazo
  (`la medición del mapa expiró a los 2400 s`) en una ejecución de 15 h, probablemente con el equipo
  suspendido. No es de F-078: había pasado en la pasada 1 y vuelve a pasar en la 3.
- Pasada 3: VERDE (EXIT 0). Raíz: 2537 passed, 48 skipped. sv3 en verde (2739 passed).
  `PUERTA CARRIL: dentro de los límites (1/3 ficheros, 4/150 líneas)`.
  `PUERTA COBERTURA: N/A (no cambia líneas Python de producción)`.

## Pendiente
Redesplegar sv3 (lo hace el humano). Los partes ya guardados se corrigen desde el portal.
