<!-- progress/review_F-004.md -->
# F-004 · Congelar registros aprobados — Review

- **Veredicto: APPROVED**
- Rama `feature/F-004-congelar-aprobados`, HEAD `c27dc04`. Base del diff de
  la feature: **`9772ba4`** (punta de F-013 + el commit de `in_progress`),
  la misma que declara el implementer. Medir contra `dev` arrastraría F-003
  y F-013, que aún no están integradas.
- Fecha: 2026-08-18. Sin `git push`, sin PR, sin tocar `dev` ni `main`.
- Commits AJENOS intercalados en la rama, excluidos del juicio: `f83cde8`,
  `c13b524`, `765cab8` (spec F-012) y `093ee41` (F-014 al backlog).
  Verificado commit a commit: **ninguno de los 18 commits `F-004 ...` toca
  `harness/`, `infra/`, `orm_models.py` ni `CHECKPOINTS.md`**.

Todo lo que sigue está verificado por el reviewer ejecutando las
herramientas, no leyendo el informe del implementer.

## Nivel de rigor

`harness/features.json` declara `"rigor": "estandar"` para F-004. Exige, por
`CHECKPOINTS.md`: C1–C3, C3 bis, C5, tests trazables (C4), **fase RED** en
los requisitos centrales, **cobertura** de las líneas cambiadas ≥ 80 % y
**campaña de mutación** con los supervivientes analizados. No exige cero
supervivientes (eso es `critico`).

## Verificación independiente de las puertas

| Puerta | Declarado | Recalculado por el reviewer | ¿Cuadra? |
|---|---|---|---|
| Alcance (ficheros) | 3 ficheros, 481 líneas | `harness.alcance --base 9772ba4`: congelacion.py 170, parte_repository.py 255, app.py 56 = **481** | Sí |
| Mutantes | 54 | `harness.mutacion.generar_mutantes` (cálculo puro): 5 + 41 + 8 = **54** | Sí |
| Cobertura | 100 % (183/183) | `python -m harness.cobertura --base 9772ba4` → **PUERTA COBERTURA: 100.0% de 183 líneas cambiadas (183/183, umbral 80%)** | Sí |
| Suite sv4 | 448 passed | ejecutada: **448 passed in 48.74s** | Sí |
| No regresión | +134 tests | suite sv4 en `9772ba4` (worktree aislado): **314 passed**. 314 + 134 = 448: **ningún test previo perdido** | Sí |
| `init.sh` | verde | ejecutado tal cual: **ENTORNO LISTO**, exit 0, `PUERTA COBERTURA [OK] 96.7% (1032/1067)` contra `dev` | Sí |
| ruff | 450 avisos, los mismos que antes | HEAD: 450. Worktree en `9772ba4`: **450**. Sobre los ficheros nuevos: `All checks passed!` | Sí |
| `node --check static/app.js` | OK | ejecutado: sin salida (OK) | Sí |

El mutante superviviente se ha **muestreado contra el generador real**:
`app.py:929`, operador `entero`, `congeladas = 0` → `congeladas = 1`. Existe
como mutante con exactamente ese operador y ese texto original→mutado. La
campaña NO declara cero mutantes, así que la prueba de control por exclusión
de alcance no aplica.

**El análisis del superviviente es correcto** (verificado leyendo
`app.py:924-997`, no el informe): los cuatro caminos que alcanzan el `return`
final reasignan `congeladas` desde el repositorio; el quinto sale por un 400
y la excepción por un 500, y ninguno de los dos lleva ese campo en el cuerpo.
No existe ejecución observable que distinga 0 de 1: **mutante equivalente**.
Mantener la inicialización está bien argumentado (sin ella, un selector
futuro daría `NameError` en producción). Ninguna sección en `PENDIENTE`.

### Fase RED — reproducida, no creída

No basta con la traza pegada en el informe. El reviewer ha hecho `checkout`
de dos commits RED en un worktree aislado y ha ejecutado sus tests:

```
$ git checkout --detach 1cbc557   # F-004 T2 (RED)
$ python -m pytest tests/test_f004_endpoints_congelados.py::test_f004_r3_patch_horas_de_linea_congelada_responde_409 -q
3 failed   (doc-aprobado, linea-encolada, linea-registrada)

$ git checkout --detach 8f122fd   # F-004 T5 (RED)
$ python -m pytest tests/test_f004_endpoints_congelados.py -q -k "r12 or r13"
7 failed, 2 passed
```

Coincide con lo que declara `progress/impl_F-004.md`. Hay commit RED propio
para T1–T6 (los requisitos centrales R1–R17). T7 (`app.js`, sin arnés de
tests JS) y T8 (cierre) no lo tienen, y no lo necesitan.

## Verificación funcional a mano (TestClient, sin fiarme de la suite)

Guion propio del reviewer sobre SQLite en memoria (`tests/dobles.py`), fuera
del repositorio. Parte con tres líneas: libre, `registrado` y `omitido`.

| # | Acción | Resultado real |
|---|---|---|
| 1 | PATCH horas de línea libre, parte sin aprobar | 200, horas 8.0 → 3.0 |
| 2 | PATCH horas de línea `registrado` | **409** `{ok:false, congelado:true, error:"Linea ya registrada en Sigrid…"}`, horas siguen 8.0 |
| 3 | PATCH horas de línea `omitido` | 200 (el camino de arreglo sigue abierto) |
| 4 | Aprobar el documento | 303 |
| 5 | PATCH horas de la línea antes libre | **409** «Parte aprobado: márcalo pendiente…», horas siguen 3.0 |
| 6 | `POST /api/registro/{id}/delete` (papelera) | **409**, línea activa |
| 7 | `POST /api/registros/{id}/extra` | **409**, no se crea |
| 8 | `PATCH /api/partes/{id}/fecha` | **409** con el motivo de documento |
| 9 | `POST /documents/{id}/delete` (formulario) | 303 a `/partes?message=<motivo>`, documento NO borrado |
| 10 | `POST /documents/{id}/unapprove` sin encoladas | 303 «Parte marcado como pendiente» |
| 11 | PATCH horas de la línea libre tras desaprobar | **200**, editable otra vez |
| 12 | PATCH horas de la `registrado` tras desaprobar | **409**, horas intactas (R11: desaprobar no levanta «vive en Sigrid») |
| 13 | `POST /api/registro/{id}/hard-delete` sobre `registrado` | **409**, la fila sigue en BBDD |
| 14 | `unapprove` con línea `encolado` | 303 con el motivo; `approved` **sigue True** (R10) |

El ciclo completo que pedía la revisión —aprobar → editar → 409 →
desaprobar → editar OK— se comporta exactamente como fija la spec, y la
BBDD queda intacta en cada rechazo.

### Matriz de congelación (R1) contra la spec

`application/services/congelacion.py` implementa la matriz **literalmente**:
`encolado` → congela; `registrado` → congela; `doc.approved` → congela; el
resto (`None`, vacío, `omitido`, `error`, `conflicto`) con documento sin
aprobar → editable. Prioridad de motivos `encolado > registrado > aprobado`,
con normalización (`strip().lower()`) para que un espacio o una mayúscula no
descongele una línea. R2 (documento) usa TODAS las líneas, papelera
incluida. Función pura: sin BBDD, sin ORM, sin FastAPI.

## Checkpoints

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` exit 0, «ENTORNO LISTO».
- [x] Existen los ficheros obligatorios (los valida el propio `init.sh`).

### C2 — El estado es coherente
- [x] Una sola feature `in_progress`: `F-004` (lo valida `init.sh`).
- [x] Rama actual `feature/F-004-congelar-aprobados`, no `main`.
- [x] `progress/current.md` describe la sesión activa (F-004 + la spec de
      F-012 que corrió en paralelo). Las «Notas de contexto» sobre
      F-002/F-003/F-013 están rotuladas como tales y son deliberadas, no
      restos.
- [x] F-002, F-003 y F-013 (`done`) tienen su resumen en
      `progress/history.md`.

### C3 — El código respeta arquitectura y convenciones
- [x] Hexagonal: la regla vive en `application/services/` (sv4 no tiene
      paquete `domain/`; es donde ya viven `jornada_resolver`, `text_match`…)
      y es pura; las guardas, en `infrastructure/database/`; la traducción a
      409, en `interface_adapters/web/`. Ninguna importación de
      infraestructura desde `congelacion.py`.
- [x] Primera línea con la ruta relativa en todos los ficheros nuevos
      (`# application/services/congelacion.py`,
      `# tests/test_f004_*.py`), coherente con el resto de sv4.
- [x] Sin `print()`, sin TODOs sueltos, sin dependencias nuevas. Barrido de
      secretos sobre el diff de `services/` y `docs/` con los patrones
      `password|passwd|secret|api[_-]?key|token|connectionstring|BEGIN
      (RSA|PRIVATE)|GUID|*.azure/windows.net|IPv4`: **3 coincidencias, todas
      literales de test** (`"irrelevante-en-tests"`, `"clave-de-prueba"`,
      `http://sigrid.interno`). Ningún secreto real.
- [x] Las tres trampas del monorepo: (1) empleado ≠ recurso — la feature no
      toca la resolución de recurso ni el DNI; (2) incidencias — no se altera
      su tratamiento, y `crear_extra_desde` sigue rechazando incidencias como
      antes; (3) **schema duplicado — `orm_models.py` NO se toca en ninguna
      de sus dos copias** (verificado en el diffstat y commit a commit), así
      que sv3 y sv4 siguen idénticos. Sin `ALTER TABLE`, sin SQL.
- [x] Convención sv4 (JS/plantillas): JS vanilla sin frameworks,
      `node --check` OK, las tres plantillas Jinja2 se parsean en 26 tests
      que las renderizan con `TestClient`.

### C3 bis — Documentos de fuera
- **N/A justificado**: la feature no añade ni modifica ningún fichero de
  `docs/referencia/` (el diff solo toca `docs/ARCHITECTURE.md`). No hay PDF
  ni ofimática en el árbol ni en el historial de la rama.

### C4 — La verificación es real
- [x] **Trazabilidad completa R1–R18** (tabla abajo); 134 tests nuevos, los
      448 de sv4 en verde.
- [x] Los unit tests no tocan red ni BBDD: SQLite en memoria,
      `Settings(_env_file=None)`, doble `SigridLookupClientFake` inyectado por
      `monkeypatch`. Comprobado leyendo los fixtures, no el informe.
- [x] Las verificaciones `MANUAL (humano)` están enumeradas en
      `progress/current.md` (las 7, por título) con puntero al detalle, y con
      su comando exacto —incluido el `curl` del 409— al final de
      `progress/impl_F-004.md`. Ver «MANUAL pendientes» abajo.

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "estandar"` declarado y válido en `harness/features.json`.
- [x] **Fase RED**: trazas reales en el informe **y reproducidas por el
      reviewer** en dos commits RED (arriba).
- [x] **Cobertura**: `[OK]` en `init.sh` (96,7 % contra `dev`) y **100 %
      (183/183)** contra la base real de la feature, recalculado.
- [x] **Mutación**: `progress/mutacion_F-004.md` existe, generado por la
      herramienta; alcance y nº de mutantes **recalculados y coincidentes**
      (481 líneas, 54 mutantes).
- [x] El único superviviente tiene análisis completado (ninguno en
      `PENDIENTE`) y el análisis es **correcto**: mutante equivalente,
      comprobado sobre el código. `estandar` no exige cero supervivientes.
- [x] El informe trae la sección **«Evidencias»** con los cuatro números
      (tests, cobertura, mutantes/supervivientes, tiempo de suite), y los
      cuatro cuadran con lo que he medido.
- [x] Ningún punto marcado N/A sin justificación.

### C4 ter — Rutas sensibles
- **N/A sin nada que justificar**: este repositorio no declara
  `harness/rutas_sensibles.json` (solo existe el `.ejemplo.json`), que es el
  caso mayoritario previsto por `CHECKPOINTS.md`.

### C5 — La sesión se cerró bien
- [x] `specs/F-004-congelar-aprobados/tasks.md` con T1–T8 todas `[x]` y un
      commit `F-004 Tn: ...` por tarea (T8 con varios, todos rotulados).
- [x] `git status` limpio: sin ficheros temporales ni artefactos sin
      trackear.
- [x] `harness/features.json` refleja el estado real (`in_progress`, que es
      el correcto a la hora de la review; el paso a `done` es del líder tras
      este veredicto).

## Cobertura de requisitos: requisito → test

Todos en `services/partes-front/tests/`. Comprobado que existen y pasan.

| R | Test(s) trazables |
|---|---|
| R1 (matriz) | `test_f004_r1_*` (10) en `test_f004_congelacion_reglas.py`: aprobado, encolado, registrado, línea libre, prioridad registrado>aprobado, motivos distintos, normalización, `ESTADOS_CONGELANTES` son exactamente dos, guarda lanza / no lanza |
| R2 (documento) | `test_f004_r2_*` (7): aprobado, una sola línea en Sigrid, prioridad del encolado, normalización, guarda, documento editable |
| R3 (409 en horas/hora/partida) | `test_f004_r3_patch_horas…`, `…patch_codigo_de_hora…`, `…patch_partida…`, `…el_motivo_del_409_distingue_el_caso`, `…la_linea_editable_sigue_editandose`, `…solo_se_congela_la_linea_congelada`, `…el_registro_inexistente_sigue_dando_404` |
| R4 (papelera de línea) | `test_f004_r4_papelera_de_linea_congelada_responde_409`, `…la_linea_libre_se_sigue_pudiendo_borrar` |
| R5 (crear extra) | `test_f004_r5_crear_extra_desde_linea_congelada_responde_409`, `…el_repositorio_tambien_se_niega`, `…la_extra_se_crea_desde_una_linea_libre` |
| R6 (fecha/obra del documento) | `test_f004_r6_patch_fecha…`, `…patch_obra…`, `…el_documento_libre_se_sigue_editando` |
| R7 (papelera de documento) | `test_f004_r7_papelera_de_documento_congelado_no_borra_y_avisa`, `…el_documento_libre_se_sigue_borrando` |
| R8 (conciliación/reasignación) | `test_f004_r8_*` (8): conciliación, las cuatro variantes de reasignación, todas congeladas, sin congeladas, sin líneas, y que no se cree entrada de undo si solo hay congeladas |
| R9 (undo) | `test_f004_r9_*` (5): línea hoy registrada, mezcla, documento congelado, filas desaparecidas, undo normal |
| R10 (unapprove con encolado) | `test_f004_r10_no_se_desaprueba_con_una_linea_en_vuelo`, `…una_encolada_en_papelera_no_bloquea…`, `…un_parte_inexistente_no_revienta` |
| R11 (unapprove libera lo no registrado) | `test_f004_r11_desaprobar_libera_lo_no_registrado`, `…la_linea_registrada_sigue_congelada_tras_desaprobar`, `…el_documento_con_linea_registrada_sigue_congelado` |
| R12 (hard-delete / vaciar papelera) | `test_f004_r12_*` (7): hard-delete de línea y de documento, vaciar papelera con documento y con línea suelta, casos libres, id inexistente |
| R13 (borrados masivos) | `test_f004_r13_*` (6): obra y trabajador con congelados, otra obra intacta, sin congelados, y los dos que fijan que la respuesta **no diga `ok`** cuando no se borró nada |
| R14 (candado en las vistas) | `test_f004_r14_*` (6, parametrizados por vista×condición): fila bloqueada, candado con motivo, línea libre sin candado, convivencia en la misma tabla, **el flag lo calcula el repositorio**, y el DTO a mano no sale congelado |
| R15 (popup de la matriz) | `test_f004_r15_la_celda_de_la_matriz_marca_las_lineas_congeladas`, `…sin_congeladas_la_celda_no_marca_nada`, `…sigue_llevando_horas_tipo_y_partida`, `…no_inventa_valores` |
| R16 (el front enseña el motivo) | `test_f004_r16_el_front_lee_el_motivo_del_409` (estático sobre `app.js`) + `test_f004_r3_el_motivo_del_409_distingue_el_caso` (el contrato que el JS consume). El comportamiento en navegador queda como MANUAL: el proyecto no tiene arnés de tests JS y la spec lo previó así |
| R17 (parte aprobado en `parte_detail`) | `test_f004_r17_el_parte_aprobado_avisa_y_bloquea_la_cabecera`, `…el_parte_pendiente_no_lleva_aviso_ni_bloqueos`, `…un_parte_sin_aprobar_con_linea_en_sigrid_tambien_avisa` |
| R18 (no regresión) | `test_f004_r18_*` (7) + las 314 pruebas previas de sv4 (F-002/F-003/F-013), **todas vivas y en verde** |

## Contra el diseño aprobado

Solo los ficheros previstos, y todos los previstos:

- Creados: `application/services/congelacion.py` y los tres ficheros de test
  del diseño.
- Modificados: `parte_repository.py`, `app.py`, las tres plantillas,
  `static/app.js`, `static/styles.css` — exactamente la tabla del diseño.
- Añadidos con permiso explícito de `tasks.md`: `tests/dobles.py`
  (`sembrar_parte`, `datos_registros`).
- Extra razonable y bienvenido: `docs/ARCHITECTURE.md` gana el punto 10 de
  «Semántica de dominio imprescindible» con la regla de congelación. No
  estaba en la tabla del diseño; documentar la regla de dominio en el sitio
  donde se buscan las reglas de dominio es correcto.
- «Ficheros que NO se tocan» respetados al pie de la letra: `orm_models.py`
  (ninguna copia), sv3, sv5, `infra/`, `harness/`, `CHECKPOINTS.md`,
  `marcar_registros_encolado`/`marcar_registros_sigrid` (con test R18 que fija
  que las escrituras del SISTEMA nunca se congelan), `restore_*`,
  `crear_parte_manual`, `approve_document` y los endpoints `/api/aprobar/*`.
- Ninguna llamada quedó con la firma vieja: los ocho llamadores de las seis
  funciones cuya firma cambió a tupla están actualizados en `app.py`
  (verificado con `grep`, no confiando en los tests).
- `azure-apps/partes.md` **no necesita cambio**: los endpoints tocados son
  APIs internas del portal; el contrato sv4↔sv5 y lo que el proyecto expone o
  consume no varían. Coincido con el diseño.

## Hallazgos

### Bloqueantes

Ninguno.

### No bloqueantes (para el humano; no exigen cambio ahora)

1. **`crear_extra_desde` es más estricto que la letra de R5.** R5 habla de
   «documento aprobado»; la implementación aplica la matriz completa, así que
   también rechaza clonar desde una línea `registrado`/`encolado` de un parte
   nunca aprobado. Es una decisión consciente y bien argumentada (decisión 4
   del informe): si el servidor fuera más permisivo que el popup de R15, la
   única forma de descubrirlo sería una petición a pelo que sí colaría.
   Superconjunto coherente de la spec, no una desviación.
2. **`parte_detail.html`: `#fechaEdit` sale `disabled` pero no cuelga de un
   `[data-congelado="1"]`**, así que `_cablear(".fecha-edit", …)` sí le
   engancha el listener (a diferencia del combo de obra, que sí lleva el
   atributo). Inocuo: un input `disabled` no dispara `change`, y si alguien le
   quita el `disabled` desde la consola, el servidor responde 409 con motivo.
   Cosmético, anotado por consistencia.
3. **`unapprove_document` comprueba en una sesión y aplica en otra**
   (`_set_approval` abre la suya). Ventana teórica: entre ambas, una línea
   `encolado` podría pasar a `registrado` — estado que no bloquea la
   desaprobación de todas formas, así que el peor caso es permitir algo que
   ya estaría permitido un milisegundo después. Sin riesgo práctico; las
   guardas de línea y documento sí van dentro de la misma sesión que la
   mutación.
4. **Tres `SAWarning` de `DELETE ... 0 were matched`** en `hard_delete_document`
   y `vaciar_papelera`. Confirmado: es código **anterior** a F-004 (borrado
   masivo + cascada del ORM sobre filas ya borradas); los tests nuevos solo lo
   sacan a la luz. Arreglarlo toca `orm_models.py` ⇒ F-010, donde ya está
   anotado.
5. **Higiene del entorno, ajena a F-004**: `git worktree list` muestra 16
   worktrees huérfanos de la campaña de mutación de **F-013**
   (`%TEMP%\mutacion_F-013_4oyscx5d\wk_*`, commit `1612b99`), con su directorio
   todavía en disco. La campaña de F-004 sí limpió los suyos. Se arregla con
   `git worktree prune` y borrando esa carpeta; no afecta a este veredicto.
6. **La puerta de cobertura de `init.sh` mide contra `dev`**, y esta rama está
   apilada sobre F-013 sin integrar: da 96,7 % (1067 líneas) en vez del 100 %
   (183 líneas) que corresponde a F-004. El número mostrado no es de esta
   feature. No engaña a nadie aquí porque ambos números constan y superan el
   umbral, pero ver «automejoras».

## Verificaciones MANUAL que quedan al humano

Ninguna es bloqueante para el merge de código; todas necesitan el portal
levantado. Están detalladas paso a paso al final de `progress/impl_F-004.md`.
**Ctrl+F5 en cada pantalla**: cambian `app.js` y `styles.css`.

1. **Parte aprobado (R17)** — banner 🔒, fecha/obra deshabilitadas,
   «+ Añadir línea» gris, candado por línea; «Marcar pendiente» lo devuelve
   todo a editable.
2. **Línea registrada (R3/R11/R16)** — candado con tooltip en `/obras/<obra>`
   y, con el portal abierto:
   `curl -i -X PATCH http://localhost:8000/api/registros/<id> -H "Content-Type: application/json" -d "{\"horas\": 1}"`
   → `HTTP/1.1 409` con `congelado: true` y el motivo.
3. **Línea encolada (R10)** — con sv5 en modo pruebas
   (`OBRA_PRUEBAS_FORZAR=true`, obra 0404, marca `PRUEBA-IA`): encolar una
   obra×mes y comprobar que «Marcar pendiente» se niega hasta que llega el
   resultado.
4. **Matriz (R15)** — doble clic en una celda de un día registrado: filas en
   gris con 🔒, sin «Guardar» y sin oferta de crear la extra.
5. **Masivas (R8/R13)** — «Borrar obra» / «Borrar persona» / reasignación con
   un mes registrado: deben avisar de cuántos se omitieron y dejarlos ahí.
6. **Papelera (R12)** — «Vaciar papelera» con una línea registrada dentro:
   avisa y no la borra.
7. **No regresión (R18)** — ↻ / Revisar / Aprobar siguen operativos sobre
   `omitido`/`error`/`conflicto`.

## Automejoras del arnés propuestas (para el humano; NO aplicadas)

Genéricas las dos: si se aceptan, van también a `arnes-base` en el mismo
trabajo, por la regla de propagación.

1. **La puerta de cobertura debería medir contra la base REAL de la rama, no
   contra `dev` fijo.** Esta feature ha tenido que explicar dos veces —en el
   informe y en la review— por qué el número de `init.sh` (96,7 % de 1067
   líneas) no es el suyo (100 % de 183). Propuesta: permitir un campo
   `base` opcional en la entrada de la feature de `harness/features.json`
   (o, por defecto, usar el `merge-base` con `dev` del punto de bifurcación
   de la rama) y que `harness/cobertura.py` lo respete. Con features apiladas
   —cada vez más frecuentes aquí— la puerta mide hoy trabajo de otros.
2. **El protocolo del reviewer debería exigir REPRODUCIR al menos una fase
   RED**, no solo comprobar que hay una traza pegada. Bastan tres comandos
   (`git worktree add --detach <commit-RED>`, `pytest` del test en cuestión,
   `git worktree remove`) y cierra el mismo hueco que la verificación
   independiente de la mutación tapó para C4 bis: una traza se puede escribir
   a mano, un `pytest` en el commit RED no. Propuesta: añadirlo a
   `.claude/agents/reviewer.md` (§«Validación contra el nivel de rigor»,
   punto 2) y a `CHECKPOINTS.md` (C4 bis, viñeta de fase RED).
3. Menor: `harness.mutacion` deja worktrees huérfanos si la campaña se
   interrumpe (caso real de F-013, ver hallazgo 5). Un `git worktree prune`
   al arrancar la campaña, o un `finally` que limpie, evitaría la basura.

## Conclusión

F-004 hace exactamente lo que su spec aprobada dice, con la regla escrita una
sola vez y aplicada donde de verdad manda —el servidor—, con la UI como
reflejo y no como defensa. Los tests son de verdad: la fase RED es
reproducible, la cobertura del diff propio es del 100 %, y de 54 mutantes solo
sobrevive uno demostrablemente equivalente. Ningún test previo se ha perdido y
el schema duplicado sigue intacto.

**APPROVED.**
