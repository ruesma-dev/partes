<!-- progress/impl_F-082.md -->
# F-082 · Informe del implementer (`estandar`)

Rama `feature/F-082-opcion-sin-partida`, copia `partes-wt-f082`. Sin spec (sdd=false):
mandan la descripción y los `acceptance` de `harness/features.json` y la PARADA 1
aprobada el 2026-11-26.

## Hecho

- **Selector de partida** (`buildPartidaPicker`, el que usan el ✎ de la celda,
  `wirePartidaEdit`, y «Editar partida» de la barra de selección, `wireBulkSelect`):
  fila fija «— Sin partida —» justo debajo de los chips, **siempre** visible (con texto
  que no casa nada, con chip CD/CI y en una obra sin presupuesto). Elegirla llama a
  `onPick({ide: null, cod: null, res: null, capitulo: null})`; `applyPartidaToIds`
  manda los cuatro campos a null al PATCH `/api/registros/{id}/partida`, que ya lo
  admitía (`set_registro_partida` deja `partida_match_method='manual'` y registra undo).
- En una obra sin partidas el panel dice ahora «Esta obra no tiene partidas» (antes,
  al abrirlo, «Sin partidas con ese filtro», que confundía); con partidas y filtro sin
  coincidencias sigue «Sin partidas con ese filtro».
- **Celda `cell-partida`** de `obra_detail.html`, `parte_detail.html` y
  `trabajador_detail.html`: sin partida y método `manual` ⇒ «sin partida» + etiqueta
  `tag-manual` («manual»), sin ⚠ (ni «⚠ X no encontrada» ni «⚠ sin partida»). Resto de
  casos idénticos.
- D3: elegir «Sin partida» en una línea ya sin partida manda el mismo PATCH (queda
  `manual` y desaparece el aviso). No hay lógica especial: es el mismo camino.

## Ficheros

- `services/partes-front/static/app.js`: `buildPartidaPicker`, `show()` (+13 líneas).
- `services/partes-front/templates/obra_detail.html`, `parte_detail.html`,
  `trabajador_detail.html`: rama `manual` en el `else` de la celda (1 línea cada una).
- `services/partes-front/tests/test_f082_sin_partida.py` (nuevo, 13 tests).
- `progress/current.md`, este informe.

Sin cambios de backend (no hicieron falta), ni de CSS (la fila usa `combo-option`;
lleva además `combo-sin-partida` sin regla propia), ni de `features.json`.

## Decisiones de diseño

- La fila va **fuera** de `filtrados()`: no depende del texto ni del chip, así el
  requisito «siempre» no se puede romper con un filtro.
- La partida vacía se construye en el propio `mousedown` (objeto literal nuevo cada
  vez), sin constante global.
- Los tests del JS **ejecutan** el código real en node (funciones `plabel`,
  `applyPartidaToIds` y `buildPartidaPicker` extraídas de `app.js`) sobre un DOM
  mínimo, patrón de `test_f064_filtros_js.py`. Los de plantilla renderizan con Jinja2
  la celda `<td class="cell-partida">…</td>` real de cada plantilla.

## Tests por `acceptance`

| Criterio | Tests |
|---|---|
| A1 Los dos selectores ofrecen «— Sin partida —», también sin presupuesto | `test_f082_a1_con_partidas_ofrece_sin_partida_primero`, `_texto_sin_coincidencias_mantiene_la_fila`, `_chip_mantiene_la_fila`, `_obra_sin_presupuesto_ofrece_sin_partida`, `_los_dos_selectores_usan_el_picker` |
| A2 Elegirla deja la línea sin partida y sin aviso | `test_f082_a2_elegir_sin_partida_manda_todo_null`, `_partida_normal_sin_cambios`, `_sin_partida_manual_sin_aviso[×3 plantillas]`, `_resto_de_casos_sin_cambios[×3]` |
| A3 init.sh en verde y APPROVED | init.sh abajo; el APPROVED es del reviewer |

## Fase RED

Tests escritos y commiteados antes del código (T1, 2f033d9). Comando y salida real:

```
cd services/partes-front && python -m pytest tests/test_f082_sin_partida.py -q -rf
E       AssertionError: assert '[CD] P1 · Encofrado' == '— Sin partida —'
E       AssertionError: assert [] == ['— Sin partida —']
E       AssertionError: assert ['[CI] P2 · Gastos generales'] == ['— Sin parti...os generales']
E       AssertionError: assert [] == ['— Sin partida —']
E       assert None is not None
E           assert '⚠' not in '<td class=".../span> </td>'
E           assert '⚠' not in '<td class=".../span> </td>'
E           assert '⚠' not in '<td class=".../span> </td>'
FAILED tests/test_f082_sin_partida.py::test_f082_a1_con_partidas_ofrece_sin_partida_primero
FAILED tests/test_f082_sin_partida.py::test_f082_a1_texto_sin_coincidencias_mantiene_la_fila
FAILED tests/test_f082_sin_partida.py::test_f082_a1_chip_mantiene_la_fila - A...
FAILED tests/test_f082_sin_partida.py::test_f082_a1_obra_sin_presupuesto_ofrece_sin_partida
FAILED tests/test_f082_sin_partida.py::test_f082_a2_elegir_sin_partida_manda_todo_null
FAILED tests/test_f082_sin_partida.py::test_f082_a2_sin_partida_manual_sin_aviso[obra_detail.html]
FAILED tests/test_f082_sin_partida.py::test_f082_a2_sin_partida_manual_sin_aviso[parte_detail.html]
FAILED tests/test_f082_sin_partida.py::test_f082_a2_sin_partida_manual_sin_aviso[trabajador_detail.html]
8 failed, 5 passed in 0.67s
```

Los 5 que pasaban en rojo son los de «sin cambios» (regresión) y el de cableado de los
dos selectores, que vigilan lo que ya existía. Tras T2 (55a892c), el mismo comando:
`13 passed in 0.44s` (incluye la aserción añadida en T2 del texto «Esta obra no tiene
partidas»). `node --check static/app.js`: sin errores.

## Salida de `init.sh`

`bash harness/init.sh` en la copia, exit 0, «ENTORNO LISTO» (2026-11-26):

- raíz: `2549 passed, 50 skipped in 904.16s`; sv4-front: `4030 passed, 1 skipped in 892.74s`;
  sv5: `1890 passed, 1 skipped in 39.78s`; sv1, sv2, sv3: verdes por caché (sin cambios).
- `PUERTA COBERTURA: N/A (F-082 no cambia líneas Python de producción frente a dev)`
- `PUERTA TAMAÑO: F-082 dentro de los topes`
- `PUERTA CARRIL: N/A (F-082 es de nivel estandar: no declara límites)`
- `CAPA E2E: N/A (ningún servicio declara el bloque e2e)`
- AVISOS previos, no bloquean: ruff 1181 (deuda previa) e infra sin `comando_tests`.

## Verificaciones MANUAL pendientes (navegador, Ctrl+F5)

1. En una obra con presupuesto, ✎ de una línea ⇒ la primera fila es «— Sin partida —»;
   elegirla recarga con la celda «sin partida · manual», sin ⚠.
2. Seleccionar varias líneas ⇒ «Editar partida» ⇒ la fila sale igual y se aplica a todas.
3. Obra sin presupuesto: el panel ofrece «— Sin partida —» y «Esta obra no tiene partidas».
4. «Deshacer» devuelve la partida anterior.
No las he podido hacer: no arranco el portal contra la base `partes`.

## Fuera de alcance

- El combo `_partidaCombo` de «Nuevo parte».
- Líneas registradas/congeladas: siguen con candado y 409 de F-004 (F-081).
- Entradas de F-072: el backend sigue devolviendo `PartidaFijaError`; no se ha tocado.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de F-082 | 13 passed (8 en rojo en la fase RED) |
| Suite sv4-front | 4030 passed, 1 skipped (incluye los 13) |
| Suites totales en `init.sh` | raíz 2549 + sv4 4030 + sv5 1890 passed; sv1–sv3 por caché |
| Cobertura de líneas cambiadas | N/A: el cambio es JS y Jinja2, sin líneas Python de producción (`PUERTA COBERTURA: N/A`). El JS tocado se ejecuta entero en los tests de node (fila nueva, su `mousedown` y las dos ramas del texto vacío) |
| Mutantes | no lanzada por encargo del líder (carril `estandar`); la herramienta solo muta Python y aquí no hay Python de producción |
| Tiempo de la suite | sv4 892,74 s; raíz 904,16 s; sv5 39,78 s; `test_f082_sin_partida.py` 0,44 s |
| Capa e2e | N/A (`CAPA E2E: N/A`) |
