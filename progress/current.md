<!-- progress/current.md -->
# Trabajo en curso

Ninguna feature `in_progress`. Última sesión: 2026-08-18. `dev` = 97fc0a8
(merge de F-010) y en el remoto. Al retomar: `bash harness/init.sh` y
seguir el orden del backlog de abajo.

## Orden del backlog (por prioridad en `harness/features.json`)

1. **F-014** (documental, sdd=false) — candef 9 en Sigrid. La ejecuta
   RRHH/Administración a mano; el arnés solo redacta la petición y
   comprueba después por sigrid-api. Estado real: PENDIENTE de que el
   humano lo pida/haga. No bloquea la spec de F-015, sí su merge.
2. **F-015** (estandar, sdd=true) — jornada semanal derivada del candef +
   último laborable + tabla `empleado_jornada`. Prerrequisitos: F-010 (ya
   done) y F-014. Siguiente acción del líder: PARADA 1 y spec-author, con
   los requisitos R10–R25 del bloque B de `specs/F-012-.../requirements.md`
   como base (decisiones firmes ya escritas en `design.md` §9.1).
3. **F-016** — pantalla de administración de `empleado_jornada` (tras F-015).
4. F-005 GRAPH_KEY→KV · F-006 tipo_hora ext · F-007 prompt sv2 + evals ·
   F-008 roles · F-009 automejoras del arnés (lista larga en history.md:
   AM de F-013, F-004 y F-010) · F-011 jornada reducida (última; fuente
   candidata `empleado_jornada` + `emphis.porjorlab`).

## MANUAL pendiente del humano (acumulado)

- **F-002 (Azure):** validar en navegador la aprobación asíncrona (⏳
  encolado → ✓ PT26/…, obra 0404 en modo pruebas), limpiar 0404
  (`python prueba_escritura_sigrid.py limpiar --ejecutar` en sv5) y pasar
  sv5 a modo normal (`az containerapp update -n ca-sv5-transfer -g $RG
  --set-env-vars OBRA_PRUEBAS_FORZAR=false`).
- **F-003:** encendido cuando sesame-api esté desplegado (P2) — variables
  SESAME_* en sv3 y sv4 a la vez + secreto `sesame-api-key` en kv-partes.
  Ojo: encender contra URL muerta bloquea aprobaciones por diseño.
- **F-004:** 7 comprobaciones en navegador con Ctrl+F5 (pasos al final de
  `progress/impl_F-004.md`).
- **F-010:** M1/M2 — arrancar sv3 y sv4 en local, «esquema inicializado
  (118 sentencias complementarias)» en ambos, índice
  `ix_parte_registros_deleted_at_utc` en `pg_indexes`, columnas 7/47/56/7
  (`progress/impl_F-010.md` §6). M3 redeploy cuando decida.
- **F-013:** validar el Excel `services/partes-front/logs/
  festivos_por_trabajador_2026.xlsx` (no versionado): Alicante 8/21
  (Antuane Gavilán) y asignaciones por centro.
- **F-014:** pedir candef 9 en la hora por defecto HLOF de MO/0006, 0007,
  0008, 0031, 0366, 0405, 0456 y DNI en `emp` para MO/0037.
- **sesame-api (otro repo, del humano):** commitear el árbol P2 (incluye
  el fix `daysOff` del 2026-08-18), desplegar, doc en azure-apps (P3);
  `contract_not_found` → 404 en vez de 502; su `.env` ya apunta a EU4.
- **Sesame HR (RRHH):** completar el calendario Alicante; contratos vacíos
  (0/218) — decidir si se cargan.
- **Cambio de modelo Gemini** en sv2 (comando dado; actualizar
  `infra/create_capps_partes.ps1:38`).

## Notas de contexto

- F-013 (2026-08-18): informe contra sesame-api local, 218 empleados;
  festivos OK (Madrid 196, Tomares 15, Sevilla 4, Málaga 2, Alicante 1
  parcial); contratos en Sesame: NINGUNO ⇒ jornada/reducida sin fuente en
  Sesame; F-011 repriorizada a baja por eso.
- F-012 (2026-08-18): decisiones firmes del humano — jornada semanal
  DERIVADA del candef ({8:40, 9:42}, env espejo sv3+sv4); resto en el
  ÚLTIMO LABORABLE de la semana (festivo cuenta como jornada); excepciones
  en `empleado_jornada`; candef desconocido → 5×candef + WARNING; sin
  calendario → viernes.
- azure-apps es un repo git LOCAL sin remoto (decisión del humano): tiene
  commits 8f55505 (F-010) y anteriores; no proponer push.
- Automejoras del arnés propuestas por reviewers (F-013 AM-1..3, F-004,
  F-010) esperan decisión del humano en F-009; genéricas ⇒ arnes-base.
