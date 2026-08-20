<!-- progress/review_F-017.md -->
# F-017 · Identidad real de Easy Auth en el portal (sv4) — Review

**Fecha:** 2026-08-20 · **Rama:** `feature/F-017-identidad-easy-auth`
**Diff:** `dev` (`4ca131c`) ... `HEAD` (`4528951`), 20 ficheros, +3435 / −77

## Veredicto

> ## CHANGES_REQUESTED (RECHAZADO)

**Nada de lo que falta es código de la feature.** El trabajo es sólido: la
resolución de identidad es correcta, la fase RED es real, la campaña de
mutación la he **reejecutado entera** y da 31/31, y la enmienda de R14/R15
**dice la verdad** (verificado por mí en el árbol, no leído del informe).

Se rechaza por **seis defectos concretos**, cinco de ellos de texto y uno de
código, que comparten una misma raíz: **la propiedad que vende la feature
—«`autor IS NULL` ⇔ fila anterior a F-017»— se enuncia sin sus excepciones en
cuatro documentos, y hay una vía real por la que una fila puede nacer sin
actor DESPUÉS del corte.** Como F-018 va a construir encima de ese criterio,
dejarlo enunciado en falso es exactamente el daño que `CLAUDE.md` describe:
«un documento desactualizado que parece vigente hace más daño que no tenerlo».
Se añade la instrucción de la spec que vuelca los secretos de Key Vault.

Todo lo exigible es reparable en una sesión corta. Ninguna corrección toca
`identidad.py` ni las rutas.

---

## Nivel de rigor

`harness/features.json` declara **`rigor: "estandar"`** para F-017. Según
`harness/rigor.json` eso exige: **fase RED**, **cobertura** de líneas
cambiadas ≥ 80 %, **campaña de mutación** con supervivientes documentados y
analizados; `supervivientes_maximos: null` (los juzga el reviewer). Las tres
puertas aplican y las tres se cumplen.

---

## C1–C5 recorridos

### C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina en verde (`ENTORNO LISTO`), ejecutado tal
      cual al abrir la review.
- [x] Existen los nueve ficheros obligatorios del arnés.

### C2 — El estado es coherente

- [x] Una sola feature `in_progress`: `['F-017']` (lo valida `init.sh`).
- [x] Rama actual `feature/F-017-identidad-easy-auth`, nunca `main` ni `dev`.
- [x] `progress/current.md` describe la sesión activa. **Nota, no defecto**:
      arrastra la sección «MANUAL pendiente del humano (acumulado)» con
      pendientes de F-010/F-015/F-016. Es deliberada y así venía de features
      anteriores; no la cuento como resto de sesión.
- [x] `progress/history.md` al día (F-016 cerrada con su resumen).

### C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal respetada, y comprobada por un test, no por lectura.**
      `identidad.py` vive en `interface_adapters/web/` —leer una cabecera HTTP
      es transporte, no dominio— y son funciones puras sin FastAPI, sin
      `Settings` y sin `os.environ`. `test_f017_r10_las_capas_internas_no_
      saben_que_existe_easy_auth` barre `infrastructure/`, `application/`,
      `domain/` y `config/`. Verificado por mí: ningún fichero de esas capas
      menciona `X-MS-CLIENT-PRINCIPAL`.
- [x] Primera línea con la ruta relativa en los **nueve** ficheros nuevos o
      tocados (comprobado uno a uno).
- [x] Sin `print()` de debug, sin TODO/FIXME, sin dependencias nuevas.
      `python -m ruff check` sobre los ficheros nuevos: **All checks passed**.
- [x] Reglas de dominio: la feature no toca empleado/recurso, ni incidencias,
      ni el schema. **Cero cambios de ORM**: las dos copias
      (`sv3`/`sv4` `orm_models.py`) están intactas en el diff, y R22 lo vigila
      con un test parametrizado por copia × columna × ancho.

### C3 bis — Documentos que entran de fuera

Aplica: el diff modifica `docs/referencia/partes-proyecto.md`.

- [x] No se añade ningún documento nuevo a `docs/referencia/`; se amplía uno
      existente, que conserva su cabecera de origen y fecha.
- [x] Sin originales PDF ni ofimáticos, ni ahora ni en el historial de la
      rama: `git log --diff-filter=A --name-only dev..HEAD` filtrado por
      extensión no devuelve **ni un fichero** que no sea `.py`, `.md` o
      `.json`.
- [x] **Barrido de datos sensibles ejecutado por el reviewer** sobre las 3 455
      líneas añadidas del diff completo (`git diff dev...HEAD | grep "^+"`),
      con estos patrones:

      | Patrón | Resultado |
      |---|---|
      | `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}` (correos) | **Limpio.** Solo dominios `.invalid` (RFC 2606): `ana.ejemplo@ejemplo.invalid`, `quien.firma@ejemplo.invalid`, `otra.persona@ejemplo.invalid`. Ni un correo real |
      | `\b[0-9]{8}[A-Za-z]\b` (DNI/NIF) | **Limpio.** Cero coincidencias. El DNI ficticio `00000000T` de `empleado_jornada` no aparece y las filas de prueba no se han tocado |
      | `\b([0-9]{1,3}\.){3}[0-9]{1,3}\b` (IPs) | **Limpio.** Cero |
      | GUID `[0-9a-f]{8}-...-[0-9a-f]{12}` (suscripción / tenant / oid) | **Limpio.** Cero |
      | `(password\|passwd\|secret\|api[_-]?key\|token)\s*[:=]\s*["']...` | **Limpio.** Las cuatro coincidencias son el nombre de cabecera `X-MS-CLIENT-PRINCIPAL` y literales de test (`"irrelevante"`, `"no-es-base64-!!!"`) |
      | `subscription\|tenant[_-]?id\|client[_-]?secret` | **Limpio.** Cero |

      Los tests usan `sub="guid-secreto"` / `tid="tenant-secreto"` como
      literales inventados para comprobar que `/whoami` NO los devuelve: son
      señuelos, no datos.
- [x] Nada que redactar, nada redactado.

### C4 — La verificación es real

- [x] Los 24 requisitos (R1–R23 + R5b/R5c) tienen test trazable y todos pasan.
      Tabla completa abajo.
- [x] Los unit tests no tocan red ni BBDD: SQLite en memoria con el ORM real,
      `Settings(_env_file=None)` y dobles, igual que la suite de F-016.
      Verificado en los cinco ficheros nuevos.
- [x] Verificaciones MANUAL listadas en `progress/current.md` (líneas 552–587)
      con comando exacto y pendientes del humano: M1 bis (**ya ejecutada**,
      positiva), M1, M2, M3 y M4.

### C4 bis — El rigor declarado se cumple

- [x] `rigor: "estandar"` declarado y válido.
- [x] **Fase RED**, con traza pegada, para los seis requisitos centrales que
      la spec exige (R1, R5, R5b, R10, R12, R16):
      - T2 (R1/R5/R5b): `ModuleNotFoundError: No module named
        'interface_adapters.web.identidad'` — los tests escritos antes del
        módulo, con la salida real de la recolección.
      - T6 (R12/R16): `AssertionError: assert None == 'ana.ejemplo@ejemplo.
        invalid'` en `test_f017_r12_approved_by` y en el sobre de
        `q-transfer`. El rojo devuelve **`None`**, que es el estado real del
        despliegue (H1), no un caso de laboratorio.
      - T8 (R10/R11): el implementer **introdujo el defecto a propósito**
        (una segunda lectura de `settings.default_reviewer` en
        `api_registro_delete`) y pegó la traza de los tres tests que lo cazan,
        incluida la que señala la ruta culpable. Es la demostración correcta
        cuando el entregable es el propio guardián.
- [x] **Cobertura**: `PUERTA COBERTURA: 99.2 % de 133 líneas cambiadas
      (132/133, umbral 80 %, nivel estandar)` en `[OK]`, leído de mi propia
      ejecución de `init.sh`.
- [x] **Mutación verificada de forma independiente**, no creída. Ver la
      sección «Verificación de la campaña».
- [x] Sin supervivientes; ninguna sección de análisis en `PENDIENTE`. Los dos
      supervivientes de las campañas intermedias están analizados en T12 y
      ambos se mataron con test nuevo (ninguno se declaró equivalente).
- [x] Sección **«Evidencias»** con los cuatro números. **Comprobado el número
      grande**: relancé la suite de sv4 entera → `1040 passed in 74.44s`,
      exit 0. Coincide con lo declarado.
- [x] Ningún punto N/A.

### C4 ter — Rutas sensibles

**N/A justificado**: no existe `harness/rutas_sensibles.json` en el
repositorio, y `CHECKPOINTS.md` dice literalmente que sin esa declaración el
bloque es N/A y no hay nada que justificar. `init.sh` no señaló ninguna ruta.

### C5 — La sesión se cerró bien

- [x] `tasks.md`: 16 tareas, **todas `[x]`, cero `[ ]`**, con commit por tarea
      (`F-017 T0` … `F-017 T12/T14`) verificado en `git log dev..HEAD`.
- [x] `git status` limpio; ningún artefacto temporal.
- [x] `features.json` refleja el estado real (`in_progress`; el paso a `done`
      es del líder tras esta review).

---

## Verificación de la campaña de mutación (independiente)

No me creí `progress/mutacion_F-017.md`. Hice las tres cosas:

**1. Recálculo puro del alcance y del número de mutantes** (`harness.alcance`
+ `harness.mutacion.generar_mutantes`, sin ejecutar la suite):

| | Informe | Mi recálculo |
|---|---|---|
| Base del diff | `4ca131c…` | `4ca131c…` = `git rev-parse dev` **y** `merge-base` ✔ |
| `app.py` | 143 líneas | 143 ✔ |
| `identidad.py` | 257 líneas | 257 ✔ |
| Total líneas | 400 | 400 ✔ |
| Mutantes | 31 | **31** ✔ |

Reparto por operador: 10 lógico, 8 not, 7 booleano, 4 comparación, 1 entero,
1 aritmético.

**2. Prueba de control del «cero»**: no aplica en el sentido peligroso —la
campaña declara 31 mutantes, no cero—, así que el generador demostradamente
funciona sobre estos ficheros.

**3. La reejecuté entera.** En vez de muestrear supervivientes (no hay
ninguno, que es el caso en el que un informe falso es más fácil de escribir),
apliqué **los 31 mutantes uno a uno** sobre el árbol real, ejecuté la suite
del servicio dueño con el mismo ejecutor del arnés y restauré el fichero en un
`finally`:

```
TOTAL 31 Counter({'muerto': 31}) 95s
--- arbol --- (git status vacío)
```

**31/31 muertos, 0 supervivientes. El informe del implementer es exacto.**
Antes había muestreado a mano los cuatro mutantes más difíciles de matar
(`ACTOR_MAX_LEN 120→121`, `b64decode(validate=True→False)`,
`cabecera_vista=False→True`, `c == " "→ c != " "`) y los cuatro murieron.

### La limitación conocida del arnés, y por qué aquí no muerde

`harness/mutacion.py` juzga cada mutante con la suite **del servicio dueño del
fichero mutado** (`ejecutor_para`), así que los guardianes que viven en
`tests/` de la raíz —los de **R22 y R23**— no pueden matar mutantes de sv4.
Aquí eso **no afecta al resultado**, y lo he comprobado en vez de suponerlo:
los 31 mutantes viven en `app.py` e `identidad.py`, ambos de sv4, cuya suite
es exactamente donde están los tests de F-017. Los ficheros que R22 y R23
vigilan (las dos copias del ORM y `docs/referencia/partes-proyecto.md`) **no
generan ni un mutante**: el ORM no está en el diff y un `.md` no se muta. La
limitación es real y hay que tenerla presente en features futuras que cambien
código de la raíz; en ésta es inocua.

---

## Los cinco puntos que se pidieron mirar con lupa

### 1. La enmienda de R14 y R15 — **NO es una excusa: dice la verdad**

Éste era el punto en el que había que buscar trampa. La verifiqué entera **en
el árbol**, sin leer el informe, y las tres afirmaciones se sostienen:

1. **`undo_log.actor` no la escribe nadie.** `_record_undo`
   (`parte_repository.py:1756`) ni siquiera acepta un actor: construye
   `UndoLogOrm(created_at_utc=…, action=…, description=…, payload=…,
   undone=False)` y ya. Un barrido de asignaciones sobre las siete columnas de
   autor en todo sv4 no devuelve **ni una** a `actor`.
2. **Las cuatro operaciones de R14/R15 no generan filas de `undo_log`.**
   Resolví los nueve llamantes de `_record_undo` por AST y son todos
   ediciones: `update_registro`, `set_registro_hora`, `set_registro_partida`,
   `backfill_empleado`, `reassign_empleado_by_leido`,
   `…_by_worker_key`, `…_by_registro_ids`, `update_parte_fecha`,
   `update_parte_obra`. `soft_delete_registro`, `soft_delete_obra`,
   `soft_delete_worker` y `crear_parte_manual`: **ninguna** llama a
   `_record_undo`.
3. **`crear_parte_manual` declara `by` y lo tira.** Extraje el cuerpo entero
   del método (líneas 2548–2698): `by` aparece **exactamente una vez**, en la
   firma (`by: str | None = None`, línea 2562). Cero usos.
4. **No hay dónde persistir el alta manual.** `ParteDocumentOrm` y
   `ParteRegistroOrm` no tienen `created_by`; el `created_by` del ORM que sí
   existe es de `EmpleadoAliasOrm` y `EmpleadoJornadaOrm`. Añadirlo habría
   tocado **las dos copias** del ORM, que es precisamente el cambio de schema
   que la feature prometió no hacer.

**Juicio.** La enmienda no tapa trabajo no hecho: **describe trabajo que era
imposible hacer dentro del alcance declarado**, y lo hace nombrando lo que
queda fuera («lo que NO: el dato guardado») en vez de esconderlo. El orden fue
el correcto —el implementer paró en T6, marcó el hallazgo como «⚠ HALLAZGO QUE
EL HUMANO DEBE DECIDIR», descartó por escrito las dos salidas que habría
podido tomar por su cuenta, y el humano decidió después—. Es lo contrario de
la trampa: reescribir la spec para que encaje con lo implementado habría sido
callar que `undo_log.actor` seguirá vacía. Aquí se dice en la spec, en el
informe, en `current.md` y en la documentación de referencia.

**Lo que sí falla es la propagación de esa enmienda** a los otros cuatro sitios
donde el criterio sigue enunciado en su forma vieja. Es el defecto 2 de abajo.

### 2. R7 y el corte — **el criterio, tal como está documentado, NO es cierto**

Aquí está el fondo del rechazo. Dos agujeros distintos:

**(a) `undo_log.actor` — conocido, documentado en un sitio y solo en uno.**
Las filas de `undo_log` que se creen **mañana** nacerán con `actor = NULL`.
Quien lea la tabla dentro de un año y aplique el criterio publicado concluirá
que son anteriores a F-017. **Falso.** El criterio se enuncia **sin la
excepción** en cuatro sitios y **con** ella en uno solo:

| Documento | Enuncia el criterio | ¿Trae la excepción? |
|---|---|---|
| `docs/referencia/partes-proyecto.md` §5.7 punto 3 | sí | **SÍ, correcta y explícita** ✔ |
| `docs/ARCHITECTURE.md:152` | sí, «exclusivamente» | **NO** ✘ |
| `azure-apps/partes.md:211` | sí, «exclusivamente» | **NO** ✘ |
| `specs/…/requirements.md:135` (R7) | sí, «exclusivamente» | **NO** ✘ (y R15:204 sí lo reconoce, en la misma spec, 70 líneas más abajo) |
| `identidad.py:5-8` y `:53` | lista `undo_log.actor` entre las columnas que **se sellan** | **NO** ✘ |

`ARCHITECTURE.md` es el documento que los agentes leen antes de diseñar. Dejar
ahí la versión sin excepción es sembrar el error justo donde F-018 lo va a
recoger.

**(b) Encontrado en esta review, no consta en ningún informe: `DEFAULT_REVIEWER`
SÍ puede firmar estando desplegado, y una fila SÍ puede nacer sin actor
después del corte.**

`services/partes-front/interface_adapters/workers/resultado_consumer.py:48`:

```python
usuario = sobre.get("usuario") or getattr(settings, "default_reviewer", None)
```

Ese `usuario` va a `aplicar_resultado(...)` y termina en
`reg.sigrid_registrado_by = usuario` (`parte_repository.py:1363` y otras
cinco). Consecuencias, las dos reales:

- **Un mensaje en vuelo en `q-transfer-result` en el momento del despliegue**
  lleva un sobre publicado ANTES de F-017, es decir con
  `usuario = settings.default_reviewer = None` (el publicador de `dev` pasaba
  exactamente eso). El consumidor lo aplica y marca líneas **después del
  corte** con `sigrid_registrado_by = NULL`. El criterio «NULL ⇔ anterior a
  F-017» queda roto para esas filas, en la ventana del despliegue.
- **Si alguna vez se configura `DEFAULT_REVIEWER` en Azure**, este consumidor
  firmará filas de producción con ella. Eso contradice de frente lo que la
  propia feature declara en tres sitios: «`DEFAULT_REVIEWER` … estando
  desplegado **no firma nada**» (`identidad.py:35-37`), y lo mismo en
  `ARCHITECTURE.md` y en `azure-apps/partes.md`.

Ningún test cubre esta línea, y el guardián del punto único **no puede
verla**: `test_f017_r11_*` solo lee `app.py`, y
`test_f017_r10_el_repositorio_no_importa_identidad` solo lee
`parte_repository.py`. R10 nombra «ninguna ruta, plantilla ni repositorio», y
un worker no es ninguna de las tres — la letra se cumple, el propósito no.

**No hay más vías.** Barrí las 22 asignaciones a columnas de autor de sv4 y el
resto está sano: las once rutas pasan por `_actor` (14 llamadas contadas), las
dos escrituras de `empleado_alias.created_by` llevan los literales de proceso
`"conciliacion"` / `"reasignacion"` (nunca `NULL`, y fuera del espacio
reservado), y los `= None` de `_set_approval` / restaurar papelera son
**desaprobar y desborrar**, que limpian el par completo
(`approved_at_utc`/`deleted_at_utc`) y por eso no rompen la consulta del
corte, que ya filtra por esos campos. Sobre `empleado_alias`: solo sv4 lo
escribe (sv3 tiene la clase del ORM pero no la instancia nunca), así que la
tabla no puede recibir filas sin autor por la puerta de atrás.

### 3. R5/R5b/R5c y la asimetría — **cubierta, y bien**

El caso peligroso (creerse local estando desplegado ⇒ escribir `local:…` en
producción) **no se queda en el diseño**: lo cubren tres tests que reproducen
el escenario del fallo de la señal A, no la señal aislada.

- `test_f017_r5c_la_senal_b_se_aprende_y_corrige_a`: la plataforma deja de
  inyectar `CONTAINER_APP_*`; entra un usuario autenticado; la siguiente
  petición **sin** cabecera ya no cae en `local:` — `entorno == "desplegado"`,
  `senal_despliegue == "cabecera-vista"`, y afirma explícitamente
  `not actor.startswith("local:")`.
- `test_f017_r5c_la_senal_b_tambien_llega_a_la_columna`: impide que la señal B
  se quede en cosmética de `/whoami` — comprueba el valor **sellado en la
  fila** (`approved_by == "sin-identidad"`).
- `test_f017_r5c_creerse_desplegado_en_local_es_inocuo`: la otra dirección,
  con `DEFAULT_REVIEWER="ana"` puesta, y afirma que `"ana" not in sellado`.

La asimetría está **fijada por test**, que es lo que se pedía. R5b, además, no
se conforma con la igualdad: afirma la ausencia del prefijo, la presencia del
WARNING en `caplog` y que la escritura se completa. La señal A dejó de ser
supuesto: T0 la confirmó en `ca-sv4-front` y
`test_f017_r5c_las_cuatro_variables_declaradas` congela la lista.

Detalle menor, no bloqueante: en `/whoami` la señal se calcula **antes** de
`_resolver_identidad`, así que en la primerísima petición que aprende la señal
B el campo `entorno` va un paso por detrás de `origen`. Inofensivo (desplegado
manda la señal A) y no afecta a lo que se sella.

### 4. R6, el espacio reservado — **intenté romperlo y no cede**

La garantía es estructural, no una apuesta sobre la forma del texto, y aguanta
los ataques que se me ocurrieron:

- **Orden correcto.** `es_actor_reservado` se evalúa sobre el valor **ya
  normalizado y ya truncado**, y `normalizar_actor` es idempotente. No hay
  ventana entre «lo que se comprueba» y «lo que se devuelve».
- **Mayúsculas / espacios**: `LOCAL:X`, ` Sin-Identidad ` → normalizados →
  descartados.
- **Caracteres invisibles**: los de control se **eliminan antes** de comparar,
  así que `local:​x` o `local:\xa0x` colapsan a `local:x` y se descartan.
  Meterlos no evade la comprobación: la dispara.
- **Truncado**: el corte a 120 ocurre antes del test, así que no se puede
  fabricar un reservado por truncamiento ni esconder uno detrás de 120
  caracteres.
- **Las dos vías**: `-NAME` y token se comprueban **por separado**; envenenar
  una no contamina la otra ni salta el descarte de la segunda.
- **El fallback tampoco**: si `DEFAULT_REVIEWER` fuese `local:x`, se descarta
  y se cae a `local:sin-identidad`.
- Lo más cerca que llegué fue confusión **visual** (homoglifos: `SİN-İDENTİDAD`
  baja a `si̇n-i̇dentidad`, con punto combinante), que no es igualdad y por
  tanto no invade el espacio reservado — se guarda como el texto raro que es.
  No lo cuento como defecto: la garantía es de igualdad exacta y se cumple.

`test_f017_r6_que_cuenta_como_reservado` incluye los dos casos frontera que
importan: `sin-identidad@ejemplo.invalid` (empieza igual) y
`localista@ejemplo.invalid` (`local` sin `:`), ambos **no** reservados. El
mutante que convierte ese `and` en `or` (`identidad.py:232`) muere.

### 5. R10/R11, el punto único — **exacto**

Comprobado por mí, no solo por el test: `grep -rn "default_reviewer"` sobre el
código de producción de sv4 devuelve **tres** líneas —
`config/settings.py:103` (la declaración), `app.py:505` (dentro de
`_resolver_identidad`) y `workers/resultado_consumer.py:48`. En `app.py` hay
**exactamente una**, y está en el resolutor: R11 se cumple al pie de la letra.
El guardián lo vigila por tres vías (recuento, ubicación dentro del bloque del
resolutor, barrido por cuerpo de ruta) y el implementer demostró en T8 que
detecta el defecto sembrándolo. La tercera lectura, la del worker, es el
defecto 1 de abajo.

### 6. R19 y el test de F-016 — **reparado como prometía la spec**

Se hizo **exactamente** lo que el aviso del reviewer de F-016 pedía y lo que
la spec anunciaba: `test_f016_r13_auditoria` ya no parchea
`DEFAULT_REVIEWER` (`monkeypatch` fuera, incluido el parámetro de la firma) y
**fabrica la cabecera** con un helper `_como(usuario)` que devuelve
`{"X-MS-CLIENT-PRINCIPAL-NAME": usuario}`. Prueba el camino real
cabecera → columna. Parchear `_actor` no era una alternativa y la razón es
correcta: es una clausura dentro de `build_app`, no un símbolo de módulo.

**No se debilitó: se reforzó.** El test conserva las cinco escrituras y todas
sus aserciones, y se añaden dos:
`test_f016_r13_cada_peticion_lleva_su_propio_actor` (dos personas distintas,
dos firmas distintas en la misma fila — imposible de expresar con
`DEFAULT_REVIEWER`), y `test_f016_r13_sin_cabecera_se_sella_el_actor_local`,
que sustituye al viejo `…_se_sella_nulo_y_no_falla` afirmando el nuevo
contrato (`local:sin-identidad`) **y** que el cambio no se pierde. Los cinco
endpoints de F-016 no se han tocado: la promesa de F-016 («solo cambia el
INTERIOR de `_actor`») se cumplió.

### 7. `GET /whoami` — **no filtra nada**

Superficie nueva expuesta en producción, mirada como tal. Devuelve cinco
campos y ninguno lleva material sensible: `actor` (la identidad **de quien
pregunta**, ya normalizada), `origen` (una de las cuatro ramas), `entorno`,
`senal_despliegue` (el **nombre** de la variable, nunca su valor) y
`cabeceras_easy_auth` (solo **nombres** de cabeceras presentes, por
comprensión sobre tres constantes).

`test_f017_r21_whoami_no_revela_valores_ni_claims` es el test correcto: manda
un token con `sub="guid-secreto"` y `tid="tenant-secreto"` más un
`X-MS-CLIENT-PRINCIPAL-ID: oid-secreto`, y afirma sobre el **texto crudo** de
la respuesta que no aparece ni el token, ni el `sub`, ni el `tid`, ni el
`oid`; además congela el conjunto exacto de claves con `set(datos) == {...}`,
de modo que añadir un campo nuevo pone el test rojo.
`test_f017_r21_whoami_no_escribe_nada` comprueba que consultarlo no ensucia
ninguna fila, que es lo que hace útil a M1. No expone datos de otro usuario ni
estado global. **Sin objeciones.** (Único detalle cosmético: es la única ruta
sin `include_in_schema=False`, así que sale en el OpenAPI. No es una fuga.)

### 8. Límite de servicio — **solo sv4, cero schema**

El diff toca 20 ficheros: `services/partes-front/**` (2 de producción, 5 de
test), `tests/` de la raíz (2 guardianes), `docs/` (2), `specs/` (3),
`progress/` (3) y `harness/features.json`. **Cero ficheros de sv1, sv2, sv3 o
sv5. Cero cambios en las dos copias de `orm_models.py`** (confirmado en el
diffstat y vigilado por R22). `azure-apps/partes.md` se actualizó **en su
propio repositorio y con su propio commit** (`47cb860`), como manda la regla
de propiedad de `CLAUDE.md`.

### 9. Datos personales — **limpio**

Ver el barrido de C3 bis: ni un DNI, ni un correo real, ni una IP, ni un GUID,
ni un secreto, en código, tests, spec ni `progress/`. Las filas de prueba con
DNI `00000000T` **no se han tocado** (la feature no escribe en
`empleado_jornada` fuera de los endpoints existentes y el diff no las
menciona).

---

## Cobertura requisito → test

| R | Test | Estado |
|---|---|---|
| R1 | `test_f017_identidad.py::test_f017_r1_manda_la_cabecera_name` | ✔ |
| R2 | `::test_f017_r2_sin_name_se_lee_el_token` (5 claims) | ✔ |
| R3 | `::test_f017_r3_token_corrupto_no_rompe` (4 formas de reventar) | ✔ |
| R4 | `::test_f017_r4_normalizacion` | ✔ |
| R5 | `::test_f017_r5_fallback_local_sin_desplegar` | ✔ |
| R5b | `::test_f017_r5b_desplegado_sin_cabecera_es_sin_identidad_con_warning` | ✔ |
| R5c | `test_f017_entorno.py` (15 tests: 4 variables, vacías, señal B, asimetría) | ✔ |
| R6 | `::test_f017_r6_espacio_reservado_por_cabecera_se_descarta`, `::_el_descarte_avisa`, `::_que_cuenta_como_reservado` | ✔ |
| R7 | `::test_f017_r7_siempre_hay_actor` (4 cabeceras × 2 entornos × 4 fallbacks) | ✔ en el resolutor; **la propiedad global falla fuera de él** (defecto 1) |
| R8 | `::test_f017_r8_upn_larguisimo_se_trunca_y_no_falla` | ✔ |
| R9 | `::test_f017_r9_aviso_una_sola_vez` | ✔ |
| R10 | `test_f017_punto_unico.py` (5 tests, incluidas las 4 capas internas) | ✔ letra; **no alcanza a `workers/`** (defecto 1) |
| R11 | `::test_f017_r11_una_sola_lectura…`, `::_esta_dentro_del_resolutor`, `::_ninguna_ruta…` | ✔ verificado a mano |
| R12 | `test_f017_endpoints_firmados.py::test_f017_r12_approved_by` | ✔ |
| R13 | `::test_f017_r13_deleted_by` | ✔ |
| R14 | `::test_f017_r14_borrar_linea_sella_deleted_by`, `::_undo_log_actor_borrados` (3 rutas), `::_sin_cabecera_tambien_se_firma`, `::_cada_peticion_lleva_su_actor` | ✔ (enmendado) |
| R15 | `::test_f017_r15_undo_log_actor_parte_manual`, `::_sin_cabecera…`, `::_desplegado_sin_cabecera…` | ✔ hasta la frontera del repositorio (enmendado) |
| R16 | `test_f017_aprobacion_firmada.py::test_f017_r16_payload_y_marcas` | ✔ |
| R17 | `::test_f017_r17_log_forzado_nombra_al_actor` | ✔ |
| R18 | `::test_f017_r18_el_sobre_manda_en_el_consumidor` | ✔ el sobre; **no el fallback** (defecto 1) |
| R19 | `test_f016_endpoints_admin_jornadas.py::test_f016_r13_auditoria` + 2 nuevos | ✔ |
| R20 | `::test_f017_r20_cabeceras_basura_no_cambian_el_estado` | ✔ |
| R21 | `::test_f017_r21_whoami*` (5 tests) | ✔ |
| R22 | `tests/test_f017_r22_sin_reescritura_historica.py` (ORM × 2 copias + barrido de `UPDATE`/`.sql`) | ✔ |
| R23 | `tests/test_f017_r23_corte_documentado.py` | ✔ |

Los nombres `test_f017_r14_undo_log_actor_*` y `test_f017_r15_undo_log_actor_*`
conservan a propósito el literal histórico del requisito. Con la enmienda ya
no describen lo que comprueban (comprueban `deleted_by` y el paso por `by=`).
Renombrarlos sería más honesto, pero **no lo exijo**: la spec dice
explícitamente que se conserva el nombre y el docstring lo aclara.

---

## Cambios requeridos

Ninguno toca `identidad.py` ni las rutas. El 1 es de código; los demás, de
texto.

1. **`services/partes-front/interface_adapters/workers/resultado_consumer.py:48`
   — quitar el fallback a `DEFAULT_REVIEWER`, o justificarlo por escrito.**
   Hoy dice
   `usuario = sobre.get("usuario") or getattr(settings, "default_reviewer", None)`.
   Es la tercera lectura de identidad del portal y contradice lo que la propia
   feature publica en tres documentos («estando desplegado no firma nada»).
   Lo que hay que entregar:
   - dejar que el sobre mande solo (R18 ya dice que el sobre viaja firmado), o
     bien conservar el fallback con un comentario que explique por qué;
   - **un test** que fije el comportamiento con un sobre sin `usuario`
     (hoy no hay ninguno que ejecute esa línea);
   - **ampliar el guardián del punto único** para que barra el código de
     producción de sv4 entero y no solo `app.py` y `parte_repository.py` —
     tal como está, esta lectura podría reaparecer sin que nada se queje.
   Si se decide dejarlo como está, hay que **documentar la ventana**: los
   mensajes en vuelo en `q-transfer-result` durante el despliegue marcarán
   líneas con `sigrid_registrado_by = NULL` después del corte.

2. **`docs/ARCHITECTURE.md:152` — añadir la excepción de `undo_log.actor`.**
   Dice «`NULL` en una columna de autor significa exclusivamente “fila
   anterior a F-017”» sin salvedad. Es falso para `undo_log.actor`, que sigue
   naciendo `NULL`. Basta con la frase que ya está bien escrita en
   `docs/referencia/partes-proyecto.md` §5.7 punto 3.

3. **`azure-apps/partes.md:211` (repositorio `azure-apps`) — la misma
   corrección**, y con su propio commit, como se hizo con `47cb860`. Es el
   documento que se lee para operar el servicio.

4. **`specs/F-017-identidad-easy-auth/requirements.md:135` (R7) — acotar el
   criterio.** La propia spec ya se contradice: R15 (línea 204) reconoce que
   «`undo_log.actor` sigue vacío», pero R7 sigue diciendo «exclusivamente».
   La enmienda del 2026-08-20 tocó R14 y R15 y **no propagó a R7**, que es el
   requisito del que cuelga todo.

5. **`specs/F-017-identidad-easy-auth/requirements.md:341` — quitar el comando
   que vuelca los secretos.** M1 bis sigue proponiendo
   `az containerapp exec … --command "printenv" | Select-String CONTAINER_APP`.
   El `Select-String` filtra **lo que se muestra**, no lo que el contenedor
   imprime ni lo que viaja: `printenv` a secas vuelca **todas** las variables
   con los secretos ya resueltos desde Key Vault (`PG_PASSWORD`,
   `SESAME_API_KEY`, …) al terminal y a su historial. El implementer lo
   detectó y ejecutó T0 variable a variable; `progress/current.md:554-561` lo
   deja avisado. **Falta arreglarlo en la spec**, que es el documento
   versionado que alguien volverá a leer. Sustituir por la forma segura ya
   usada:
   `az containerapp exec -n ca-sv4-front -g rg-partes-dev --command "printenv CONTAINER_APP_NAME"` (ídem con las otras tres).

6. **`specs/…/requirements.md:348-349` (M3) y
   `services/partes-front/interface_adapters/web/identidad.py:5-8 y :53` —
   restos de la premisa vieja.** M3 manda comprobar `undo_log.actor` tras un
   borrado, que la enmienda demostró que no se escribe ni genera fila
   (`current.md` ya lleva el «Ojo», la spec no). Y el docstring del módulo
   lista `undo_log.actor` entre las columnas donde el actor **se sella**, y la
   línea 53 justifica `ACTOR_MAX_LEN = 120` como «la columna más estrecha:
   `undo_log.actor`»: el número es correcto, pero la razón debe ser una
   columna que de verdad se escriba (`empleado_jornada.created_by` /
   `updated_by`, también 120).

**No exigido, para que conste**: `/whoami` calcula `senal` antes de
`_resolver_identidad`, con lo que `entorno` puede ir una petición por detrás
en el instante en que se aprende la señal B (irrelevante desplegado); y es la
única ruta sin `include_in_schema=False`.

---

## Automejora del arnés (propuesta, no aplicada)

1. **`CHECKPOINTS.md` / `.claude/agents/reviewer.md` — checkpoint nuevo: «la
   enmienda de un requisito se propaga».** Esta feature enmendó R14 y R15 tras
   verificar el árbol —bien hecho— y dejó la premisa vieja viva en R7, en dos
   verificaciones MANUAL, en dos documentos de arquitectura y en un docstring.
   Enmendar una spec es legítimo y hay que poder hacerlo; lo que falta es la
   exigencia de **buscar y arreglar todos los sitios donde el requisito viejo
   se daba por cierto**, en la misma feature. Redacción propuesta para C3:
   «Si algún requisito se enmendó durante la implementación, el informe de
   review lista los sitios donde la premisa antigua seguía enunciada y
   confirma que se corrigieron todos».

2. **`harness/mutacion.py` — que el informe declare qué suite juzgó cada
   mutante.** La limitación (solo se ejecuta la suite del servicio dueño del
   fichero) obliga hoy al reviewer a razonarla a mano en cada feature para
   saber si muerde. Con una columna «suite» en el informe, o una nota
   automática cuando el diff toca ficheros de la raíz, se vería sola.

3. **`.claude/agents/reviewer.md` — cuando la campaña declare 0
   supervivientes, muestrear MUERTOS.** El protocolo manda muestrear
   supervivientes, pero un informe de mutación falso es más fácil de escribir
   **sin** supervivientes: no hay nada que muestrear y los totales cuadran
   solos. Aquí lo resolví reejecutando los 31 (95 s, porque la suite muere
   rápido con `-x`), y propongo que sea la regla: con cero supervivientes,
   reejecutar la campaña o muestrear al menos tres muertos de los operadores
   más difíciles.
