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

