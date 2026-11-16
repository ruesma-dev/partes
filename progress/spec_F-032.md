<!-- progress/spec_F-032.md -->
# F-032 · Resumen de la spec refrescada (2026-11-16)

Rama `feature/F-032-sesame-festivos-produccion`, creada desde `dev` (`95982ac`). No
existía ninguna rama con ese nombre. Spec en `specs/F-032-sesame-festivos-produccion/`:
requirements 148/150, design 250/250 (`python -m harness.tamano --feature F-032` en
verde) y tasks con 19 tareas. Rigor **estándar**. `harness/features.json` no se ha tocado:
el líder marca el estado y rellena «Decidido».

## Decisiones

- **DA1–DA4 y DA6–DA10**: como recomendaba la spec, según lo que el humano decidió el
  2026-11-16. Quedan en la tabla de design §9 con «Decidido» vacío para que el líder la
  rellene al aprobar.
- **DA5 cambiada**: `SESAME_FESTIVOS_MINIMOS` con **defecto 1** en sv3, sv4 y
  `00_vars_partes.ps1` (un calendario con 0 festivos del año se trata como degradado).
  Sigue siendo configurable, y la spec dice que se vuelve a 8 si M2 demuestra que Sesame
  devuelve todas las fiestas. El guardián de la raíz comprueba que los dos servicios
  usan el mismo defecto.
- **Nuevas, a decidir**:
  - **DA11, cuándo corre la pasada de sv3 al encender o apagar.** Recomendado (A): el
    script la pide por `q-persistencia` con `infra/pedir_recalculo_partes.py` (motivo
    `encendido_sesame` o `apagado_sesame`), justo después de la revisión nueva de sv3 y
    antes de tocar sv4.
  - **DA12, qué hacer si M2 muestra que a Sesame le faltan festivos del respaldo
    (nacionales o 28-feb).** Recomendado (A): es una puerta. No se enciende y se vuelve a
    decidir: o RRHH los carga en Sesame, o se unen respaldo y Sesame en una feature aparte.
  - **DA13, la rejilla de obra por persona.** Es la que pidió el humano; se deja en la
    tabla para que quede registrada como revocación de la D6 de F-003.

## Cambios respecto a la versión de octubre

1. **Recálculo de lo ya conciliado (DA7, revisado contra F-042 a F-069).** La pasada
   sigue siendo global: `conciliar_todos` recalcula todo lo libre de los partes activos,
   tanto en cada ingesta como en cada mensaje `recalcular` de sv4, y el `document_id` no
   la acota. Las features posteriores solo cambian quién la pide. Lo que sí es nuevo:
   - **Encender no recalcula nada.** sv3 es un worker KEDA con 0 réplicas mínimas y no
     tiene ingress en Azure. Hasta el siguiente mensaje, la BBDD guarda el reparto
     calculado con el JSON, y aprobar en ese intervalo congela ese reparto. De ahí DA11,
     el R26 y el orden sv3 → pasada → sv4 del R23. El endpoint
     `/admin/reconciliar-recursos` solo existe en local y se descarta.
   - **Las líneas congeladas ya no quedan siempre intactas.** Con `REPARTO_REAJUSTE`
     encendido (desde el 2026-10-18), un día que mezcla líneas reajustables y libres, y
     cuyo reparto ideal cambia, genera una propuesta en `reparto_pendiente` (F-046). No
     se escribe nada en Sigrid hasta que alguien pulse «Aplicar» (R30 y M7).
   - **El impacto se mide por semana.** Un festivo puede cambiar cuál es el último día
     laborable de la semana (F-015). La herramienta clasifica cada línea afectada con
     `clase_linea` y `_congelado`, importados y no copiados, deja fuera la papelera y
     cuenta los días mixtos (R19 y R20).
2. **Requisito nuevo en sv4: festivos por persona en la rejilla de obra (R10–R13).**
   - Cada celda se pinta con el calendario del DNI de su fila. La cabecera solo marca fin
     de semana y fecha futura.
   - El aviso degradado ya no consulta (`None`, año) y su texto pasa a decir «Los
     festivos marcados en la rejilla…».
   - `get_obra` recibe ahora `holiday_name_de` en lugar de `holiday_name`.
   - Un test existente cambia a propósito:
     `test_f003_r2_la_columna_de_la_matriz_usa_el_calendario_por_defecto`, que fijaba la
     D6 que ahora se revoca.
   - He comprobado las demás vistas y ya usan el DNI de la persona: `trabajador_detail`,
     `/api/calendario` de «+ Nuevo» (sin trabajador elegido usa el calendario por
     defecto, que es lo correcto) y los avisos de registro. No se tocan.
3. **Contraste**: la marca nueva `FALTAN DEL RESPALDO` es la puerta de DA12. Con un
   mínimo de 1, un calendario que solo traiga las fiestas locales pasaría el control y
   pagaría el 1 de enero como día ordinario.
4. **Infra**: `add_sesame_partes.ps1` sigue el orden sv3 → espera a la revisión →
   pasada → sv4, y `-Quitar` también pide la pasada. Se añade el script nuevo
   `pedir_recalculo_partes.py` (precedente: `enqueue_test.py`; la clave de la storage
   vive solo en `$env:STKEY`) y un test de contrato con el `clasificar` de sv3.
5. **sesame-api, revisado en solo lectura sin abrir su `.env`.** Está igual que el
   2026-10-06: `dcef288`, el rediseño sin versionar, sin Dockerfile y con el `.env`
   versionado y modificado. Las precondiciones P0–P5 no cambian.
   - **Puerto 8006**: en local lo ocupa porcentajes-transfer, así que para M2 sesame-api
     se arranca con `$env:API_PORT="8016"` (la variable de entorno manda sobre su
     `.env`). En Azure no hay choque.
6. **Numeración nueva**: R1–R34 (antes R1–R29), tareas T1–T19 (antes T1–T17) y
   verificación manual M1–M8 (antes M1–M7).

## Preguntas abiertas para el humano

- DA11, DA12 y DA13 (design §9).
- ¿Hay partes activos de 2025? Si los hay, M2 y M3 se pasan también con `--ano 2025`:
  sin calendario de 2025 en Sesame, esos partes saldrían degradados y marcados para
  revisión en cada pasada.
- Para M5, el humano necesita poder leer las claves de la storage
  (`az storage account keys list`), igual que con `enqueue_test.py`. Si no puede, el
  script avisa y la pasada llega con el siguiente parte.
