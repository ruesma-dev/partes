<!-- progress/current.md -->
# Trabajo en curso

Limpiado el 2026-11-16: las secciones anteriores (2026-08-19 a 2026-11-15) están archivadas
tal cual al final de `progress/history.md` («Archivado de current.md · 2026-11-16»).

Feature activa: ninguna. Siguiente: **F-084** (spec aprobada el 2026-11-26, copia `partes-wt-f084`). Última cerrada: **F-082** (2026-11-26, OK del humano: «ok»; desplegada el 2026-11-26, sv4 `r20261126182437`; MANUAL pendientes del humano). Anterior: **F-083** (2026-11-25, OK del humano: «1 hazlo»; desplegada el 2026-11-25, sv5 `r20261125120627`; M4 pendiente de repetir en unos días con la base 416461). Anterior: **F-072** (2026-11-24, desplegada el 2026-11-25 sv2–sv5 `r20261125120627`, **apagada**: variables vacías).

## F-082 · done 2026-11-26 (OK del humano: «ok»; reviewer APPROVED pasada 2, SHA 5a897d3; copia `partes-wt-f082`; **desplegada el 2026-11-26**, sv4 `r20261126182437`, arranque sin errores en Log Analytics; faltan las MANUAL de abajo, que hace el humano)

- T1 (2f033d9): tests en rojo `services/partes-front/tests/test_f082_sin_partida.py` (fase RED, 8 en rojo).
- T2 (55a892c): fila fija «— Sin partida —» en `buildPartidaPicker` (app.js) y celda
  `cell-partida` de obra/parte/trabajador: sin partida + método `manual` ⇒ «sin partida»
  con etiqueta «manual», sin ⚠. Sin cambios de backend. Sin desviaciones de la PARADA 1.
- Informe: `progress/impl_F-082.md`.
- **Verificaciones MANUAL (humano)**, en el portal tras desplegar sv4 (o en local), con
  **Ctrl+F5** antes de empezar para recargar `app.js`; en una obra con líneas sin registrar:
  1. **Detalle de obra** (`/obras/<obra>`) ⇒ ✎ de la celda «Partida» de una línea ⇒ la primera
     fila del desplegable es «— Sin partida —»; elegirla ⇒ la página recarga y la celda dice
     «sin partida» con la etiqueta «manual», sin ⚠. Repetirlo en el detalle de parte (`/partes/<id>`) y de trabajador (`/trabajadores/<clave>`).
  2. **Misma página**, marcar varias líneas de la misma obra ⇒ barra de selección «Editar
     partida» ⇒ sale «— Sin partida —» arriba; elegirla ⇒ todas quedan «sin partida · manual».
  3. **Detalle de una obra sin presupuesto** ⇒ ✎ de una línea ⇒ el panel ofrece «— Sin partida —»
     y debajo «Esta obra no tiene partidas»; elegirla ⇒ «sin partida · manual».
  4. Tras el paso 1, **Deshacer** ⇒ la línea vuelve a su partida (o a su aviso ⚠) de antes.

## F-084 · human_review 2026-11-27 (reviewer principal APPROVED en 986f868; evidencias APPROVED en 34a5dbb; mutación 93/100, 7 equivalentes a aceptar por el humano; copia `partes-wt-f084`)

- T1–T9 y T12 hechas (commits `F-084 T1`…`T9`; azure-apps `e09fd49`, sin push). T10 (mutación)
  y T11 (manual) quedan para el líder y el humano. Informe: `progress/impl_F-084.md`.
- Decisiones menores (detalle en el informe): agrupar por el primer motivo; `recuperar_parte`
  devuelve None si no existe (404); fecha vacía = sin cambio; «Ver PDF» solo con visor, como Conciliar.
- **Verificaciones MANUAL (humano)**, design §12, tras desplegar sv3 y sv4 (en el portal, **Ctrl+F5**
  antes de empezar para recargar `app.js`):
  1. **M1** (solo lectura, base `partes`):
     `SELECT column_name FROM information_schema.columns WHERE table_name = 'parte_documents' AND column_name LIKE 'sustituido%';`
     ⇒ **2 filas**: `sustituido_por_id` y `sustituido_at_utc` (las añade el DDL de arranque).
  2. **M2** (portal, solo lectura): abrir `/problemas` ⇒ el parte `5c1a9b04` sale en «Sustituido por
     otra página del mismo correo» con `89f17181` de sustituto (enlace «ver» a `/partes/89f17181…`);
     y el número del enlace «Problemas» de la navegación = `total` de `GET /api/problemas/resumen`.
  3. **M3** (portal, **escribe**: solo con el OK expreso del humano para esta acción): en `/problemas`,
     «Recuperar» `5c1a9b04` con fecha `25/11/2026` ⇒ si ya hay otro parte activo del 25/11 de esa obra
     con los mismos trabajadores (el reenvío), 409 con el texto «Corrige la fecha o descarta antes el
     otro parte» y ese parte nombrado; entonces «Descartar» `5c1a9b04` ⇒ vuelve a `/problemas` con
     «Parte movido a la papelera», deja de salir allí y en el contador, y aparece en `/papelera`.
     Sin choque, la recuperación da «Parte recuperado» y el parte sale en `/partes` con fecha 25/11;
     «Deshacer» («Recuperar parte») lo devuelve a inactivo con su fecha anterior.
  Resultado, en `progress/manual_F-084.md` (T11).

### F-084 · spec_ready 2026-11-26 (spec-author; copia `partes-wt-f084`)

- Spec escrita: `specs/F-084-partes-con-problemas/` (rama `feature/F-084-partes-con-problemas`).
  Resumen, decisiones y preguntas al líder en `progress/spec_F-084.md`.
- Decisiones abiertas para el humano: D1–D10 (recomendado (a) en todas: sv3 deja rastro en
  dos columnas nuevas y sigue sustituyendo igual; pestaña `/problemas` en sv4 con contador;
  «Recuperar» nuevo con 409 ante choque; retroactivo; poison de sv2/sv3 y sustitución de
  partes congelados, fuera). Rigor `critico` propuesto (D9).
- Preguntas de datos para el líder: retirados de F-061 entre los 112 inactivos y sustituidos
  aprobados o con líneas en Sigrid.

## F-083 · done 2026-11-25 (OK del humano: «1 hazlo»; copia `partes-wt-f083`)

- T1–T5 hechas y commiteadas (T1 9a73523, T2 c43d3be, T3 6fc7ccc, T5 10681ce; T4 al cerrar);
  `azure-apps` 5078dc0 en `main`, **sin push**.
- **Desviación justificada (T2, R22)**: además de los dos subcasos que nombra R22, se enmienda
  el gemelo de pipeline del mismo subcaso en `test_f062_ciz_mismo_dia.py`,
  `test_f062_r11_lo_que_no_es_ciz_posterior_no_lo_impide[fila1]` (un CIV posterior del tramo,
  mismo fichero, mismo comentario `# F-083 R8`). Era el único test fuera de la lista que
  fallaba con la suite completa de sv5, y su aserción contradice R8 y R15: no se puede cumplir
  la spec y conservarla. Los subcasos de otro recurso, `can` ≠ 0 y anterior se conservan.
  Lo valida el reviewer.
- **M0 hecha por el líder el 2026-11-24** (Sigrid `ruesma`, solo lectura, consulta de design §8,
  `truncated: False`): 416318 (20261118, CIV, can 0, `partes:25090`), 416356 (20261119, CIV, can
  0, `partes:25091`) y 416319 (20261120, CIV, can 0, `partes:25092`). Coincide con lo esperado.
- **T6 hecha (implementer, 2026-11-24)**: campaña del líder 19 evaluados, 17 muertos, 2
  supervivientes (`racha_ciz.py:189` y `:196`, `is not None` → veracidad), propuestos como
  **equivalentes, aceptados por el humano el 2026-11-24** («acepto ñas 2 equivalentes»;
  M1 y M3 autorizadas: «aturoizo m1 y m3») (`progress/equivalentes_F-083.py`,
  exit 0). Encargo del reviewer: quitar `list(candidatas)` de `decidir_fin` muere con
  `test_f083_puro_r2_con_un_iterador` (comprobado a mano). RM7: N/A a mi juicio; lo decide el
  reviewer de evidencias. Sin cambios de producción.
- **T7 M1–M3 hechas (implementer, 2026-11-24/25)**: M1, M2 y M3 en verde y limpieza hecha (Sigrid
  PT26/00417 borrado, partes de prueba en la papelera); el cambio CIZ→CIV lo hizo el líder por
  sigrid-api con autorización del humano. Falta M4 tras desplegar sv5 (`progress/manual_F-083.md`).
- Reviewer: principal APPROVED (c25a504) y evidencias APPROVED (cacb373; RM7 aplicada, H1 a
  criterio del humano). Hecho el merge a `dev`, push del humano (34aa5e4) y despliegue
  del humano el 2026-11-25 (sv2–sv5 `r20261125120627`; arranques sin errores en Log Analytics,
  sv5 con `MOVER_CIZ=true` y `OBRA_PRUEBAS_FORZAR=false`). `azure-apps` 5844bc9 (`partes.md`
  3c: «desplegado»), **sin push**. Falta: repetir M4 en unos días (base 416461), que cierra T7.

## F-072 · done 2026-11-24 (OK del humano: «dame codigo para desplegar»)

- T28: 222 evaluados, 178 muertos, 44 supervivientes; 31 muertos con tests nuevos y 13
  **equivalentes aceptados** por el humano el 2026-11-24 («acepto los 13 equivalentes de F-072»).
- T29–T31: hechas por el implementer a petición del humano («haz tu las pruebas»), en verde
  (`progress/manual_F-072.md`). Sigrid limpia (PT26/00417 borrado); partes de prueba en papelera.
  Sin cotejar: el preview real de porcentajes (lectura de `dedicacion` denegada).
- Reviewer, pasada de evidencias: **APPROVED** (d6aa07a), `init.sh` en verde, cobertura 99,7 %.
- Falta: push de `dev` y despliegue (encendido sv5 → sv3 → sv2 → sv4,
  avisar a porcentajes).

## 2026-11-23 · cola tras F-072: F-083 → F-082 → F-080 → F-081

- **F-083** (alta, `todo`, crítico, prioridad 1: la siguiente a implementar por decisión del humano, «f83 ponla la siguiente a implementar»). Caso del correo de Administración de obra (0730, vacaciones 18-20/11): el CIZ del 20 se cambió a mano a CIV en Sigrid y, al reaprobar el 19 («omitido · intermedio»), sv5 no encontró CIZ posterior y escribió uno el 19. Spec lanzada en la copia `partes-wt-f083` (rama `feature/F-083-ciz-solo-fin-de-racha`).
  - **Spec escrita (spec-author, 2026-11-23)**: `specs/F-083-ciz-solo-fin-de-racha/`, F-083 en `spec_ready` en su rama. Resumen y decisiones en `progress/spec_F-083.md`. Decisiones abiertas para el humano: D1–D8 (lo recomendado: solo sv5; cualquier línea posterior de la racha deja el día como intermedio; sv4, el ↻ y `racha_desordenada` sin cambios; respetar el CIZ quitado a mano; bajo `MOVER_CIZ`; nada retroactivo). Aviso: la rama sale de 011bc2a, que lleva F-072 sin fusionar en `dev`.
- **F-081**: spec aprobada por el humano el 2026-11-23 (D1-D8 como se recomendaba; commit db01b37 en su rama, copia `partes-wt-f081`). Espera a F-082 (T15 depende de ella).

## F-072 · desbloqueada 2026-11-21: el humano elige (b) («la b»); anotada en tasks.md encima de T16. F-070 a `todo`.

**Implementer, tras el desbloqueo.** Enmienda (b) hecha y commiteada: RED 6aef54d y código
b66a749 (sv4 manda `partida_metodo` de la línea base; sv5 lo lleva a `LineaEntrada` en reajuste
y franquicia). Después, T16–T27: conflictos por partida, catálogo de entradas, repositorio y
endpoints de sv4, `app.js`, documentación y `azure-apps` (cd58cab, sin push). T32 en verde:
`init.sh` da ENTORNO LISTO y la cobertura, 99,3 %. T28–T31 son para el líder y el humano. Interpretaciones
(i)–(x), en `progress/impl_F-072.md`.

### Bloqueo original 2026-11-21 (implementer, en T16): la guarda de sv5 omite reajustes y franquicias

**Hecho y commiteado** (rama `feature/F-072-postventa-var-como-obras`), T1–T15:
- el gemelo `obras_agrupadas.py` en sv2–sv5, con los ajustes y los tests R4–R11 y R41;
- sv2: la marca, sin consulta de obra, y el prompt;
- sv3: el casado de la entrada, `save_parte` y la conciliación (R14–R22, R42, R43);
- sv5 T14–T15 (f4ea30d): `partidas_de_obra`, `LineaEntrada.partida_metodo`,
  `motivo_partida_agrupada` y el paso 2d de `RegistroPipeline.preparar` (R36, R37, R39).
- Suites en verde: sv5 1665 passed (suite completa), sv3 2943 passed y 2 skipped, sv2 465 passed.
- Las trazas RED de T1–T14 están guardadas. El informe `progress/impl_F-072.md` aún no está escrito.

**Motivo: la spec se contradice.** Design §6 pone la guarda (R36) en `RegistroPipeline.preparar`. Una
línea sin `partida_metodo` de entrada se omite. Pero design §10 dice que no se tocan
`reajuste_pipeline.py` ni `franquicia_pipeline.py`, «que copian obra y partida de líneas que ya
pasaron la guarda». No es así: los dos llaman a `preparar` con una `LineaEntrada` que construyen
ellos, con `partida_ide` y `partida_cod` y **sin** `partida_metodo`. `FranquiciaIn` y
`LineaReajusteIn` ni siquiera tienen el campo. Con las agrupadas encendidas, en POSTV2 y en VAR:
- la franquicia de un trabajador cuyo día de ajuste cae en una entrada se omite;
- las extras nuevas del reajuste también, con `partida_agrupada: sin entrada var: …`.

Comprobado con el `preparar` real y los dobles de `tests/f072_comun.py`: la extra
`(obra VAR, partida 91012 «29»)` sale con `omitir`. Arreglarlo sin decidir es improvisar: o se
tocan ficheros que §10 excluye, o se cambia el contrato sv4→sv5.

**Opciones** (para el líder y el humano):
- **(a)** `preparar(…, guarda_agrupada=True)`, y reajuste y franquicia pasan `False`. Toca los 2
  ficheros de §10, unas 2 líneas cada uno. En esas dos vías solo se comprueba la marca; la hoja
  activa y el universo VAR también se dejarían de comprobar.
- **(b)** Llevar `partida_metodo` por `FranquiciaIn`, `LineaReajusteIn` y `OpReajuste`, y que sv4
  lo mande desde la línea base. La guarda se aplica siempre, como dice R36. Toca sv4 (los
  payloads de reajuste y franquicia) y los 2 pipelines de sv5.
- **(c)** Dejarlo así y documentarlo como límite: en las obras agrupadas no hay reajuste de
  extras nuevas ni franquicia; sv4 ve el motivo `partida_agrupada:` de la línea.
- **Recomendación: (b).** Es la única que mantiene R36 para toda escritura en una obra agrupada.
  (a) es la más barata.

**Interpretaciones ya aplicadas, para que el reviewer las valide.** Irán también en el informe:
- **(i)** Los alias solo se leen en sv2 y sv3 (design §5–§6), pese al R1 literal.
- **(ii)** El segundo paso de `casar_var` es «la única con el mismo número inicial», al pie de
  la letra.
- **(iii)** En la forma base, un resultado mixto da `agrupada_varias_entradas`; varios fallos
  distintos dan `agrupada_sin_entrada`.
- **(iv)** Desviación justificada: el reemplazo del mismo día de `save_parte` (sv3) cuenta
  también la entrada. Si no, dos entradas del mismo día se pisarían.
- **(v)** `tests/test_f038_lectores_sigrid.py` (raíz) lista ficheros, no métodos.
  `partidas_de_obra` vive en `sigrid_write_client.py`, que ya está en la lista. R39 se prueba en
  `test_f072_guarda.py` (`max_rows` y `truncated`) y el guardián de raíz no cambia.
- **(vi)** Para T17, `lineas_existentes` solo leerá `hmores.paride` cuando se le pida, con un
  parámetro nuevo. Si lo lee siempre, rompe `test_f053_cliente_anular.py::…sql_exacto`, un test
  anterior que T25 prohíbe tocar. Comprobado: cae.

**`bash harness/init.sh` al bloquear** (2026-11-21): 2 fallos.
- **Raíz**: `test_f019_r22_…timeout_literal` caía por el `timeout=120` literal de
  `tests/test_f072_equivalencia_porcentajes.py`. Ya está arreglado con `escalar_timeout`, en
  0159869: 54/54.
- **PUERTA COBERTURA**: 81,4 % (669/822) contra el 90 % de `critico`. Es esperable a mitad de la
  feature. En esa pasada la suite de raíz paró en el primer fallo. Además, las copias del gemelo
  en sv2, sv4 y sv5 solo las ejercitan en parte sus propias suites. Se mide de nuevo en T32.

El resto, en verde: sv2 por caché, sv3 2943 passed y 2 skipped, sv4 3824 passed y sv5 1665
passed; PUERTA TAMAÑO también en verde: impl 88/220.

**Para retomar:** con la opción decidida, seguir por T16 (con el arreglo de la opción, si toca
código), y luego T17–T27 y T32. T28–T31 quedan para el líder y el humano.

## F-072 · spec escrita 2026-11-20 (pendiente de aprobación)

La spec está en `specs/F-072-postventa-var-como-obras/` (requirements 150/150, design 248/250,
T1–T32). El resumen, los hallazgos y las decisiones están en `progress/spec_F-072.md`. Rigor
crítico.

Las decisiones abiertas para el humano son DA1–DA12, todas con recomendación (a):
- forma en el papel;
- alias de postventa;
- sv2 sin relectura;
- un gemelo nuevo en la lista cerrada (sv3, sv4 y sv5);
- la entrada guardada sin columnas;
- obra cerrada solo como postventa (no aplica);
- VAR y POSTV2 fuera del selector normal;
- conflictos de sv5 por partida;
- partes ya guardados;
- bandeja sin cambios;
- configuración sin valores por defecto;
- sincronizar una entrada (fuera).

Conviene tener M0 (T29, consulta de solo lectura) antes de cerrar DA1 y DA9.

**Enmienda del humano del 2026-11-20** («V y número, POST y número, y variantes»), incorporada a
la spec:
- R41–R43;
- DA2 con los alias `POST` y `V`;
- DA13 nueva (colisión con una obra real: `150702-V` y la antigua `POSTV`);
- el gemelo pasa también a sv2.

La lectura de Sigrid (solo lectura) encontró `POSTV2` y `VAR` en las empresas 1 y 28. Detalle en
`progress/spec_F-072.md`.

## F-078 · DONE 2026-11-20, sin desplegar (alias DORSAN de la empresa 28)

Express, APPROVED en pasada única (`progress/review_F-078.md`); OK del humano «push hecho ok, a
todo». Integrada en `dev` en local. Pendiente del humano: redesplegar sv3; mover desde el portal
los 3 partes «Dorsan» (11–13/11) y el del 10/11 a la obra 0730 de Porsan; caso Alberto (DNI mal
en la plantilla de Porsan, casar MO/0018 en Conciliar); nombre de la obra 0730 de Porsan en Sigrid.

## F-077 · DONE 2026-11-19, sin desplegar (sv3 lee los festivos de Sesame HR, sin pasarela)

Review APPROVED en tres pasadas (`progress/review_F-077.md`): la 1 pidió 3 cambios fuera de
producción; la 2 los dio por resueltos junto con la enmienda de R13 (0 DNIs ⇒ fallo, decisión del
humano «a»); la 3 (evidencias) aprobó condicionado a la aceptación de los 3 equivalentes, que el
humano dio literalmente el 2026-11-19: «acepto» (anotada en `progress/mutacion_F-077.md`).
Campaña: 85 evaluados, 73 muertos, 9 supervivientes muertos con test, 3 equivalentes aceptados.
Integrada en `dev` en local.

Pendiente del humano (nada de esto lo hace el arnés): **M0–M6** (T17–T18), comandos en
«Verificaciones manuales pendientes» de `progress/impl_F-077.md`: rotar el token y cargar
`SESAME-TOKEN` con `add_secrets_partes.ps1`, contraste e `--impacto`, redespliegue apagado,
encendido con `add_sesame_partes.ps1`, portal y `-Quitar`. Sigue P5 de F-032 (RRHH Alicante).
Observaciones sin bloqueo: O2 (URL pública en `features.json`), O3 (`ultimas_paginas`
compartido), O4 (el doble `_ProveedorSinJornada` revienta también ante `hasattr`).

## F-077 · vuelta a in_progress 2026-11-19 (review 1 CHANGES_REQUESTED)

Cambio 3 de la review hecho por el líder (5e6ffb1). El humano elige **(A)** para O1 («a»):
enmienda de R13, índice con empleados pero 0 DNIs ⇒ fallo (anotada en requirements R13,
design §5.2 y tasks T5). Implementer: cambios 1–2 de `progress/review_F-077.md` y la enmienda.

## Abierto fuera del código (2026-11-16)

- **Verificaciones manuales** (líder, por lectura, 2026-11-16 ⇒ `progress/verificacion_manuales_2026-11-16.md`):
  OK F-047 M1 (por indicios), F-050 M2–M3, F-062 M6, F-055 M3. **Del humano**: F-068 M1 (falta un
  casado real), F-064 M2 (dos usuarios en el mismo navegador), F-046 M6 (pulsar «Aplicar»; el caso
  del 14/10 ya no existe; queda una fila `pendiente` en `reparto_pendiente`, recurso 2636243, 09/10).
  Hallazgo: la espera real de F-047 es 41–87 s (mediana 56 s), no 20–40 s: revisar el texto de R19.
- **Obra 0721, adjunto 4936_001.pdf**: reactivar la página 7 (doc 9d453e26) solo después de que
  Administración pase la página 11 al 29/10 (autorización del humano, escritura puntual).
- **Posible bug**: deshacer un cambio de fecha deja líneas con `fecha_int` NULL (doc 5ea328f7).
  En investigación ⇒ `progress/explore_bug_deshacer_fecha.md`.
- Las verificaciones manuales de F-020 a F-045 (septiembre–octubre) se dan por superadas por
  uso en producción (decisión del humano 2026-11-16).

## F-077 · in_review 2026-11-19 (líder)

El líder recortó su propia enmienda de design §4 a 2 líneas sin cambiar lo decidido (131ad40):
`design.md` 250/250. `bash harness/init.sh` en verde (ENTORNO LISTO; cobertura 99,2 %, 263/265).
T19 marcada; F-077 a `in_review`; siguiente: reviewer.

Manuales del humano M0–M6 (token rotado y `SESAME-TOKEN` en el Key Vault, contraste,
impacto, redespliegue apagado, encendido, portal y `-Quitar`): comandos en «Verificaciones
manuales pendientes» de `progress/impl_F-077.md`.

### Bloqueo en T19 (implementer, 2026-11-19): `design.md` pasaba del tope de tamaño

**Hecho.** T11 está commiteada (914f8d7) con la enmienda aplicada. Los 7 tests pasan y no cae
ninguno más:

| Suite | Resultado |
|---|---|
| sv4 | 3809 passed |
| sv3 | 2722 passed, 2 skipped |
| Raíz F-077 | 37/37 |

`PUERTA COBERTURA` da 99.2 % (263/265). El informe está en `progress/impl_F-077.md`.

**Motivo.** `bash harness/init.sh` termina con `1 comprobaciones fallidas`:
`PUERTA TAMAÑO: specs/F-077-sesame-directo-sin-pasarela/design.md: 252 líneas > tope 250`.

- Todo lo demás de `init.sh` está en verde.
- Lo que pasa de 250 son las 4 líneas que la enmienda añadió a design §4 (commit 76183db).
- Un reflujo sin cambiar palabras no ahorra ni una línea, porque la prosa ya va a ~97
  columnas. Bajar de 250 obliga a reescribir texto de la spec aprobada, y eso no le toca al
  implementer.

**Propuesta para el líder y el humano.** Recortar 2 líneas de design §4 sin cambiar lo
decidido. Por ejemplo, dejar la enmienda en «sv4, enmienda del 2026-11-18: el doble
`CalendarioNoFiable` de `test_f056_decisiones.py` deja de pasar `cliente=None`; arregla sus 4
tests y los 3 de `test_f032_sin_bloqueo.py` y `test_f056_vista.py`». Esa frase ocupa 2 líneas
en lugar de 4. Hecho eso, `init.sh` en verde, T19 marcada y F-077 a `in_review`.

## F-077 · desbloqueada 2026-11-18 (enmienda aprobada por el humano: «ok»)

Se amplía la lista cerrada de design §4 con `test_f056_decisiones.py` (una línea del doble
`CalendarioNoFiable`); anotada en `tasks.md` (T11). F-077 vuelve a `in_progress` y sigue en T11.

### Bloqueo original (implementer, T11): test fuera de la lista cerrada

**Motivo.** Con T11 aplicado (sv4 sin Sesame: `CalendarioProvider(activo=...)` en vez de
`cliente=`, design §5.4), la suite de sv4 da **7 failed, 3802 passed** (24 min). Los 7 caen en
ficheros que **no** están en la lista cerrada de design §4:

- `services/partes-front/tests/test_f056_decisiones.py`: `test_f056_r6_preflight_calendario_no_fiable`,
  `test_f056_r6_ejecutar_ajustar_sin_calendario_es_409`,
  `test_f056_r16_ejecutar_no_ajustar_sin_propuesta_si_se_guarda`,
  `test_f056_r8_ejecutar_ajustar_tras_rechazo_con_dia_sin_calendario`;
- `services/partes-front/tests/test_f032_sin_bloqueo.py`: `test_f032_r23_dia_de_ajuste_con_calendario_no_fiable`,
  `test_f032_r23_ajustar_con_calendario_no_fiable_se_decide` (importan el doble de `test_f056_decisiones.py`);
- `services/partes-front/tests/test_f056_vista.py`: `test_f056_r45_r6_decidir_ajustar_con_calendario_no_fiable_se_decide`.

**Causa única.** El doble `CalendarioNoFiable` de `test_f056_decisiones.py:397-401` hace
`super().__init__(cliente=None, respaldo_holiday_name=lambda d: None)` →
`TypeError: CalendarioProvider.__init__() got an unexpected keyword argument 'cliente'`. No es
un cambio de comportamiento: el doble solo sobrescribe `fiable_para`.

**Arreglo propuesto (para decidir el líder o el humano).** Ampliar la lista cerrada de design §4
con `test_f056_decisiones.py` y cambiar esa línea a
`super().__init__(respaldo_holiday_name=lambda d: None)` (el defecto `activo=False` equivale al
`cliente=None` de antes). Una línea; arregla los 7.

**Estado del trabajo.** T1–T10 y T12–T15 commiteadas (`fcafdad` T12, `f3a1db3` T13, `f9b9ec9`
T14–T15; `azure-apps` `a568995`, commit aparte, sin push). **T11 aplicada en el árbol y SIN
commitear** (su verificación no está en verde por lo anterior): settings, `calendario_provider.py`,
`web/app.py`, `trabajador_detail.html`, `logging_config.py` de sv4 y los `git rm` de
`infrastructure/sesame/`, `validar_datos_sesame.py` y sus tests (ya en el índice). Fuera de T11
todo lo demás está verde: suite de sv3 2722 passed / 2 skipped; guardianes de raíz F-077 37/37.
Los `.env.example` de sv3 y sv4 (no versionados) se han puesto al día con los nombres nuevos.
Pendiente tras desbloquear: commit de T11, T19 (`init.sh`), informe `progress/impl_F-077.md`.
T16 (mutación) y T17–T18 (manuales) quedan sin marcar, como se pidió.

## F-077 · spec escrita 2026-11-18 (spec_ready, pendiente de aprobación)

Spec en `specs/F-077-sesame-directo-sin-pasarela/`, resumen y DAs en `progress/spec_F-077.md`.
Decisiones abiertas para el humano: DA5–DA14 (normalización del DNI, «no encontrado», inactivos,
índice fallido a mitad, quitar el cliente de sv4, interruptor `FESTIVOS_SESAME_ENABLED`,
nombres, token de la herramienta, URL en infra, solo HTTPS), todas con recomendación (A).
F-077 sustituye a las M1–M7 y P0–P4 de F-032 (P5, RRHH, sigue).

## Siguiente en el backlog

F-072 (prioridad 1, sin spec) · F-057 (`spec_ready` desde 2026-10-24: refrescar contra F-068
antes de implementar) · F-070, F-071, F-073, F-067 sin spec · F-074 (consulta de obra de sv2,
prioridad la más baja).

## F-032 · DONE 2026-11-18, sin desplegar (festivos por trabajador desde Sesame)

Review APPROVED en tres pasadas (`progress/review_F-032.md`); la condición de la pasada 3 se
cumple con la **aceptación literal del humano del 2026-11-18: «acepto. push hecho. mejora como
encargo.»**, que cubre los 3 equivalentes y los 11 muertos por la raíz (anotada en cada uno en
`progress/mutacion_F-032.md`). Integrada en `dev` en local. La mejora del selector de la
herramienta de mutación queda como encargo en `arnes-base`.

Pendiente del humano (nada de esto lo hace el arnés):
- ~~sesame-api P0–P4~~ y ~~manuales M1–M7~~: **sustituidos por F-077** (Sesame HR directo, sin
  pasarela; decisión del humano 2026-11-18). Sigue **P5** (RRHH completa Alicante).
- Menores: 8 avisos de ruff en `services/partes-persistencia/tests/test_f032_campana.py`
  (fixtures importados, mejor en `conftest.py`); fila «Workers: 3» en Evidencias del informe.


## F-078 · human_review 2026-11-19 (express): alias DORSAN de la empresa 28 en empresas_membrete.yaml; informe en `progress/impl_F-078.md`.

## F-072 · spec_ready 2026-11-20 (pendiente de aprobación del humano)

Spec en `specs/F-072-postventa-var-como-obras/` (requirements 150, design 248, T1–T32; T29–T31
manuales); resumen y DA1–DA12 en `progress/spec_F-072.md`. Rigor `critico`. F-071 en `todo`.
M3 de F-077 hecha (despliegue apagado de sv3 y sv4 con F-032, F-077 y F-078, 2026-11-20).

## F-072 · in_progress 2026-11-21 (spec aprobada por el humano: «ok», DA1–DA13 en (a))

Lo decidido está en la columna «Decidido» de design §13. Siguiente: implementer (rigor `critico`).

## F-072 · in_review 2026-11-21 (líder)

Implementer: T1–T27 y T32 hechas (`progress/impl_F-072.md`); `init.sh` en verde, cobertura 99,3 %
(1065/1072). `azure-apps` cd58cab sin push. Siguiente: reviewer principal; después, campaña (T28).

## F-072 · vuelta a in_progress 2026-11-21 (review 1 CHANGES_REQUESTED)

`progress/review_F-072.md`: cambios 1–2 al implementer (sv4 `catalogo_entradas.py`:
`partida_capitulo` con la categoría y tests del desempate de `IndicePostventa`); cambio 3 (este
apunte) hecho por el líder. Decisiones abiertas para el humano: **D1** (segundo paso de
`casar_var`, R8) y **D2** (falso conflicto en `ReajustePipeline._choques`). Spec y tareas:
`specs/F-072-postventa-var-como-obras/tasks.md`; informe: `progress/impl_F-072.md`.

Manuales pendientes del humano (comandos completos en `tasks.md`):
- **T29 · M0** (antes de encender): consulta de solo lectura a la base `partes` sobre
  `parte_documents` (partes en POSTV2/VAR o con marca leída).
- **T30 · M1**: sv4 en local con `POSTVENTA_OBRA_COD=POSTV2 VAR_OBRA_COD=VAR
  VAR_PARTIDA_DESDE=29`; contar `/api/sigrid/obras` por agrupada y empresa y comparar con el
  preview de dedicación de porcentajes.
- **T31 · M2**: portal en local en modo pruebas (obra 0404, `OBRA_PRUEBAS_FORZAR=true`): un parte a
  `VAR-<n>` y otro a `Postv-<obra>`, aprobar, `prueba_escritura_sigrid.py verificar`, una línea
  sin marca en POSTV2 omitida con `partida_agrupada:`, y `prueba_escritura_sigrid.py limpiar --ejecutar`.

## F-072 · enmienda 2026-11-23 (humano: «D1 c, D2 a»)

R8 (segundo paso de `casar_var` solo si lo leído es solo un número) y R38 (también
`ReajustePipeline._choques`) enmendados en requirements y design; nueva T33 en `tasks.md`. Los
cambios 1–2 de la review 1 ya están (67d48e4). Siguiente: implementer con T33; luego reviewer
(pasada 2) y campaña.

## F-072 · in_review 2026-11-23 (líder): pasada 2 del reviewer

Cambios 1–2 de la review 1 (67d48e4) y T33 (enmienda D1 c / D2 a, 1adb0d2) hechos; `init.sh` en
verde, cobertura 99,7 %. Siguiente: reviewer pasada 2; después, campaña (T28).
