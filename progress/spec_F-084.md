<!-- progress/spec_F-084.md -->
# F-084 · Spec para el humano (spec-author, 2026-11-26)

Spec: `specs/F-084-partes-con-problemas/` (requirements 144/150, design 249/250, tasks T1–T12).
Rama `feature/F-084-partes-con-problemas`, en la copia `partes-wt-f084` (sale de `dev` 0b2ff00).
F-084 pasa a `spec_ready`, con rigor `critico` **propuesto** (D9).

## Qué propone

1. **sv3 deja rastro al sustituir** (D1, D2). Cuando el reemplazo desactiva un parte, escribe
   `sustituido_por_id` y `sustituido_at_utc`, dos columnas nuevas nullables en
   `parte_documents`. Si los dos partes son del mismo correo, lo avisa con un WARNING. **Qué
   se sustituye no cambia**, ni siquiera entre páginas del mismo envío: dejar los dos activos
   duplicaría las horas del día y sv3 calcularía extras que no existen.
2. **Pestaña nueva «Problemas»** en sv4 (`/problemas`), entre Conciliar y Partes, con contador
   en la navegación. Motivos:
   - de los partes **activos**: `sin_obra`, `sin_fecha`, `fecha_futura`,
     `fecha_posterior_al_correo` y `sin_lineas`;
   - de los **desactivados en silencio**: `sustituido_mismo_envio` (el caso 0692),
     `sustituido` (un reenvío normal: se lista, pero no cuenta en el aviso) y
     `desactivado_sin_rastro`.
   - Fuera quedan la papelera y los retirados de F-061.
3. **Acciones**, reutilizando lo que hay:
   - en un activo, el detalle `/partes/{id}`, donde ya se corrigen la obra y la fecha;
   - en cualquier parte con PDF, «Ver PDF» con el visor de siempre (ya sirve los inactivos);
   - en un sustituido, «Descartar» por el `delete_document` de siempre, o «Recuperar», que es
     la única acción nueva (`POST /api/partes/{id}/recuperar`). Recuperar admite corregir la
     fecha en el mismo paso, entra en Deshacer con el actor y pide el recálculo a sv3.
   - Si al recuperar choca con otro parte activo del mismo día, obra y trabajador, da 409 y lo
     nombra: el usuario corrige la fecha o descarta antes el otro.
4. **Retroactivo** (D4): lo desactivado antes de F-084 sale con una pista (mismo día y obra,
   creado después; gana el del mismo correo).

## Respuestas a lo que pedía investigar

- **Qué pone `is_active = false` sin `deleted_at_utc`**: solo dos sitios. El reemplazo de sv3
  (`deleted_by` NULL) y el retirado de F-061 en sv4 (`deleted_by` = `sin-lineas[ · actor]`).
  Los 21 «sin sustituto posterior» serán retirados (fuera de la pestaña) o partes cuyo
  sustituto cambió luego de fecha u obra o se borró: salen como `desactivado_sin_rastro`.
- **Páginas que fallan en sv2 o sv3**: agotados los reintentos, van a `q-extraccion-poison` o
  `q-persistencia-poison` y **no dejan nada en la base**. El aviso de poison de F-002 solo
  mira las colas de sv5. Propongo una feature aparte (D7).
- **Mismo envío**: se reconoce por `email_id`, que ya está en `parte_documents`, junto con
  `page_number`/`page_count` y `source_attachment_sha256`.

## Decisiones (recomendación en negrita; tabla completa en design §13)

| D | Pregunta | Recomendado |
|---|---|---|
| D1 | Rastro del reemplazo | **(a) dos columnas nuevas** que escribe sv3. (b) Marca en `deleted_by`, sin DDL. (c) Nada en sv3: sv4 lo deduce siempre |
| D2 | Páginas del mismo envío | **(a) se sigue sustituyendo y se avisa**. (b) No sustituir: los dos activos. (c) Desactivar el nuevo |
| D3 | Qué cuenta en el contador | **(a) todo menos los reenvíos normales** (`sustituido`) |
| D4 | Retroactivo | **(a) sí**, con la pista de R8 |
| D5 | «Fecha dudosa» | **(a) sin fecha + futura + posterior al correo** (con un día de margen) |
| D6 | Recuperar con choque | **(a) 409**: corregir la fecha o descartar antes el otro |
| D7 | Poison de extracción y persistencia | **(a) feature aparte** |
| D8 | Recuperar en Deshacer | **(a) sí**, acción `parte_recuperar` con actor |
| D9 | Rigor | **(a) `critico`** (disparador 2: worker de sv3 y DDL en la base del servidor compartido). `estandar` solo si D1 = (c) |
| D10 | Sustituir un parte aprobado o en Sigrid | **(a) fuera**: insignia en la pestaña y feature aparte si hay casos |

## Preguntas para el líder (datos de la base, solo lectura)

1. De los 112 inactivos sin borrar, ¿cuántos tienen `deleted_by` que empieza por `sin-lineas`
   (retirados de F-061, quedan fuera)? Así se sabe qué hay entre los 21 «sin sustituto».
2. De los sustituidos (`deleted_by` NULL), ¿cuántos están `approved` o tienen alguna línea con
   `sigrid_estado` en `registrado`, `encolado` o `dedicacion`? Decide si D10 necesita una
   feature urgente.
3. Con D3 y D4 como se recomienda, el contador del primer día sería del orden de 11 + los
   «sin rastro» que no sean retirados + 8 activos (1 sin obra, 5 sin fecha, 2 sin líneas).
   El número exacto lo dará M2.

## Riesgos y avisos

- **Dos criterios de «mismo trabajador»**: sv3 compara ide, DNI o nombre; la guarda de
  recuperar usa la clave de trabajador del portal (F-050). Si en algún caso raro discrepan,
  el doble se vería en la matriz (design §10).
- **DDL en producción**: dos `ADD COLUMN` nullables, solo en la base `partes`, que aplica el
  arranque de sv3 y sv4. El despliegue puede hacerse en cualquier orden.
- **Frontera: sí.** Cambian el esquema de `partes`, hay tres rutas nuevas del portal y dos
  motivos nuevos (solo de traza) en el mensaje `recalcular`. Se actualiza
  `azure-apps/partes.md` en un commit aparte (T9), sin push.
- **M3 escribe en producción** (recupera o descarta `5c1a9b04`): necesita el OK expreso del
  humano para esa acción.
