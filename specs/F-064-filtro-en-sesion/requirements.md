<!-- specs/F-064-filtro-en-sesion/requirements.md -->
# F-064 · El filtro del portal se mantiene durante la sesión de cada usuario — Requisitos

**Servicio tocado: solo sv4** (`services/partes-front`; ficheros en `design.md` §3). Rigor
**estándar**: cambia el comportamiento del navegador. No escribe en `partes` ni en Sigrid, no
añade endpoints, esquema ni colas, y no toca nada compartido.

**Petición del humano del 2026-10-26**, literal: «la siguiente feature es que el filtro se
mantenga dentro de la sesion por susuaio».

**Contexto** (`design.md` §2): hoy cada filtro vive solo en la página. Al navegar o recargar se
pierde. La única excepción es «Actualizar» de **F-043** (R21, DA10; no de F-022): guarda los
filtros por posición en `sessionStorage` (`VISTA_CLAVE`) durante 60 s y los repone una vez.

**Decisiones**: los requisitos suponen la opción **recomendada** de cada DA de `design.md` §9
(DA1–DA7 = A). El humano las confirma antes de T1.

## Glosario

- **Usuario**: el actor de F-017, que es el principal de Easy Auth normalizado
  (`_resolver_identidad`).
- **Clave de usuario**: los 16 primeros caracteres hexadecimales del SHA-256 (UTF-8) del actor.
  El servidor la pinta en `<body data-filtros-usuario>` y el navegador nunca ve el actor en claro
  por esta vía.
- **Sesión**: la actividad de un usuario en un navegador. Caduca a las **8 h** sin cargar
  ninguna página del portal (`SESION_MS`; DA2, M0).
- **Pantalla**: la ruta (`location.pathname` sin barra final). `/obras/obr-10` y `/obras/obr-11`
  son pantallas distintas (DA3).
- **Filtros de la pantalla**: los filtros por columna (`.col-filter` de cada tabla con
  `tr.filter-row`), la selección de días (casillas del calendario del trabajador o de la matriz
  de obra), la casilla «Ocultar trabajadores sin código de hora extra» y, en `/partes`,
  `/obras` y `/trabajadores`, la búsqueda del servidor (`search`, `pendientes`) (DA1).
- **Foto**: los filtros de una pantalla tal como se guardan (`design.md` §5).

## Requisitos

### Quién es el usuario (servidor)

- **R1.** Toda página HTML de sv4 debe pintar `<body data-filtros-usuario="…">` con la clave de
  usuario del actor que resuelve `_resolver_identidad`. Usuarios distintos tienen claves
  distintas y el mismo usuario tiene siempre la misma.
- **R2.** SI el origen de la identidad es `sin-identidad-desplegado`, ENTONCES el atributo debe ir
  vacío, porque todos los usuarios compartirían clave. En local, la clave sale de `local:…` como
  cualquier otro actor.
- **R3.** La clave debe calcularla una función pura de `identidad.py` (`clave_filtros(actor,
  origen)`). `app.py` no lee cabeceras de Easy Auth por su cuenta y los guardianes de F-017
  (`test_f017_punto_unico.py`) siguen en verde sin tocarlos. El actor en claro no aparece en el
  HTML por causa de esta feature.

### Dónde y cuánto se guarda (navegador)

- **R4.** Los filtros deben guardarse en `localStorage`, bajo `partes.filtros.v1:<clave de
  usuario>`, con la forma de `design.md` §5: versión, `t` y una entrada por pantalla.
- **R5.** SI el atributo está vacío, o `localStorage` no existe o lanza, ENTONCES el portal debe
  funcionar exactamente como hoy, sin guardar ni restaurar nada y sin errores en consola.
- **R6.** CUANDO se lee el estado y es JSON inválido, de otra versión o con `t` de hace 8 h o
  más (o en el futuro), el sistema debe tratarlo como vacío y borrar esa clave.
- **R7.** CUANDO se carga una página con clave de usuario, el sistema debe actualizar `t` (la
  actividad renueva la sesión) y conservar como mucho las **50** pantallas más recientes.
- **R8.** CUANDO se carga una página, el sistema debe borrar las claves `partes.filtros.v1:*` de
  **cualquier** usuario que estén caducadas según R6.
- **R9.** Un estado guardado con la clave de un usuario no debe leerse nunca con la de otro.

### Qué se guarda

- **R10.** CUANDO cambia un filtro por columna (al escribir o con «Limpiar»), la selección de
  días (con un clic o con «Quitar filtro») o la casilla de la matriz, el sistema debe guardar la
  foto de la pantalla. Para una foto vacía (R14), debe borrar su entrada.
- **R11.** Cada filtro por columna debe identificarse por **(tabla, columna)**, nunca por su
  posición en la página:
  - tabla: su `id`; si no lo tiene, `matriz` para la `table.matrix` y `tabla` para las demás;
  - columna: el `data-col-key` de la cabecera, o su texto, en la misma posición de la primera
    fila de `thead`.

  Solo se guardan los valores no vacíos. Mover columnas (`wireColumnTools`) no rompe la
  restauración.
- **R12.** La selección de días debe guardarse con las claves de las casillas marcadas y con su
  **periodo**, que se forma con el valor de `#period`, `|` y el `modo` del formulario
  `.cal-period`. Si no hay formulario, el periodo es una cadena vacía.
- **R13.** La casilla «Ocultar trabajadores sin código de hora extra» debe guardarse solo cuando
  está desmarcada, porque su valor por defecto es marcada.
- **R14.** Una foto es **vacía** si no tiene filtros por columna, ni días, ni casilla desmarcada
  ni búsqueda.

### Restaurar

- **R15.** CUANDO se carga una pantalla con una entrada vigente, el sistema debe reponer sus
  filtros:
  - filtros por columna: el valor de cada `.col-filter`, disparando `input`;
  - días: solo si coincide el periodo, y solo las casillas que existan en la página;
  - casilla de la matriz.

  Debe hacerlo **antes** de `restaurarVista` de F-043 y sin escrituras intermedias: una sola
  escritura al final.
- **R16.** SI una tabla, una columna o un día guardados no existen en la página, ENTONCES el
  sistema debe ignorarlos sin error. Si no queda ningún día, no se aplica el filtro de días.
- **R17.** CUANDO se repone al menos un filtro por columna o un día, el sistema debe mostrar el
  aviso «Filtros recuperados de tu sesión» con el botón **«Quitar filtros»**. Ese botón:
  - vacía todos los filtros por columna y la selección de días;
  - vuelve a marcar la casilla de la matriz;
  - borra la entrada de la pantalla y oculta el aviso.
- **R18.** Tras restaurar, el contador de selección y el botón de aprobar de F-022 deben reflejar
  ya los filtros repuestos: cada reposición pasa por el `apply` de siempre y avisa con
  `lineas:cambio`.

### Búsqueda del servidor (`/partes`, `/obras`, `/trabajadores`)

- **R19.** CUANDO se carga una de esas tres listas:
  - con una consulta que solo lleva `search` o `pendientes`, el sistema debe guardarla
    normalizada; si todos sus valores están vacíos, se guarda como vacía;
  - **sin** consulta y con una búsqueda guardada no vacía, debe hacer `location.replace(ruta +
    "?" + búsqueda)` antes de cablear nada;
  - con cualquier otro parámetro, como `message`, ni guarda ni redirige.
- **R20.** El enlace «Limpiar» de las tres listas debe apuntar a `?search=` y no a la ruta sin
  consulta. Así limpiar no vuelve a traer la búsqueda guardada.

### Selección y aprobación (F-022)

- **R21.** La selección de líneas (`PartidaSel`, casillas `.sel-linea`, Ctrl/Shift+clic) **no** se
  debe guardar ni restaurar: al cargar cualquier página no hay ninguna línea seleccionada.
- **R22.** No deben cambiar `conjuntoAprobacion`, `PartidaSel.visible` ni la validación del
  `ambito` en el servidor. Con un filtro repuesto, el botón aprueba solo lo visible (F-022 R6) y
  una línea oculta nunca se envía.

### Lo que no cambia

- **R23.** No deben cambiar: `restaurarVista`, `actualizarVista`, `vistaRestaurable` ni
  `VISTA_CLAVE` (F-043); `_ctKey` ni anchos y orden de columnas; los combos de edición
  (`wireObraCombo`, `wireEmpleadoCombo`) ni `capFilter`; `period` y `modo` de los detalles.
- **R24.** Solo debe cambiar sv4, más `docs/ARCHITECTURE.md`, comprobable con `git diff --stat
  dev`. No cambian sv1, sv2, sv3, sv5, `infra/`, los `orm_models.py`, los endpoints JSON ni
  `azure-apps/partes.md`, porque no cambia lo que se expone ni lo que se consume.
- **R25.** `docs/ARCHITECTURE.md` (punto 11, identidad del portal) debe contar la clave de
  filtros, el guardado por usuario y pantalla en el navegador, la caducidad de 8 h y que la
  selección nunca se guarda.

## Verificación manual (`design.md` §8)

- **M0** (líder, solo lectura, antes de T1): la caducidad de la cookie de Easy Auth de
  `ca-sv4-front`, que fija `SESION_MS` (DA2).
- **M1** (humano o líder, portal local): lista → detalle → volver, recarga, pestaña nueva,
  «Quitar filtros», «Limpiar», periodo distinto y aprobar con un filtro repuesto. Solo se mira;
  no se aprueba nada fuera de la obra de pruebas.
- **M2** (humano, tras desplegar sv4): dos usuarios de Entra en el mismo navegador
  (`/.auth/logout` entre uno y otro) no ven los filtros del otro.

**Fuera de alcance**: guardar en el servidor o entre ordenadores (DA2-C); el mes o el modo de
los detalles (DA1-C); la ordenación y la selección de líneas; sincronizar pestañas en vivo;
anchos de columna por usuario (`ct:*`); un «olvidar mis filtros» global (DA4-B).
