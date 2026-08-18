<!-- progress/spec_F-015.md -->
# F-015 · Jornada semanal derivada del candef y último laborable — informe del spec-author

- Rama: `feature/F-015-jornada-semanal-candef` (ya existía; no se ha creado
  otra, no hay push ni PR). Rigor `estandar`, `sdd: true`.
- Fecha: 2026-08-19. **No se ha escrito ni una línea de código de producción.**
- Entregable: `specs/F-015-jornada-semanal-candef/` con `requirements.md`,
  `design.md` y `tasks.md`.
- `bash harness/init.sh`: **verde** (exit 0), con la puerta de cobertura en
  N/A porque F-015 todavía no cambia líneas Python frente a `dev`.

## 1. Qué he redactado

**`requirements.md`** — 25 requisitos EARS con criterios de aceptación y
nombre de test por requisito.

- **R10–R28 se heredan literalmente del bloque B de F-012** (con su
  numeración original, para que la trazabilidad estudio → spec → test sea
  directa y valgan los nombres `test_f015_rNN_…` que ya proponía el estudio).
  Se han completado con criterios de aceptación concretos y casos límite.
- **R27 queda RESERVADO**: es la pantalla de administración, y es F-016.
- **R29–R35 son nuevos**, y cubren lo que el estudio dejó como trabajo de
  diseño: guardián de F-010 a cinco tablas (R29), DDL generado del ORM (R30),
  congelación D7 (R31/R32), variable espejo verificada por test (R33),
  documentación (R34) y la **puerta de entrega de F-014** (R35).
- Tabla de trazabilidad **escenario A–R de F-012 → requisito → test**,
  incluidos los de regresión (K, L) y los dorados de F-003.
- Apartado explícito de **fuera de alcance**: F-016 (UI), F-011 (jornada
  reducida), F-014 (Sigrid), sv1/sv2/sv5, columnas nuevas en
  `parte_registros`, librería compartida.

**`design.md`** — servicios y justificación del LÍMITE DE SERVICIO, modelo de
resolución paso a paso, ficheros a crear / modificar / **no tocar** (rutas
exactas), firmas del resolutor gemelo, cambios de sv3 y sv4, DDL de
`empleado_jornada`, configuración, plan de pruebas (con los MANUAL del
humano), riesgos, alternativas descartadas, **8 decisiones propias (DA1–DA8)**
y **5 dudas** para el humano.

**`tasks.md`** — 13 tareas atómicas (T1…T13), ordenadas por dependencia, cada
una con su verificación; T12 es MANUAL del humano y T13 es `init.sh` en verde
+ campaña de mutación. La puerta de merge de F-014 va escrita en cabecera.

Antes de diseñar he leído el código real: los dos `jornada_resolver.py`,
`RecursoConciliador._reclasificar_extras_jornada` y `_es_no_laborable`,
`sqlalchemy_parte_repository.revert_extras_auto` /
`fetch_registros_para_recurso`, las dos copias de `orm_models.py` con
`ddl_complementario()`, el guardián `tests/test_f010_orm_models_gemelos.py`,
los tres llamantes de sv4 (`trabajador_detail`, `obra_detail`,
`/api/sigrid/empleados`), el `CalendarioProvider` y los dos `settings.py`.

## 2. Decisiones que he tenido que tomar yo (detalle en `design.md` §12)

1. **DA1** · conservar la numeración R10–R28 de F-012 en vez de renumerar.
2. **DA2** · añadir `detalle_jornada_dia(...) -> DetalleJornada` **junto a**
   `jornada_dia(...) -> float` (la firma que fijó F-012 §6.2, que se mantiene
   intacta): sin el detalle, el KPI (R25) y el log (R28) tendrían que
   recalcular `S` y el origen por su cuenta, que es la duplicación de reglas
   que F-003 vino a eliminar.
3. **DA3** · **D7 se implementa contando, no ignorando** (ver duda 3).
4. **DA4** · sábado con `calendario=None` (D11) sigue recibiendo jornada
   `candef`, como hoy, para no romper la regresión cero.
5. **DA5** · el WARNING de «candef fuera del mapa» lo emite el llamante, no
   el resolutor, que se queda puro y sin logging.
6. **DA6** · el guardián R19 vive en `tests/` (raíz) y compara comportamiento
   y API pública, no bytes (los dos resolutores tienen docstrings distintos
   a propósito desde F-003).
7. **DA7** · puerto + adaptador en sv3 y proveedor en sv4, como proponía
   F-012 §7; el puerto se llama `jornada_empleado_port.py` por coherencia con
   `calendario_laboral_port.py`.
8. **DA8** · la tabla de excepciones se lee **entera** (se espera vacía) y se
   indexa en memoria; nada de un `SELECT` por DNI y día.

## 3. Hallazgo que el humano debe conocer (design §11.2)

El riesgo §10.6 de F-012 («F-014 antes que F-015») es correcto, pero al
bajarlo a diseño se ve que **la ventana peligrosa es la inversa** de la
intuitiva:

| Situación | Efecto sobre los 7 recursos de la cuadrilla |
|---|---|
| Hoy | +2 h/semana de extra automática |
| **F-015 sin F-014** | exactamente igual que hoy (**regresión cero**) |
| **F-014 sin F-015** | **−3 h/semana** de extra negativa: peor que hoy |
| F-014 + F-015 | 0 extras (lo que registran los humanos) |

La puerta de R35 se mantiene tal como la decidió el humano (no mergear F-015
sin F-014 verificada), pero conviene **coordinar el cambio en Sigrid con el
despliegue de sv3+sv4**, porque el daño está en la espera intermedia. Los
partes no congelados se autocorrigen en la primera pasada de sv3 tras el
despliegue; los congelados no, y eso es lo correcto (ya están en Sigrid).

## 4. Dudas que necesitan validación del humano

1. **`jornada_resolver.py` no figura en la lista cerrada de duplicación
   tolerada de `CLAUDE.md`** aunque lleva duplicado desde F-003 y F-015 lo
   amplía. ¿Se añade a esa lista con fecha y motivo? **No he tocado
   `CLAUDE.md`**: es documento del humano.
2. **Ventana F-014 → F-015** (punto 3 de este informe): ¿se coordina el
   cambio de RRHH con el despliegue, o se acepta la ventana?
3. **DA3 · implementación de D7.** F-012 dice «excluir del re-split lo
   registrado/encolado/approved». Excluirlas también del **total del día**
   rompe los días mixtos (una obra ya registrada y otra pendiente: el
   trabajador recibiría una segunda jornada completa). He diseñado que las
   líneas congeladas **cuenten en el total pero no se modifiquen nunca**, y
   que si el día no cuadra sin tocarlas no se genere split y se avise. Si el
   humano prefiere la lectura literal, hay que decirlo **antes de T6**.
4. **`hasta` es exclusivo** (`desde ≤ d < hasta`), como escribió F-012 §6.1.
   Importa para F-016: «hasta el 31/07» se carga como `hasta = 2026-08-01`.
5. **Validaciones de `empleado_jornada`** (horas 0–24, sin solapes, al menos
   `S` o patrón) son de **F-016**. Hasta entonces las filas se cargan por SQL
   manual y el resolutor solo se defiende ignorando la fila mal formada con
   WARNING. ¿Suficiente, sabiendo que se espera que la tabla siga vacía?

## 5. Estado y siguiente paso

- La spec está **pendiente de aprobación del humano** (PARADA 1). El
  spec-author **no** edita `harness/features.json`: mover F-015 a
  `spec_ready` / `in_progress` es del líder.
- Ninguna decisión firme de F-012 (D1–D11) se ha reabierto ni contradicho.
- Ningún dato personal en la spec: sin DNIs, sin nombres y sin códigos de
  recurso (`grep -nE "[0-9]{8}[A-Z]"` y `grep -nEi "MO/[0-9]{4}"` sin
  resultados sobre los tres ficheros).
