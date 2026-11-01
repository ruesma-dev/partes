<!-- specs/F-061-parte-vacio-tras-borrar-lineas/requirements.md -->
# F-061 · Un parte que se queda sin líneas no puede seguir activo — Requisitos

**Servicio tocado: solo sv4** (`services/partes-front`: borrado, restauración, papelera,
listado y un script de consola). sv3 no se toca (DA6, `design.md` §10). **Sigrid no se
toca.** Sin cambios de esquema (`orm_models.py` intactos). Rigor **estándar** (DA8).

**Petición del humano**: 2026-10-25, «añade una feature para ver por que no los borro
bien»; 2026-10-26, «si, spec de la siguiente».

**Decisión del humano (2026-10-26)**, literal: «f61 al borrar todas la slineas de un parte se
deb borrar el parte. el parte como entidad no hace falta que vaya a paperlera porque es
confuso. habra una logica que borre el parte en si, al quedarse sin lineas». A las dos
preguntas del líder eligió «Oculto y luego borrado» y, para los existentes, «Lo mismo que la
regla» (DA1–DA4 decididas, `design.md` §10).

**Causa** (`design.md` §2): borrar una línea suelta (`soft_delete_registro`) nunca mira si
el parte se queda sin líneas vivas, y vaciar la papelera borra físicamente las líneas
sueltas sin mirar su parte. El parte queda `is_active`, sin líneas, y sv3
(`get_by_sha256` filtra `is_active`) descarta la reingesta del mismo PDF.

## Glosario

- **Línea viva**: `parte_registros.deleted_at_utc IS NULL`.
- **Parte vacío**: `parte_documents.is_active` y **ninguna línea viva** (sin filas, o con
  todas en la papelera).
- **Parte retirado**: `is_active = false`, `deleted_at_utc IS NULL` y `deleted_by` con la
  marca `sin-lineas` (`design.md` §4.1, DA7). No sale en `/partes` ni en la papelera de
  partes, y su sha256 queda libre (índice único parcial `WHERE is_active`).
- **Estados que viven fuera**: `registrado`, `dedicacion` (`vive_fuera`) y `encolado`.

## Requisitos

### Retirar el parte que se queda sin líneas (DA1)

- **R1.** CUANDO `POST /api/registro/{id}/delete` manda a la papelera la última línea viva de
  un parte, sv4 debe retirar ese parte **en la misma transacción** y responder
  `{"ok": true, "parte_retirado": true, "document_id": "<id>"}`. Si quedan líneas vivas,
  `parte_retirado` debe ser `false` y el parte no se toca.
- **R2.** El borrado por persona (`POST /api/trabajador/{key}/delete`) y el deshacer de una
  edición de celda (`_deshacer_creadas`, F-049) deben aplicar la misma regla con la misma
  función. Las líneas congeladas que se omiten (F-004 R13) siguen vivas, así que su parte no
  se retira.
- **R3.** Antes de mirar si un parte se queda vacío y antes de cambiar sus líneas, sv4 debe
  bloquear su fila de `parte_documents` (`SELECT … FOR UPDATE`; si son varias, por `id`
  ascendente). Así, dos borrados simultáneos de las dos últimas líneas (el borrado en bloque
  lanza N peticiones a la vez) no dejan el parte activo y vacío.
- **R4.** El borrado de obra y el de parte («Borrar parte») no cambian: son acciones
  explícitas sobre el parte y lo siguen mandando a la papelera de partes.

### La papelera de líneas y restaurar (DA2)

- **R5.** Las líneas de un parte retirado deben seguir saliendo en «Líneas sueltas borradas»
  de `/papelera`, con «Restaurar» y «Eliminar».
- **R6.** CUANDO se restaura una línea de un parte retirado, sv4 debe devolver el parte a
  activo y quitarle la marca.
- **R7.** SI al restaurar una línea de un parte retirado o un parte de la papelera ya existe
  **otro** parte activo con el mismo `source_sha256` (se reprocesó), ENTONCES sv4 debe
  responder 409 `{"ok": false, "error": "<motivo>"}` sin escribir nada, y el portal debe
  enseñar el motivo.
- **R8.** CUANDO se restaura un parte de la papelera de partes sin ninguna línea viva, sv4
  debe restaurar también sus líneas de la papelera. Si tiene alguna viva, solo el parte, como
  hoy.

### Borrado físico del parte sin filas (DA3, decidido por el humano)

- **R9.** CUANDO se vacía la papelera, sv4 debe hacer lo de hoy y después **borrar
  físicamente** todo parte retirado que no conserve ninguna fila. Su número va en
  `partes_borrados`. Un parte retirado que conserve filas sigue retirado: son las que se
  omiten por vivir fuera, F-004 R12 y F-019 R16.
- **R10.** CUANDO «Eliminar» borra una línea suelta (`hard_delete_registro`) y su parte
  retirado se queda sin filas, sv4 debe borrar también el parte.
- **R11.** Ningún parte con filas debe borrarse físicamente por esta feature, y ningún parte
  que no esté retirado. Los partes de la papelera de partes siguen como hoy.

### Portal (DA5)

- **R12.** CUANDO se borra la última línea desde el detalle de su parte, el portal debe
  avisar: «El parte se ha quedado sin líneas y se ha retirado; sus líneas siguen en la
  papelera.». Después debe llevar a `/partes`, en vez de recargar una página que daría 404.
  Aplica al borrado una a una y al borrado en bloque.
- **R13.** El listado `/partes` debe contar empleados y horas solo con las líneas vivas. Al
  parte activo sin ninguna línea viva debe marcarlo con la insignia «Sin líneas».

### Los existentes (DA4, decidido por el humano: «Lo mismo que la regla»)

- **R14.** Sin argumentos, el script `services/partes-front/limpiar_partes_vacios.py` debe
  **solo leer**, en una transacción `READ ONLY` en PostgreSQL. Debe escribir en
  `services/partes-front/logs/` un Markdown y un CSV (UTF-8 BOM, `;`), sin nombres ni DNIs.
  Por cada parte vacío, deben llevar `document_id`, fecha, `obra_codigo`, `created_at_utc`,
  categoría, acción prevista (`borrar` si no tiene filas, `retirar` si las tiene) y el motivo
  de exclusión, si lo hay.
- **R15.** Las categorías deben ser:
  - `todas_en_papelera`: tiene filas y ninguna viva;
  - `sin_filas_leidos`: sin filas, y la extracción guardada traía empleados;
  - `sin_filas_nada_leido`;
  - `sin_filas_manual`: `source_mime_type = 'manual'`.
- **R16.** Debe excluir, y listar con su motivo:
  - el parte aprobado;
  - el que tenga alguna línea, viva o en la papelera, en un estado que vive fuera;
  - el que tenga alguna línea de los partes de Sigrid protegidos `PT26/00373`, `PT26/00375`
    y `PT26/00376` (lista cerrada).
- **R17.** El script con `--ejecutar --esperados N`:
  - Si los candidatos no excluidos no son exactamente N, debe abortar sin escribir (código 2).
  - Si lo son, en una transacción, recomprobando cada uno bajo bloqueo, debe aplicar la
    regla: borrar físicamente el parte sin filas y retirar el que tenga filas, con la marca
    `sin-lineas · F-061-limpieza`.
  - `--ejecutar` sin `--esperados` debe ser un error de uso.
- **R18.** El script no debe usar `SessionFactory`, que toca el servidor, ni llevar secretos.
  Lee `DATABASE_URL` de la configuración de sv4.

### Generales

- **R19.** La feature no debe tocar sv1, sv2, sv3 ni sv5, ni Sigrid, ni `orm_models.py`, ni
  la regla de congelación ni los demás ficheros de la lista cerrada de duplicación.
- **R20.** `docs/ARCHITECTURE.md` y `azure-apps/partes.md` deben describir la regla nueva:
  - en ARCHITECTURE, la semántica 8 y «Herramientas de consola»;
  - en `partes.md`, la fila de `source_sha256` y la de papelera.

## Fuera de alcance

- Reprocesar los partes limpiados: lo pide el humano reenviando o reencolando, como hoy.
- Que borrar una línea pida a sv3 recalcular el reparto del día (F-042).
- Un parte que **nace** vacío (la IA no leyó a nadie) sigue bloqueando su sha256 hasta que
  se borre con «Borrar parte» (DA6).
