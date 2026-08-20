<!-- specs/F-017-identidad-easy-auth/tasks.md -->
# F-017 · Identidad real de Easy Auth en el portal (sv4) — Tareas

Rama: **`feature/F-017-identidad-easy-auth`**, creada desde `dev` (que ya
lleva F-015 y F-016 dentro). Un commit **local** por tarea, mensaje
`F-017 Tn: …`, añadiendo **rutas explícitas** (nunca `git add -A`). Sin
`git push` y sin PR: eso lo hace el humano.

Rigor **`estandar`** ⇒ **fase RED** con la traza real pegada en
`progress/impl_F-017.md` para **R1, R5, R5b, R10, R12 y R16**; **cobertura**
de las líneas cambiadas ≥ 80 %; **campaña de mutación** con los supervivientes
analizados uno a uno.

> **Enmienda del humano del 2026-08-20 ya incorporada** (`design.md` §4 y
> §4.1): el fallback tiene **dos ramas**. Sin desplegar, `local:<algo>`;
> **desplegado y sin cabecera, `sin-identidad` + WARNING**. Escribir `local:`
> en producción sería afirmar un origen falso y taparía una caída de la
> autenticación. Afecta a **T0, T2, T3, T7** y añade **T3 bis**.

Reglas que no se negocian durante la ejecución:

- **Ningún test toca red ni BBDD**: `TestClient`, `FabricaSesionSqlite`,
  dobles y `Settings(_env_file=None)`.
- **Ningún cambio de schema y ninguna columna nueva.** Si parece que hace
  falta una, el diseño se torció: **parar y consultar** (`design.md` §1).
- **Ningún `403`, ningún rol, ninguna restricción de acceso**: eso es F-008
  (`requirements.md` §0).
- **Ni un correo real de una persona, ni un DNI, ni una IP** en el código, en
  los tests ni en los mensajes de commit. Dominio de pruebas:
  `ejemplo.invalid`.
- La firma `def _actor(request: Request) -> str | None` es **intangible**:
  hay un test de F-016 que compara ese texto literal (`design.md` §6).

---

- [x] **T0 (PUERTA, antes de escribir nada): confirmar la señal de despliegue
      (R5c).** Ejecutar la verificación **M1 bis** de `requirements.md` §4 y
      pegar la salida real en `progress/impl_F-017.md`:
      `az containerapp exec -n ca-sv4-front -g rg-partes-dev --command "printenv" | Select-String CONTAINER_APP`
      Hoy **ningún servicio del monorepo lee esas variables** y ningún script
      de `infra/` las declara (comprobado el 2026-08-20): es un supuesto de
      plataforma, no un hecho verificado aquí.
      **SI NO APARECE NINGUNA `CONTAINER_APP_*`: PARAR.** No improvisar otra
      señal: marcar la feature `blocked`, anotarlo en `progress/current.md` y
      consultar al humano la alternativa `ENTORNO=produccion` de
      `design.md` §4.1 (que sí obliga a tocar Azure).
      Verificación: MANUAL (humano) — la lista de variables encontradas, con
      su nombre y **sin sus valores**, pegada en el informe.

- [x] **T1: Inventario de rojos.** Con la rama recién creada y **sin tocar
      nada**, ejecutar la suite de sv4 y dejar constancia del punto de
      partida en `progress/impl_F-017.md`; después, listar por lectura los
      tests que dependen de `DEFAULT_REVIEWER` y anotar cuáles se espera que
      caigan y por qué (`design.md` §6).
      Verificación: `python -m pytest services/partes-front/tests -q` en
      verde + sección «Punto de partida» en `progress/impl_F-017.md` con el
      recuento real y la lista de tests candidatos.

- [x] **T2: Fase RED de la resolución de identidad.** Escribir
      `services/partes-front/tests/test_f017_identidad.py` (R1–R9 menos R5c,
      R20, R21) y `services/partes-front/tests/test_f017_entorno.py` (R5c)
      **antes** de que exista `identidad.py`, y pegar la traza real del fallo
      en `progress/impl_F-017.md`. **La fase RED de R5b y R5c es obligatoria
      y no es una formalidad**: son los requisitos que impiden que un fallo
      de autenticación en producción se disfrace de sesión local, y esa clase
      de defecto no se ve leyendo el código.
      Verificación: los dos ficheros fallan con
      `ModuleNotFoundError`/`AttributeError`, y la salida está pegada en el
      informe.

- [x] **T3: `identidad.py`.** Crear
      `services/partes-front/interface_adapters/web/identidad.py` con
      `normalizar_actor`, `es_actor_reservado`, `actor_desde_token`,
      `senal_de_despliegue` y `actor_desde_cabeceras` (firmas en
      `design.md` §7). **Funciones puras**: sin FastAPI, sin `Settings`, y
      `senal_de_despliegue` recibe el entorno como `Mapping` en vez de leer
      `os.environ` por dentro. Primera línea del fichero, el comentario con
      su ruta relativa.
      Verificación:
      `python -m pytest services/partes-front/tests/test_f017_identidad.py services/partes-front/tests/test_f017_entorno.py -q`
      en verde salvo los tests de `/whoami` (R21), que dependen de T7.

- [x] **T3 bis: Las dos ramas del fallback, comprobadas por separado (R5,
      R5b, R6).** Cerrar los tests que distinguen los dos entornos: sin
      desplegar ⇒ `local:…`; desplegado y sin cabecera ⇒ **exactamente**
      `sin-identidad`, **sin** el prefijo `local:`, con **WARNING** en
      `caplog`; y el espacio de nombres reservado descartado en los dos
      entornos (`local:x`, `LOCAL:X`, `sin-identidad`, ` Sin-Identidad `).
      Verificación: `python -m pytest services/partes-front/tests/test_f017_identidad.py -q -k "r5 or r5b or r6"`
      en verde, y una aserción explícita de que el valor desplegado **no**
      empieza por `local:` (no basta con comprobar que es `sin-identidad`:
      es justo la confusión que la enmienda viene a evitar).

- [x] **T4: `_actor` pasa a leer la cabecera.** Cambiar **solo el interior** y
      el docstring de `_actor` en
      `services/partes-front/interface_adapters/web/app.py`, dejando la firma
      intacta; añadir junto a él `_resolver_identidad` (que emite el WARNING
      de R5b y mantiene viva la señal B) e inicializar
      `app.state.easy_auth_visto = False` en `build_app`.
      Verificación:
      `python -m pytest services/partes-front/tests/test_f016_endpoints_admin_jornadas.py -q`
      — `test_f016_r13_la_identidad_se_resuelve_en_un_solo_sitio` **sigue en
      verde** (si se pone rojo, se ha roto el punto único) y
      `test_f016_r13_auditoria` se pone **ROJO**, que es la trampa anunciada.
      Ambos resultados van al informe: el rojo es evidencia de que `_actor`
      manda de verdad.

- [x] **T5: Reparar los tests de F-016 (R19).** En
      `services/partes-front/tests/test_f016_endpoints_admin_jornadas.py`:
      helper `_como(usuario)`, reescribir `test_f016_r13_auditoria` para que
      fabrique la cabecera, y convertir
      `test_f016_r13_sin_default_reviewer_se_sella_nulo_y_no_falla` en
      `test_f016_r13_sin_cabecera_se_sella_el_actor_local`
      (`design.md` §6).
      Verificación:
      `python -m pytest services/partes-front/tests/test_f016_endpoints_admin_jornadas.py -q`
      entero en verde, incluido el test del punto único.

- [x] **T6: Fase RED de los once puntos.** Escribir
      `test_f017_endpoints_firmados.py` (R12–R15) y
      `test_f017_aprobacion_firmada.py` (R16–R18) **antes** de tocar las
      rutas, y pegar la traza del fallo de R12 y R16 en el informe.
      Verificación: los dos ficheros fallan por el motivo esperado (se sella
      `local:…` en vez del principal), con la salida pegada.

- [x] **T7: Los once puntos + `/whoami`.** En `app.py`: añadir
      `request: Request` a las cinco firmas que no lo tienen
      (`approve_document`, `delete_document`, `api_registro_delete`,
      `api_obra_delete`, `api_trabajador_delete`), pasar `actor` por
      parámetro a `_payload_registro` y `_trazar`, sustituir las once lecturas
      de `settings.default_reviewer` por `_actor(request)` y añadir la ruta
      `GET /whoami` (R21) con sus cinco campos: `actor`, `origen` (las
      **cuatro** ramas), `entorno`, `senal_despliegue` y
      `cabeceras_easy_auth` (**nombres**, nunca valores). Tabla completa en
      `design.md` §5.2.
      Verificación: `python -m pytest services/partes-front/tests -q` en verde
      **entero**, incluidos los tests de F-002/F-003/F-004 inventariados en
      T1 (ajustando sus literales donde solo comprobaban «que hay un valor»).

- [x] **T8: El punto único, con guardián (R10, R11).** Escribir
      `services/partes-front/tests/test_f017_punto_unico.py`: `app.py`
      contiene exactamente **una** lectura de `settings.default_reviewer` y
      está dentro de `_actor`; ninguna otra función lee cabeceras
      `X-MS-CLIENT-PRINCIPAL*`; y ningún fichero de
      `infrastructure/` ni `application/` de sv4 las menciona.
      Verificación: `python -m pytest services/partes-front/tests/test_f017_punto_unico.py -q`
      en verde, y comprobación manual de que el guardián detecta el defecto:
      añadir temporalmente una segunda lectura, ver el rojo, deshacerlo (la
      traza del rojo, al informe).

- [x] **T9: Guardián del corte (R22).** Escribir
      `tests/test_f017_r22_sin_reescritura_historica.py` en la raíz del
      monorepo: las siete columnas de autor conservan nombre y ancho en las
      **dos** copias del ORM, y no existe en el árbol ningún `UPDATE` sobre
      esas columnas ni ningún `.sql` de migración nuevo.
      Verificación: `python -m pytest tests -q` en verde.

- [ ] **T10: Documentar el corte (R23).** En
      `docs/referencia/partes-proyecto.md`: corregir §5.4 (donde hoy dice que
      `created_by`/`updated_by` llevan `DEFAULT_REVIEWER`, que además es
      falso: llevan `NULL`) y añadir el apartado **«Corte de auditoría
      (F-017)»** en §5, con el criterio `autor IS NULL` ⇔ «anterior a F-017»
      y el hueco `⛔ PENDIENTE: fecha de despliegue`. Añadir la regla corta a
      `docs/ARCHITECTURE.md`. Anotar en `progress/current.md` que la fecha la
      rellena el humano al desplegar.
      Verificación: `python -m pytest tests/test_f017_r23_corte_documentado.py -q`
      en verde (comprueba que el apartado y el criterio están escritos).

- [ ] **T11: Actualizar `azure-apps/partes.md`.** Documentar el nuevo
      significado de `DEFAULT_REVIEWER` en sv4 (etiqueta de la sesión local,
      **no** «quién firma»), que la auditoría del portal usa el principal de
      Easy Auth, y la ruta `GET /whoami`.
      Verificación: MANUAL (humano) — commit **en el repositorio
      `azure-apps`** (`git -C C:/Users/pgris/PycharmProjects/azure-apps commit`),
      local y **sin push**, con el diff enseñado en el informe.

- [ ] **T12: Campaña de mutación y evidencias.** Ejecutar
      `python -m harness.mutacion --feature F-017`, analizar **todos** los
      supervivientes (ninguno en `PENDIENTE`) y cerrar la sección
      «Evidencias» de `progress/impl_F-017.md` con los cuatro números: tests
      ejecutados y resultado, cobertura de las líneas cambiadas, mutantes
      generados y supervivientes, y tiempo de la suite.
      **Ojo con la trampa conocida** (`progress/current.md`, automejora 1):
      `harness/mutacion.py` ejecuta solo la suite del servicio dueño del
      fichero mutado; los guardianes de T9 y T10 viven en `tests/` de la
      raíz, así que sus mutantes saldrán como falsos «supervivientes
      equivalentes». Registrar **qué suite se ejecutó** por fichero.
      Verificación: `progress/mutacion_F-017.md` generado por la herramienta,
      con sus totales reales y cada superviviente analizado.

- [ ] **T13: Listar las verificaciones MANUAL.** Copiar **M1, M1 bis y M2–M4**
      de `requirements.md` §4 a `progress/current.md` con su comando exacto
      (M1 bis ya estará ejecutada en T0: se anota con su resultado real),
      marcadas como pendientes del humano, junto con el aviso de que M2–M4
      necesitan la regla de firewall de `psql-albaranes-rs9k2` que ya está
      pendiente.
      Verificación: MANUAL (humano) — las cuatro entradas presentes en
      `progress/current.md`.

- [ ] **T14: Ejecutar `bash harness/init.sh` en verde.** Tal cual, sin pipes
      ni decoración. Incluye la puerta de cobertura de las líneas cambiadas
      (rama de feature).
      Verificación: `bash harness/init.sh` termina con exit code 0 y la
      puerta de cobertura sale en `[OK]`.
