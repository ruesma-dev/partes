<!-- progress/spec_F-085.md -->
# F-085 · spec escrita (spec-author, 2026-11-27)

Rama `feature/F-085-codigo-de-incidencia-convierte-la-linea`, copia `partes-wt-f085`, base `dev`
0a77900. Ficheros: `specs/F-085-codigo-de-incidencia-convierte-la-linea/` (requirements 144/150,
design 248/250, tasks 18 tareas). `python -m harness.tamano --feature F-085` dentro de los topes.
No se tocó código, ni `status` de `features.json`, ni producción.

## Qué propone

- **Parte A (R1–R20)**, sv4 + sv3 + sv5: elegir un CI* con letra en `config/incidencias.yaml`
  convierte la línea en incidencia con la forma canónica (letra en `tipo_hora` e
  `incidencia_codigo`, horas y `horas_orig` nulos); de incidencia a un código de horas vuelve atrás
  con horas vacías; CIZ y CI* sin letra ⇒ 400. Deshacer completo (`registro_clase`), recálculo
  compartido (sv3 retira la extra automática no congelada) y recarga de la página. sv3 no pisa
  `hora_match_method = manual`. sv5 omite una línea de horas con código CI*
  (`MOTIVO_CODIGO_INCIDENCIA`) en vez de escribir HLOF.
- **Parte B (R21–R32)**, sv5 + sv4, tras `MOVER_INICIO` (nuevo, apagado): un `inicio` aprobado el
  día antes de un inicio ya registrado de la misma racha mueve ese CI* con `UPDATE`
  (`stmt_mover_linea`, como el CIZ) en vez de escribir otro; el día que era inicio queda
  `omitido · inicio_movido`. Solo se mueve si en Sigrid hay un CIZ detrás (D9): así el caso espejo
  de F-083 (CIZ cambiado a mano a CIV) no se toca.
- **Reparación del caso 0678 (M4)**: Administración edita en Sigrid la 416574 (HLOF 8 h ⇒ CIA 0 h,
  sin borrar); con OK expreso del humano, `UPDATE` puntual de la 25012 en `partes`; ↻ de la 25096
  y aprobar la 25405 (salen intermedias por el CIZ del 25). Antes, M0 debe confirmar que la synckey
  del CIZ 416563 es de una línea de esa racha; si no, PARA.

## Hallazgos que no estaban en el encargo

- sv3 restaura `horas = horas_orig` en toda fila no congelada con `horas_orig`
  (`sqlalchemy_parte_repository.py` ≈583): una base partida y luego convertida recuperaría sus 10
  h. Por eso la conversión pone `horas_orig` a nulo y deshacer lo guarda.
- `fetch_registros_para_recurso` de sv3 no trae `hora_match_method`: hace falta para R15.
- F-081 R3 («mismo tipo que el que tiene») daría por ordinaria un CI* (F-066 no lo distingue):
  F-081 escribiría una CIA con horas. Propuesta D14: enmendar F-081 con las funciones de R1.
- En los tests de F-066 hay incidencias con `tipo_hora` normal/extra; `test_f066_r14` se enmienda.

## Decisiones abiertas para el humano

D1–D15 en `design.md` §12, «Decidido» vacío. Las de más peso: **D1** (partir en dos: A arregla el
caso de origen sola; B estrena escrituras de CI*), **D9** (qué CI* se mueve), **D12**
(interruptor `MOVER_INICIO`), **D13** (el guardado por cada paso del campo de horas, fuera) y
**D15** (cómo se repara el 0678). Verificaciones manuales M0–M5 con su comando en `design.md` §8.
