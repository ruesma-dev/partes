# F-024 · Informe del implementer

Rama `feature/F-024-lineas-encoladas`. Rigor **critico**. Spec aprobada por
el humano el 2026-10-01 (DA1–DA15 según recomendación, DA15 incluida).

## T1 · Inventario de tests afectados

Búsqueda en `services/partes-front/tests`, `services/partes-transfer/tests`
y `tests/` de: payload con líneas `registrado`, `MOTIVO_LINEA_REGISTRADA` y
respuesta de `/api/aprobar/encolar`.

- **Payload con líneas `registrado`**: ninguno. Todos los tests de
  aprobación (F-002 `test_f002_aprobar_encolar`, `test_f002_degradacion`,
  `test_f002_mutantes`; F-003 `test_f003_r18_preflight_festivos`,
  `test_f003_r23_bloqueo_registro`; F-017 `test_f017_aprobacion_firmada`,
  `test_f017_endpoints_firmados`) siembran líneas con `sigrid_estado` vacío.
  Los que siembran `registrado` (F-004 `test_f004_endpoints_congelados`,
  `test_f004_vistas_candado`, F-023 `test_f023_catalogo_empresa`) no
  aprueban: prueban congelación, papelera y reasignación.
- **`MOTIVO_LINEA_REGISTRADA`**: ningún test compara su texto (F-004 solo
  comprueba `is not None` y que difiere del de `encolado`).
- **Respuesta de `/api/aprobar/encolar`**: `test_f002_aprobar_encolar`
  (`modo`, `peticion_id`, `encoladas`) y `test_f002_degradacion` (`ok`,
  `modo`). R27 solo AÑADE `registro_ids` y `excluidas`: no se rompen.
- `ESTADOS_EN_VUELO`: ningún test lo referencia por nombre.

Conclusión: ningún test existente hay que adaptar por DA7; se confirma en
T10 con las suites de F-002, F-003 y F-017 en verde.
