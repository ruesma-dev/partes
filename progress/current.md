<!-- progress/current.md -->
# Trabajo en curso

Limpiado el 2026-11-16: las secciones anteriores (2026-08-19 a 2026-11-15) están archivadas
tal cual al final de `progress/history.md` («Archivado de current.md · 2026-11-16»).

Ninguna feature activa (`in_progress`, `in_review` ni `human_review`). Última cerrada: F-032
(2026-11-18, sin desplegar; ver abajo).

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
- **sesame-api**: P0 (sacar `.env` de git y rotar el token si lo lleva), P1 (commitear el
  rediseño), P2 (Dockerfile), P3 (contrato ausente ⇒ 404), P4 (su documento en `azure-apps`),
  P5 (RRHH completa Alicante).
- **Manuales M1–M7** (desplegar sesame-api, contraste, redesplegar sv3 y sv4,
  `infra/add_sesame_partes.ps1`, portal, `-Quitar`): comandos en `progress/impl_F-032.md`.
- Menores: 8 avisos de ruff en `services/partes-persistencia/tests/test_f032_campana.py`
  (fixtures importados, mejor en `conftest.py`); fila «Workers: 3» en Evidencias del informe.

