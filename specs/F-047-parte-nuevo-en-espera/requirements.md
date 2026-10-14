<!-- specs/F-047-parte-nuevo-en-espera/requirements.md -->
# F-047 · Parte nuevo «en espera» hasta que sv3 lo reparta — Requisitos

**sv3** (marca el pedido al guardar un parte nuevo y el terminado tras
conciliar) y **sv4** (motivo de la espera, textos, listado y aprobación).
**Sin columnas nuevas**: reutiliza el seguimiento de F-043. Rigor **crítico**
(design §1). Decisiones abiertas: design §11 (DA1–DA10).

## Contexto (verificado en el código el 2026-10-14)

- `PersistPartePipeline.run` (sv3) guarda el documento y sus líneas con las
  horas leídas (`save_parte`, commit y log `[parte-repo] guardado`) y
  **después** lanza `conciliar_todos` de partidas y de recurso, que reparte
  ordinaria y extra. Medido el 2026-10-14: de 22 a 39 s entre una cosa y otra.
  En ese hueco el portal enseña 10, 5 o 9 h en vez de 8+2, 8−3 u 8+1.
- Las dos conciliaciones de la ingesta son *best-effort*: si lanzan, se
  registra un WARNING y el mensaje se consume. Un sha256 repetido sale antes
  de guardar y no concilia.
- La maquinaria de F-043 (guarda 409, vistas pintadas por el servidor, sondeo,
  «Actualizar») depende solo del **estado** `pendiente`, no de quién escribió
  el pedido.
- sv3 no reparte lo congelado (`esta_congelado`: parte aprobado o línea
  encolada o registrada). Si se aprueba un parte en espera, **su reparto no
  llega nunca**.

## Glosario

- **Estado del seguimiento**: el de F-043 (`sin_seguimiento`, `pendiente`,
  `terminado`, `vencido`; `ESPERA_MAX_S` = 600 s). **En espera** = `pendiente`.
- **Motivo de la espera**: `nuevo` si `recalculo_pedido_id` es igual al `id`
  del documento (lo escribió sv3 al guardarlo, DA1); `recalculo` en cualquier
  otro caso (lo escribió sv4 al pedir el recálculo de F-042/F-043).

## sv3 · marca del parte nuevo

- **R1.** CUANDO el pipeline guarda un parte nuevo con el conciliador de
  recurso y el seguimiento cableados, `save_parte` debe escribir
  `recalculo_pedido_id` = `document_id` y `recalculo_pedido_at_utc` = la hora
  UTC ISO del guardado **en el mismo commit** que el documento y sus líneas,
  con `recalculo_terminado_id` y su `_at_utc` a NULL.
- **R2.** SI falta el conciliador de recurso o el seguimiento, ENTONCES el
  parte se guarda sin pedido (las cuatro columnas a NULL), como hoy.
- **R3.** SI el sha256 ya existe, ENTONCES no se guarda, ni se marca, ni se
  concilia nada (sin cambios).
- **R4.** CUANDO, tras guardar con pedido, la conciliación de recurso acaba
  sin excepción, el pipeline debe llamar a `marcar_terminado(document_id,
  document_id)` **después** de las dos conciliaciones, haya fallado o no la
  de partidas (DA2).
- **R5.** SI la conciliación de recurso lanza, ENTONCES no se marca, queda el
  WARNING de hoy, no se propaga y el resultado del pipeline no cambia (DA2).
- **R6.** CUANDO marca, INFO `[persist-parte] parte nuevo repartido
  document_id=%s marcado=%s`. SI marcar lanza, ENTONCES WARNING
  `[persist-parte]` con `document_id` y el tipo de error, sin propagar.
- **R7.** SI sv4 escribe otro pedido durante la conciliación (cambio de fecha
  o deshacer), ENTONCES la marca del pipeline no lo toca (UPDATE condicional
  de F-043) y el documento sigue `pendiente`.
- **R8.** En un reemplazo (`_deactivate_same_day_obra`), solo el documento
  nuevo lleva el pedido; los desactivados no cambian sus columnas de
  seguimiento.
- **R9.** El puerto `ParteRepository.save_parte` gana el parámetro opcional
  `recalculo_pedido_id: str | None = None`; sin él, el comportamiento es
  idéntico al actual.
- **R10.** `build_app` debe pasar al pipeline el **mismo** adaptador de
  seguimiento que expone en `app.state.recalculo_seguimiento`.
  `PersistParteResult`, `despacho.py` y `main_worker.py` no cambian.

## sv4 · motivo y vistas (servidor)

- **R11.** `motivo_espera(document_id, pedido_id)` debe devolver `nuevo` si
  `pedido_id` no está vacío y es igual a `document_id`, y `recalculo` en
  cualquier otro caso.
- **R12.** `motivos_espera(ids)` debe devolver `{id: motivo}` solo de los
  documentos activos `pendiente`, en una consulta; con `ids` = None, los de
  toda la base (consulta filtrada a pedido no nulo y distinto del terminado).
- **R13.** Las vistas de obra, de trabajador y de detalle deben seguir
  llamando una vez a `documentos_en_espera` (F-043 R37). Para los documentos
  con motivo `nuevo` deben añadir `data-recalculo-motivo="nuevo"` y la marca
  `<span class="recalculando-marca">procesando…</span>`; los demás se pintan
  exactamente como en F-043.
- **R14.** En `/partes`, cada fila debe llevar `data-document-id` y
  `data-fecha`; la de un parte en espera, además, `data-recalculando="1"`,
  `data-recalculo-motivo="nuevo"` si toca y la marca de R13 (o la de F-043)
  en la celda de estado.
- **R15.** Las ediciones de un parte nuevo en espera deben dar el 409 de F-043
  R38, con el mismo texto; cambiar la fecha y deshacer siguen permitidos.

## sv4 · aprobación (DA3)

- **R16.** SI se envía `POST /documents/{id}/approve` sobre un parte en espera
  (de cualquier motivo), ENTONCES no se aprueba y se redirige a `back` con el
  motivo de F-043 R38.
- **R17.** `lineas_para_registro` debe dejar fuera las líneas de los
  documentos en espera y contarlas en `excluidas["recalculando"]` (la clave
  solo existe si es > 0), con su detalle y el motivo «parte en espera: se
  están repartiendo sus horas; pulsa Actualizar cuando termine».
  `_motivo_sin_lineas` debe nombrarlas. Las claves que ya existen no cambian.
- **R18.** En el detalle del parte, la barra de acciones debe llevar
  `data-parte-acciones` y `data-document-id`. Mientras dure la espera, «Aprobar
  parte», «Marcar pendiente» y «Borrar» quedan deshabilitados. Los
  contenedores `[data-parte-contenido]` siguen siendo dos (DA10).

## sv4 · portal (`static/app.js`)

- **R19.** CUANDO la página carga con un contenedor en espera que lleva
  `data-recalculo-motivo="nuevo"`, el portal debe poner el parte en espera
  con la marca «procesando…» y el aviso: «Procesando el parte nuevo del D: se
  están repartiendo sus horas normales y extra (suele tardar menos de 1 min).
  Puedes seguir trabajando con el resto.» (DA6).
- **R20.** CUANDO un parte nuevo pasa a `terminado`, la marca debe decir
  «procesado · pulsa Actualizar» y el aviso «Parte nuevo del D procesado:
  horas repartidas.», con «Actualizar».
- **R21.** CUANDO un parte nuevo da `vencido`, el aviso debe decir «No se ha
  podido confirmar el reparto de horas del parte nuevo del D. Pulsa
  Actualizar; si siguen sin repartir, avisa a quien mantiene el portal.»
  (marca de F-043).
- **R22.** Sin `data-recalculo-motivo`, y siempre que sea `wireFechaInput` quien
  pone el parte en espera tras un `pedido`, las marcas y avisos deben ser los
  de F-043, idénticos.
- **R23.** Siguen igual el sondeo, «Actualizar», la restauración de la vista
  y la regla de no recargar nunca sin un clic (F-043 R18–R26, R40).

## Esquema, contrato y documentación

- **R24.** `orm_models.py` (las dos copias, byte-idénticas) **sin columnas
  nuevas**: el comentario del bloque de seguimiento dice que el pedido también
  lo escribe sv3 al guardar un parte nuevo, con el id del documento (DA4).
- **R25.** Un test de la raíz debe comprobar por AST:
  - que el repositorio de sv3 escribe `recalculo_pedido_id` y
    `recalculo_pedido_at_utc` y no las columnas de terminado;
  - que el pipeline pasa `recalculo_pedido_id=document_id`;
  - que `motivo_espera` de sv4 compara con el id del documento.
- **R26.** Deben contar el pedido de la ingesta, el motivo, el listado y la
  exclusión de la aprobación:
  - `docs/ARCHITECTURE.md` (semánticas 3, 7 y 10);
  - `docs/referencia/partes-proyecto.md` (§5 y «El parte en espera»);
  - `azure-apps/partes.md`.
- **R27.** No se modifica ningún test existente (DA8).

## Fuera de alcance

- Cambiar el algoritmo de reparto (F-045) o acelerar sv3.
- Recargar la página o refrescar filas sin un clic.
- Las vistas agregadas (`/obras`, `/trabajadores`) y `/conciliacion` (DA7).
- Los partes creados a mano en sv4 (`/api/partes/nuevo`), que no pasan por sv3.
- Volver a conciliar un parte cuya entrega se repite tras una caída entre el
  guardado y la marca (DA9).
