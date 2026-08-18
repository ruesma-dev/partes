<!-- progress/current.md -->
# Trabajo en curso

## F-010 · Saneamiento: resincronizar orm_models.py entre sv3 y sv4

- Estado: `pending`, spec EN REDACCIÓN (spec-author lanzado el
  2026-08-18) · rama `feature/F-010-resincronizar-orm-models` (desde dev
  716a4f7) · rigor estandar · sdd=true. Prerrequisito de F-015 (D6 de
  F-012). Diff real de las dos copias al arrancar: sv3 tiene
  `horas_orig`/`extra_auto` (y comentarios de conciliación) que faltan en
  sv4; sv4 tiene `sigrid_*` (7 columnas) y `UndoLogOrm` que faltan en sv3.


## Notas de contexto para la próxima sesión

- F-012 cerrada el 2026-08-18 (resumen en `progress/history.md`). Merge de
  `feature/F-012-estudio-jornada-semanal` a dev y push pendientes del
  humano.
- MANUAL del humano (F-014): pedir a RRHH/Administración candef 9 en HLOF
  de MO/0006, 0007, 0008, 0031, 0366, 0405, 0456 y DNI en emp de MO/0037;
  después F-014 se cierra con la comprobación por sigrid-api.

- F-004 cerrada el 2026-08-18 (resumen en `progress/history.md`). MANUAL
  del humano: 7 comprobaciones en navegador (Ctrl+F5), pasos en
  `progress/impl_F-004.md`. Merge a dev y push pendientes del humano.

- F-003 cerrada el 2026-08-16 (resumen en `progress/history.md`): entregada
  APAGADA; para encenderla hacen falta las peticiones P1/P2 al proyecto
  sesame-api (desplegarlo + exponer horas de jornada) — están en manos del
  humano. Merge a dev y push pendientes del humano.
- F-002 desplegada: sv5 en MODO PRUEBAS (obra 0404, PRUEBA-IA) hasta que
  el humano valide en navegador y ejecute el paso a modo normal.
- F-013 cerrada el 2026-08-18 (resumen en `progress/history.md`). MANUAL
  del humano: ejecutar `validar_datos_sesame.py` contra sesame-api local y
  validar los números.
- Informe F-013 ejecutado el 2026-08-18 contra sesame-api local (218
  empleados): festivos OK (Madrid 196, Tomares 15, Sevilla 4, Málaga 2,
  Alicante 1 parcial 8/21 — revisar asignación); contratos en Sesame:
  NINGUNO (jornada/reducida sin fuente). Bug daysOff corregido en
  sesame-api (sin commit allí: árbol P2 pendiente). Excel para el humano en
  services/partes-front/logs/festivos_por_trabajador_2026.xlsx (no
  versionado).
- F-011 REPRIORIZADA A BAJA (última del backlog, prio 14 tras el alta de
  F-015/F-016) por el humano el 2026-08-18: sin
  contratos en Sesame no hay fuente de jornada reducida.
- Siguiente feature por prioridad: F-014 (candef en Sigrid, humano) →
  F-010 → F-015 → F-016 → F-005 …
