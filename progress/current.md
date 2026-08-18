<!-- progress/current.md -->
# Trabajo en curso

Sesión 2026-08-19. **F-014 `blocked`** (a la espera de RRHH/Administración,
motivo abajo). Ninguna feature `in_progress`. Rama de trabajo viva:
`feature/F-014-candef-9-sigrid` (4 commits, sin mergear a `dev` porque la
feature no está `done`). `dev` = `cf77e6a`.

## F-014 · bloqueada a la espera de RRHH (2026-08-19)

**Motivo del `blocked`**: el `acceptance` 2 exige verificar por sigrid-api,
tras el cambio, que los 7 recursos tienen `candef = 9` y que `MO/0037` tiene
DNI. Ese cambio es de **datos maestros en Sigrid** y lo ejecuta a mano
RRHH/Administración: ningún agente escribe ahí. Hasta que no se ejecute, no
hay nada que verificar.

Entregado y **APROBADO por el reviewer** (`progress/review_F-014.md`, dos
pasadas):

- `progress/peticion_F-014.md` — la petición para RRHH, con el porqué en
  lenguaje de negocio, la tabla recurso a recurso, qué NO se toca, el
  procedimiento de 5 pasos, la verificación posterior (V1/V2/V3 con su
  resultado esperado en los 3 escenarios) y el **texto de correo copiable**
  (§7).
- `progress/impl_F-014.md` — línea base medida contra Sigrid el 2026-08-19
  en solo lectura, hallazgos y evidencias. El reviewer re-midió todo por su
  cuenta: coincide dato por dato.

**Para retomar**: `git checkout feature/F-014-candef-9-sigrid` y seguir el
apartado 6 de `progress/peticion_F-014.md`.

### Lo que falta para cerrarla (en orden)

1. **El humano envía la petición** a RRHH/Administración (§7 de
   `peticion_F-014.md`).
2. **RRHH ejecuta en Sigrid**: `candef` 8 → 9 en la línea `HLOF` de las 7
   fichas (o 6, según decidan) y el DNI de `MO/0037`.
3. **RRHH responde qué decidió con `MO/0007`** (ficha 2146403: figura de
   alta pero no registra partes desde el 2026-02-04, así que nunca llegó a
   hacer el régimen de 9 h). Sin esa respuesta el esperado de V1 y V2 es
   ambiguo entre los escenarios A, B y C.
4. **Ejecutar V1, V2 y V3** en solo lectura y anotar el resultado real en
   `progress/impl_F-014.md`.
5. **Segunda revisión** que verifique el punto 4 → `done` → merge.

### Hallazgos que conviene no perder

- **Los códigos `MO/NNNN` NO identifican una sola ficha de recurso.**
  `MO/0006` devuelve 5 fichas (4 de alta) y bajo `MO/0006`, `MO/0007` y
  `MO/0008` hay homónimas **de alta, misma categoría, misma hora por defecto
  `HLOF` y también con `candef = 8`**: indistinguibles salvo por `res.ide`.
  Por eso la petición identifica por código + `res.ide` + categoría.
- **`MO/0031` tiene dos fichas de alta que registran partes en 2026**: la
  correcta (2714845, OFIC. 1ª ALBAÑIL) y otra (537335, ENCARGADO DE OBRA,
  hora por defecto `MENC`, `candef` 1). Ahí desempata la categoría.
- **`MO/0037` sigue sin DNI** (`res.conide = 0`) y registró parte el
  2026-08-19: el hueco es actual y afecta ya al cruce con calendario y
  festivos de F-003.
- **ORDEN DURO**: F-015 **no se mergea** hasta que el punto 4 salga en
  verde. Es el riesgo §10.6 de F-012: con la cuadrilla aún a `candef = 8`,
  la regla nueva marcaría sus viernes de 6 h como incompletos y generaría
  **+2 h/semana de extra automática falsa** por trabajador.

## Orden del backlog (por prioridad en `harness/features.json`)

1. **F-014** — `blocked`, ver arriba. Solo la desbloquea RRHH.
2. **F-015** (estandar, sdd=true) — jornada semanal derivada del candef +
   último laborable + tabla `empleado_jornada`. Base: requisitos R10–R25 del
   bloque B de `specs/F-012-.../requirements.md` y las decisiones firmes de
   su `design.md` §9.1. Su **spec** no depende de F-014; su **merge** sí.
3. **F-016** — pantalla de administración de `empleado_jornada` (tras F-015).
4. F-005 GRAPH_KEY→KV · F-006 tipo_hora ext · F-007 prompt sv2 + evals ·
   F-008 roles · F-009 automejoras del arnés (lista larga en history.md:
   AM de F-013, F-004, F-010 y ahora F-014) · F-011 jornada reducida
   (última; fuente candidata `empleado_jornada` + `emphis.porjorlab`).

## MANUAL pendiente del humano (acumulado)

- **F-014 (2026-08-19) — EN ESPERA POR DECISIÓN DEL HUMANO, NO ENVIAR
  TODAVÍA:** la petición de `progress/peticion_F-014.md` §7 está lista y
  aprobada, pero **el correo a RRHH no sale hasta que F-015 esté
  implementada y lista para desplegar**: F-014 SIN F-015 deja a esos 7
  trabajadores **peor que hoy** (−3 h/semana de extra negativa). El aviso
  está también en la cabecera del propio documento. Cuando salga y RRHH
  avise: ejecutar V1/V2/V3 del apartado 6 (solo lectura, script de usar y
  tirar fuera del repo, credenciales `SIGRID_API_*` de sv3).
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
- **Deuda detectada el 2026-08-19 (fuera de alcance de F-014)**:
  `services/partes-front/consulta_reshor_recursos.py` tiene 4 DNIs y
  nombres de personas reales **hardcodeados y versionados** (líneas 27-31)
  y apunta a una ruta `.env` de otro repositorio. Pendiente de decisión del
  humano sobre si se limpia y en qué feature.
- azure-apps es un repo git LOCAL sin remoto (decisión del humano): tiene
  commits 8f55505 (F-010) y anteriores; no proponer push.
- Automejoras del arnés propuestas por reviewers (F-013 AM-1..3, F-004,
  F-010 y F-014) esperan decisión del humano en F-009; genéricas ⇒
  arnes-base. Las de F-014 (`progress/review_F-014.md` §11): (A) checkpoint
  nuevo para features cuyo entregable es una **petición a un tercero**
  (clave unívoca verificada, apartado «qué NO se toca», verificación
  escrita ANTES con control de daños, resultado esperado en TODOS los
  escenarios, barrido de datos sensibles porque el documento sale del
  repo); (B) generalizar la regla del reviewer «si el entregable es una
  medición, se **re-ejecuta** en solo lectura en vez de leerla» — es lo que
  destapó el defecto D1 de esta feature.
