<!-- specs/F-033-columna-empresa/requirements.md -->
# F-033 · Portal: columna Empresa en las vistas de obra — Requisitos

**Servicio tocado: solo sv4** (`services/partes-front/`). Ni schema, ni sv3,
ni sv5, ni `static/app.js`. Rigor **estándar**.

## Contexto (incidencia del humano, 2026-10-07)

En `/obras` la obra 0678 sale «duplicada». En Sigrid hay dos fichas con
código 0678 y el mismo nombre: Ruesma (empresa 1) y Porsan (empresa 28);
103 códigos de Porsan existen también en Ruesma. Desde F-023/F-029 cada
parte se concilia con la obra de la empresa de su membrete, y el listado
agrupa bien por ficha (`obra_key` = `obr-<ide>`), pero solo pinta
«código · nombre»: las dos filas son idénticas. Decisión del humano: «hay
que añadir una columna donde se vea la empresa»; las filas siguen
separadas por ficha.

## Glosario

- **Empresa de la ficha**: `con.emp` de la obra con ese `obra_ide` según el
  catálogo de obras que sv4 ya tiene (`ObraCatalog.get_by_ide`, campo
  `ObraOption.empresa`, F-023).
- **Empresa de un grupo de líneas** (una fila de `/obras` o un detalle de
  obra): la empresa de la ficha si el grupo tiene `obra_ide` y el catálogo
  la conoce; si no, el conjunto de `parte_documents.empresa` no nulos de
  los partes del grupo, sin repetir y en orden numérico; si no, vacío.
- **Empresa de un parte**: la de la ficha de `doc.obra_ide` si se conoce;
  si no, `doc.empresa`; si no, ninguna.
- **Nombre corto**: el que da `config/empresas.yaml` de sv4 (DA1) al número
  (`auxemp.numemp` = `con.emp`): 1 → «Ruesma», 28 → «Porsan».
- **Texto de empresa**: ningún número → «—»; un número → su nombre corto;
  varios → sus nombres unidos por « / » en orden numérico (DA5).

## Requisitos

### Nombre de la empresa (DA1, DA4)

- **R1.** El sistema debe leer al arrancar `config/empresas.yaml` (ruta
  `EMPRESAS_PATH`, relativa a la raíz del servicio) como un mapa
  `numemp → nombre corto`.
- **R2.** SI el fichero no se puede leer o parsear, una clave no es un
  entero o un nombre está vacío, ENTONCES `build_app` debe lanzar
  `ValueError` con la ruta y el motivo (el portal no arranca).
- **R3.** El fichero versionado debe cargar sin error y dar «Ruesma» para
  el 1 y «Porsan» para el 28.
- **R4.** SI un número no está en la tabla, ENTONCES su nombre corto debe
  ser «Empresa N» (N el número).
- **R5.** El texto de empresa debe ser «—» sin números, el nombre corto con
  uno y los nombres unidos por « / » en orden numérico con varios.

### Listado de obras (`/obras`)

- **R6.** El listado debe tener una columna «Empresa» justo después de
  «Obra», con su `<input class="col-filter">` en la fila de filtros: la
  cabecera y la fila de filtros deben tener el mismo número de celdas.
- **R7.** CUANDO dos grupos tienen el mismo código y nombre de obra y
  fichas (`obra_ide`) distintas de empresas distintas, el listado debe
  pintar dos filas, cada una con el texto de empresa de su ficha.
- **R8.** CUANDO el grupo tiene `obra_ide` y el catálogo conoce la ficha, la
  empresa de la fila debe ser la de la ficha aunque sus partes tengan
  `empresa` NULL (partes anteriores a F-023) u otro valor.
- **R9.** SI la ficha no se conoce (grupo sin `obra_ide`, búsqueda en Sigrid
  desactivada, catálogo caído o `ide` ausente del catálogo), ENTONCES la
  empresa de la fila debe salir de `parte_documents.empresa` de sus partes.
- **R10.** SI ninguna fuente da empresa, ENTONCES la celda debe mostrar «—»
  y la fila debe pintarse igual que hoy en todo lo demás.
- **R11.** SI, sin ficha, los partes del grupo tienen varias empresas,
  ENTONCES la celda debe mostrar sus nombres unidos por « / ».
- **R12.** Las filas deben ordenarse por código, nombre y menor número de
  empresa (las de empresa vacía detrás), de modo que las gemelas salgan
  juntas y siempre en el mismo orden.
- **R13.** El `data-label` del botón «Borrar» de cada fila debe acabar en
  « · <texto de empresa>» cuando hay empresa; sin empresa, igual que hoy.
- **R14.** El filtro de la columna «Empresa» debe ocultar las filas cuyo
  texto de empresa no contenga lo tecleado (mecanismo genérico
  `wireColumnFilters`, sin cambios en `app.js`).

### Detalle de obra (`/obras/{obra_key}`)

- **R15.** La cabecera del detalle debe mostrar la empresa del grupo
  («Empresa: Porsan») bajo el título; sin empresa, «Empresa: —».
- **R16.** El `data-label` del botón «Borrar obra» del detalle debe seguir
  la regla de R13.

### Listado y detalle de parte (DA3)

- **R17.** El listado `/partes` debe tener una columna «Empresa» justo
  después de «Obra», con su filtro de columna, y el texto de la empresa del
  parte.
- **R18.** El detalle `/partes/{id}` debe mostrar un dato «Empresa» junto al
  de «Obra» con el texto de la empresa del parte.

### Degradación y no regresión

- **R19.** SI el catálogo de obras falla al refrescar, ENTONCES `/obras`,
  `/obras/{key}`, `/partes` y `/partes/{id}` deben responder 200 con la
  empresa de los partes (R9) o «—».
- **R20.** El sistema no debe cambiar `obra_key`, la agrupación, los
  totales, la búsqueda `search` (código o nombre), ninguna ruta JSON ni el
  schema; la suite de sv4 debe seguir en verde sin tocar tests ajenos.
- **R21.** `docs/ARCHITECTURE.md` (semántica 12) debe decir en una frase
  que sv4 muestra la empresa de la obra con el nombre de
  `config/empresas.yaml`.

## Fuera de alcance

- Vista de trabajador, conciliación y papelera (DA3).
- Los combos de obra (siguen con « · empresa N» de F-023 R41).
- Re-casar la empresa de partes antiguos y hacer que el cambio manual de
  obra actualice `parte_documents.empresa` (DA7).
- Buscar por empresa en el `search` del servidor (el filtro de columna lo
  cubre).

## Trazabilidad

Cada R tiene al menos un test `test_f033_rN_...` (design §7). R21 la
verifica la lectura del reviewer. M1 (design §8) es manual del humano.
