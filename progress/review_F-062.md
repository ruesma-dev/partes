<!-- progress/review_F-062.md -->
Revisión incremental desde 2f889c2 (pasada 2) · `git diff 2f889c2..8132f6d` (pasada 1: `a82f9c6...aad629c`)

# Review F-062 · CI* con su CIZ hermano el mismo día del inicio

**Veredicto: APPROVED, CONDICIONADO a que el humano acepte los equivalentes #1, #4 y #5**
(pasada 2 de 2). Hoy esa aceptación **está pendiente** y no la doy por hecha. Mientras no conste
en `progress/` con su texto literal, F-062 **no se marca `done`**: en rigor `critico`, el
checkpoint «cero supervivientes salvo justificación aceptada por el humano» sigue en `[ ]`. Si
el humano rechaza alguno, la decisión vuelve al implementer: matarlo con un test o dejar escrito
por qué no se puede. Todo lo demás está en verde.

**Nivel de rigor: `critico`** (declarado). Exige C1–C5, C3 bis y C4 bis con fase RED,
cobertura ≥ 80 %, mutación con cero supervivientes salvo los que acepte el humano, RM1–RM6 (RM5
incluido) y las verificaciones MANUAL con su comando exacto.

## Pasada 1 (resumen; el texto íntegro está en `git show 2f889c2:progress/review_F-062.md`)

CHANGES_REQUESTED sobre aad629c. El código cumplía la spec R1–R28, y las 8 desviaciones quedaron
aceptadas (la 5, comprobada: una incidencia nunca da conflicto confirmable). RM4 sobre una copia:
los 6 huecos mueren con su test nuevo. Recálculo puro: 425 líneas y 84 mutantes, coherente con
el informe. RM1, RM2, RM3 y RM6 en `[x]`. Campaña no reejecutada: 70 min según el informe. Suites
sin caché: sv5 1164 passed y sv4 2791 passed, 1 skipped. Cambios pedidos:
(1) RM5 sin demostración ejecutable de los 3 equivalentes;
(2) `progress/equivalentes_F-060.py` roto por F-062 (exit 1 en sv4 y sv5);
(3) faltaba el nº de workers en «Evidencias»;
(4) para el líder: la aceptación del humano.

## Pasada 2 · el delta

`git diff --stat 2f889c2..HEAD`: solo `progress/` (`equivalentes_F-060.py`,
`equivalentes_F-062.py` nuevo, `impl_F-062.md`, `mutacion_F-062.md` y `current.md`). **Ni una
línea de `services/` ni de la spec.** El alcance medido y lo aprobado en la pasada 1 siguen
valiendo. Las suites de servicio que `init.sh` tomó de la caché corresponden a ese mismo código,
y ese código lo ejecuté sin caché en la pasada 1.

1. **[x] Cambio 1 · RM5.** `progress/equivalentes_F-062.py` sigue el patrón del de F-060. Lo
   ejecuté yo:
   - **sv4** (`services/partes-front`): «racha_delante: 50000 llamadas, 11726 con tramo, 8279 con
     tramo y alguna fecha None/0/1 · EQUIVALENTE #1 · control `and 0`: distinto · 1 mutantes,
     0 distintos», exit 0.
   - **sv5** (`services/partes-transfer`): «pipeline: 4000 escenarios, 1390 con un CIZ hermano
     escrito, 2190 con alguna línea sin recurso o con recurso 0 · EQUIVALENTE #4 y #5 · controles
     distintos · 2 mutantes, 0 distintos», exit 0.

   **Por qué demuestra de verdad:**
   - Muta el fuente actual con una sustitución única en su ámbito y comprueba `mutado != fuente`.
   - Compara el pipeline completo (`preflight` y `ejecutar`, con la respuesta y el estado final
     de `SigridFake`) con `MOVER_CIZ` encendido. Usa recursos `None`, 0, 1 (con horas propias) y
     REC, y CIZ candidatos del 1, de otro recurso o manuales, para que un `or 1` tuviera dónde
     notarse.
   - Lleva un **control de sensibilidad**: el hermano `and 0` de cada línea tiene que salir
     distinto o el script falla. Así queda probado que la línea se ejercita y que el diferencial
     no es ciego. Es una mejora sobre el de F-060.

   Además, mi diferencial independiente del #1 de la pasada 1 (200.000 llamadas) daba lo mismo:
   0 distintos y control distinto.
2. **[x] Cambio 2 · F-060 reparado sin debilitarlo.** `_mutar` acepta ahora un `ambito`
   opcional, que es la función de nivel superior. Solo lo usa el #6, con `def decidir(`, y exige
   que la cabecera aparezca una vez y que el original aparezca una vez dentro de ella. Los otros
   cinco conservan la exigencia de «una vez en el fichero». El #11 pasa a la primera línea de la
   llamada partida, que sigue siendo única porque la gemela del #4 no empieza por
   `d = decidir_fin(`. Añade `assert mutado != fuente`. Los diferenciales, las semillas y los
   tamaños **no cambian**. Ejecutado por mí:
   - sv4: «4 mutantes, 0 distintos», exit 0.
   - sv5: «invariante #12: 200000 llamadas, … 11467 mover, todas con hmoide verdadero · 2
     mutantes, 0 distintos», exit 0. Son las mismas cifras que dejó la review de F-060, así que la
     prueba no ha perdido cobertura.
3. **[x] Cambio 3.** «Evidencias» dice ahora «4 workers» y 49,8 s por mutante, y añade la fila de
   las demostraciones RM5. Coincide con la fila «Workers» del informe de mutación.
4. **[ ] Cambio 4 (líder): aceptación del humano.** Sigue **pendiente**, como dice el propio
   líder. `mutacion_F-062.md` mantiene «pendiente de aceptación del humano» en los tres, y además
   anota que el #5 es el #11 de F-060, ya aceptado el 2026-10-24.

**Nada roto.** Revisé el diff entero de la pasada:
- `current.md` solo cambia la línea del implementer.
- `impl_F-062.md` quita una frase redundante y actualiza la tabla.
- `mutacion_F-062.md` solo añade las líneas de demostración.
- Las primeras líneas llevan su ruta. Sin secretos.
- `git status` estaba limpio antes de escribir este informe.

## Ejecución (pasada 2)

`bash harness/init.sh` tal cual, con exit 0 y `ENTORNO LISTO`:
- Raíz: 522 passed, 3 skipped.
- sv1–sv5 en verde, desde la caché: árbol de `services/` sin cambios desde el verde.
- `PUERTA COBERTURA` [OK]: 100,0 % (135/135).
- `PUERTA TAMAÑO` [OK]: impl 217/220.
- [AVISO] heredado: `infra` sin comando de tests. No es de esta feature.

## Checkpoints (estado final)

- **C1** [x] `init.sh` exit 0 · [x] ficheros del arnés.
- **C2** [x] Solo F-062 en `in_progress` · [x] rama de la feature · [x] `current.md` con la sesión
  activa. Los bloques de features `done` que siguen ahí tienen verificaciones manuales pendientes,
  que es la práctica del repositorio · [x] `history.md`: no aplica hasta `done`.
- **C3** [x] Hexagonal (obs. O1) · [x] primera línea con la ruta, también en
  `equivalentes_F-062.py` · [x] sin `print` de depuración (los del script son su salida), TODOs,
  secretos ni dependencias · [x] empleado ≠ recurso, incidencias con `can` 0, sin esquema nuevo.
- **C3 bis** [x]. El barrido de la pasada 1 sobre el diff entero (correo, IPv4, GUID,
  `password|secret|token|apikey|AccountKey|SharedAccessSignature|x-functions-key`, DNI) solo
  encontró `$KEY` como variable. La pasada 2 no toca `docs/referencia/`.
- **C4** [x] R1–R26 con `test_f062_rN_*` y en verde; R27 es documentación; R28 está en MANUAL ·
  [x] sin red ni BBDD · [x] M1–M6 con comando exacto en `current.md`; M0 hecha.
- **C4 bis** [x] rigor declarado · [x] fase RED con trazas reales · [x] cobertura [OK] · [x]
  recálculo independiente: 425 líneas y 84 mutantes · [x] campaña no reejecutada (4185 s > 60 s,
  dicho) · [x] coste por mutante 199 s · [x] sin cabecera de campaña no válida · [x] RM1 · [x]
  RM2 · [x] RM3 · **[x] RM5**, reproducido el #1 dos veces y los tres con el script · [x] RM6 ·
  N/A campaña manual (no la hubo) · [x] análisis completos · **[ ] aceptación del humano de #1,
  #4 y #5: es la condición del veredicto** · [x] «Evidencias» con los workers.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] commits `F-062 Tn:` y los de la review 1 · T13 `[ ]` **justificado**: MANUAL del
  humano después del merge, por diseño (§9) · [x] sin temporales · [x] `features.json`
  `in_progress`.

## Para el líder

1. **Condición**: registrar la aceptación literal del humano de #1, #4 y #5 en
   `mutacion_F-062.md`, `impl_F-062.md` y `current.md`, como se hizo en F-060. Hasta entonces, no
   hay `done`.
2. Después del merge: M1–M5 en local, en modo pruebas, **antes** de desplegar sv4. Con
   `MOVER_CIZ` ya encendido, desplegar equivale a activar. Orden: sv5 y luego sv4, y M6 en solo
   lectura.

## Observaciones (no bloquean)

- **O1**. `racha_ciz.py` importa `SUFIJO_CIZ` de `infrastructure`. Hay precedente: `synckey_de`
  se importa así en 4 módulos. Encajaría mejor junto a `PREFIJO_PARTES` en `pisado.py`.
- **O2**. `stmt_insert_inicio_con_fin` no acepta `pisadas`. Es correcto por la desviación 5, pero
  conviene una línea en su docstring que lo explique.

**Automejora (propuesta, no aplicada)**:
- En C4 bis, que el reviewer ejecute los `progress/equivalentes_F-*.py` existentes cuando el
  diff toque sus ficheros. Así se cazó aquí el cambio 2.
- Adoptar el **control de sensibilidad** (`and 0` tiene que salir distinto) como requisito de
  toda demostración RM5.
