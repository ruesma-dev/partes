<!-- specs/F-064-filtro-en-sesion/design.md -->
# F-064 · El filtro del portal se mantiene durante la sesión de cada usuario — diseño técnico

## 1. Encaje y límite de servicio

- **Solo sv4.** Los filtros son del portal (`static/app.js`, plantillas). La identidad la da
  `_resolver_identidad` (F-017), que sigue siendo el único punto: nadie más la lee.
- **Sin servidor de estado.** No hay tablas, endpoints, colas ni variables de entorno nuevas;
  el servidor solo pinta un atributo con la clave de usuario. `azure-apps/partes.md` no se toca:
  no cambia lo que se expone ni lo que se consume.
- **La lista cerrada de duplicados de `CLAUDE.md` no crece**: nada de esto existe en otro servicio.

## 2. Lo que hay hoy (`dev` ec7111d), por pantalla

| Pantalla | Filtros de cliente | Filtros de servidor |
|---|---|---|
| `/partes` | `.col-filter` (8) + «Limpiar» | `search`, `pendientes` |
| `/obras`, `/trabajadores` | `.col-filter` (7 y 8) + «Limpiar» | `search` |
| `/obras/{key}` | matriz: `.col-filter` (2); `#lines-table`: `.col-filter` (8); días `td.mx-pick` (trabajador\|fecha) + «Quitar filtro»; casilla `#hide-sin-extra` (marcada por defecto) | `period`, `modo` |
| `/trabajadores/{key}` | `#lines-table`: `.col-filter` (8); días `.cal-pick[data-fecha]` | `period`, `modo` |
| `/admin/jornadas` | `.col-filter` (8) | — |
| `/partes/{id}`, `/papelera`, `/conciliacion`, `/nuevo` | ninguno | — |

**No son filtros de vista**, y quedan fuera porque son efímeros a propósito: los buscadores de
`wireObraCombo` (≈ l. 698) y `wireEmpleadoCombo` (≈ l. 1224), que editan una línea; `capFilter`
(≈ l. 1633 y 2496), las fichas CD/CI del selector de partida; y `.manual-q` de Conciliar.

**Cómo funciona hoy.** `wireColumnFilters` oculta con `display:none` y llama a
`avisarCambioLineas()` (`lineas:cambio`). `_setupDaySelection` guarda los días en un `Set`
dentro de su cierre y marca `.filtered-day`. La casilla de la matriz la cablea el IIFE «Matriz
de obra» (`ready`, después del `DOMContentLoaded` principal). `PartidaSel` es la selección en
memoria; nunca se ha guardado. `conjuntoAprobacion` (F-022 R6) envía solo las seleccionadas
**visibles** y, sin selección pero con algo oculto, las visibles. `restaurarVista` (F-043 R21)
repone por **posición** los `.col-filter` y el scroll que guardó «Actualizar» (< 60 s). `_ctKey`
guarda anchos y orden de columnas en `localStorage` por ruta y tabla, **sin** usuario. El actor
no llega hoy al HTML; el portal no tiene enlace de salida (Easy Auth da `/.auth/logout`).

## 3. Ficheros (sin prefijo: `services/partes-front/`)

**Modificar**
- `interface_adapters/web/identidad.py`: función pura `clave_filtros` (§4.1).
- `interface_adapters/web/app.py`: global de Jinja `clave_filtros_de(request)`, justo después
  de `_actor` (§4.2).
- `templates/base.html`: `<body data-filtros-usuario="{{ clave_filtros_de(request) }}">`.
- `templates/partes_list.html`, `obras_list.html`, `trabajadores_list.html`: «Limpiar» pasa a
  `href="/partes?search="` (y sus equivalentes) (R20).
- `static/app.js`: el IIFE global `FiltrosSesion` justo después de `avisarCambioLineas` (§4.3);
  `_setupDaySelection` y `wireDayFilters` devuelven un manejador (§4.4); dos líneas en el
  `DOMContentLoaded` principal (§4.5).
- `docs/ARCHITECTURE.md`: punto 11 (R25).

**Crear**: `tests/test_f064_clave_usuario.py` (R1–R3, `TestClient` con el patrón de
`test_f022_vistas_seleccion.py`) y `tests/test_f064_filtros_js.py` (node, con el patrón de
`test_f049_editor_js.py`, y el cableado leído del fuente).

**NO se tocan**: `restaurarVista`, `actualizarVista`, `vistaRestaurable` y `VISTA_CLAVE`
(F-043); `conjuntoAprobacion`, `PartidaSel` y `wireBulkSelect` (F-022); `_ctKey`,
`wireColumnTools`, `wireSortable`, los combos de edición y `capFilter`; el IIFE «Matriz de
obra»; `styles.css` (el aviso usa `alert info`); `parte_detail.html`, `papelera.html`,
`conciliacion.html`; los endpoints, `orm_models.py`, sv1, sv2, sv3, sv5 e `infra/`.

**Solape con F-061** (en marcha en `partes-wt-f061`), para la fusión:

| Fichero | F-061 toca | F-064 toca |
|---|---|---|
| `static/app.js` | ≈ l. 1457–1561 y 2753 | ≈ l. 82, 893–990 y 2829–2846 |
| `partes_list.html` | l. 66 | l. 34 |
| `app.py` | sus rutas | junto a `_actor` |
| `docs/ARCHITECTURE.md` | semántica 8 | punto 11 |

Son trozos distintos: se espera fusión limpia. `_irTrasBorrar` (F-061) navega a `/partes` sin
consulta; con R19 vuelve a la búsqueda guardada, que es lo deseado (se mira en M1).

## 4. Funciones

### 4.1 `clave_filtros(actor: str, origen: str) -> str` (interface_adapters, pura)

`""` si `origen == "sin-identidad-desplegado"` o el actor está vacío; si no,
`hashlib.sha256(actor.encode("utf-8")).hexdigest()[:16]`. Sin sal: no protege nada que no sepa
ya quien usa ese navegador; solo evita dejar el UPN en claro en `localStorage` y en el HTML.

### 4.2 Global `clave_filtros_de(request)` en `app.py`

`lambda request: clave_filtros(*_resolver_identidad(request))`, registrada en
`templates.env.globals` **después** de definir `_resolver_identidad` y `_actor`. No lee
cabeceras: delega. Efecto aceptado: con la autenticación caída, cada página renderizada deja
también el WARNING de R5b de F-017 («cada una es un incidente»), y el INFO de primer arranque
puede salir en un GET de página. Ningún texto de log cambia.

### 4.3 `var FiltrosSesion = (function () { … })();` (app.js, global)

Constantes y puras a dos espacios, para que `_funcion()` de los tests las extraiga:
`PREFIJO = "partes.filtros.v1:"`, `SESION_MS = 8 * 3600 * 1000` (DA2, M0), `MAX_PANTALLAS =
50` y `LISTAS_SERVIDOR = {"/partes": ["search", "pendientes"], "/obras": ["search"],
"/trabajadores": ["search"]}`.

**Puras** (sin DOM ni `localStorage`):
- `claveAlmacen(usuario)`: `""` sin usuario; si no, `PREFIJO + usuario` (R4, R5, R9).
- `rutaNormal(pathname)`: sin barras finales; `""` ⇒ `/`.
- `estadoVigente(crudo, ahoraMs)`: el estado, o `null` si es inválido, de otra versión, con `t`
  no numérico, `ahora - t >= SESION_MS` o `t > ahora + 60000` (R6).
- `conPantalla(estado, ruta, foto, ahoraMs)`: estado **nuevo** con `t = ahora`; una foto vacía
  quita la ruta y otra la pone con `foto.t = ahora`; después poda a las 50 de mayor `t` (R7,
  R10, R14).
- `fotoVacia(foto)` (R14) y `filtrosRepuestos(foto)`: `true` si hay columnas o días, lo que
  enciende el aviso (R17).
- `consultaDeLista(ruta, search)`: `null` si la ruta no es una lista o `search` trae otro
  parámetro; si no, la consulta normalizada (permitidos en orden fijo, sin vacíos; `""` si no
  queda ninguno) (R19).
- `destinoRestaurar(ruta, search, pantalla)`: `ruta + "?" + pantalla.query` solo si la ruta es
  una lista, `search === ""` y la guardada no es vacía; si no, `null` (R19).
- `diasRestaurables(guardados, periodo, disponibles)`: la intersección en el orden de
  `disponibles` si coincide el periodo; si no, `[]` (R12, R16).

**Con DOM** (todo acceso a `localStorage` en `try/catch`, R5):
- `usuario()` lee `document.body.dataset.filtrosUsuario`; `leer()` y `escribir(estado)` borran
  la clave si el estado no es vigente; `barrerCaducados(ahora)` recorre las claves con `PREFIJO`
  y borra las no vigentes (R8).
- `claveTabla(table)` y `claveColumna(table, input)` (R11); `periodo()` = `#period` + `|` +
  `.cal-period input[name=modo]` (R12).
- `foto(dias)`: columnas no vacías del DOM, `dias.claves()`, la casilla y `consultaDeLista`.
- `guardar()`: no hace nada mientras `restaurando` está activo.
- `redirigir()`: `location.replace` y `true` si `destinoRestaurar` da una URL.
- `restaurar(dias)`: (1) activa `restaurando`; (2) repone columnas (`value` + `input` con
  burbuja); (3) días con `dias.seleccionar(…)`; (4) casilla (`checked = false` + `change`); (5)
  desactiva `restaurando` y hace **un** `guardar()`; (6) pinta el aviso si toca; (7) engancha
  `lineas:cambio` y el `change` de `#hide-sin-extra` a `guardar` (R10, R15).
- `quitarTodo(dias)` (R17): pulsa cada `.filter-clear` (o vacía y dispara `input`),
  `dias.limpiar()`, marca la casilla con `change`, borra la entrada y oculta el aviso.

API pública: `{ redirigir, restaurar }` y, para los tests, las puras.

### 4.4 Días: el manejador de `_setupDaySelection`

Devuelve `{claves(), disponibles(), seleccionar(lista), limpiar()}`: `seleccionar` añade al
`Set` las claves que existen, pone `.day-selected` y llama a `apply()`; `limpiar` es
`clearAll`. `wireDayFilters` devuelve el del calendario o el de la matriz (una página tiene uno
o ninguno) o, si no hay, uno nulo con las cuatro funciones vacías. Lo demás del cierre no
cambia: el clic y «Quitar filtro» siguen igual.

### 4.5 Cableado en el `DOMContentLoaded` principal

```js
if (FiltrosSesion.redirigir()) return;          // 1.ª línea (R19)
var dias = wireDayFilters();                    // antes: wireDayFilters();
FiltrosSesion.restaurar(dias);                  // justo ANTES de restaurarVista() (R15)
restaurarVista();
```

La casilla de la matriz se repone aquí, **antes** del `ready` del IIFE «Matriz de obra», que
luego llama a `applySinExtra()` leyendo `checked`; el `change` cubre el orden contrario.

## 5. El estado guardado (`localStorage["partes.filtros.v1:<clave>"]`)

```json
{"v": 1, "t": 1761480000000,
 "pantallas": {"/obras/obr-10": {"t": 1761480000000,
    "cols": {"matriz": {"Trabajador": "lopez"}, "lines-table": {"Tipo": "extra"}},
    "dias": {"periodo": "2026-10|nomina", "claves": ["lopez|2026-10-03"]},
    "sinExtra": false},
   "/partes": {"t": 1761470000000, "query": "search=0404&pendientes=1"}}}
```

Se guardan textos tecleados y claves de la página: nada que ese navegador no haya mostrado ya.

## 6. Tests (sin red ni BBDD; `test_f064_rN_…`; datos sintéticos)

- `test_f064_clave_usuario.py`: la pura (16 hexadecimales, determinista, distinta para dos
  actores, `""` con `sin-identidad-desplegado`) (R1, R2); `TestClient` sobre `/partes` con
  `X-MS-CLIENT-PRINCIPAL-NAME` de dos usuarios inventados ⇒ atributos distintos y sin el actor
  en el HTML (R1, R3); con `CONTAINER_APP_NAME` y sin cabecera ⇒ atributo vacío (R2); sin
  cabeceras en local ⇒ la clave de `local:…`. `test_f017_punto_unico.py` corre tal cual (R3).
- `test_f064_filtros_js.py`, puras con node: caducidad en el borde (exactamente `SESION_MS` ⇒
  caduca), JSON roto, otra versión y `t` futuro (R6); poda a 50 por `t` (R7); foto vacía borra
  la entrada (R10, R14); `claveAlmacen` de A ≠ de B y `""` sin usuario (R5, R9);
  `consultaDeLista` con `search=&pendientes=1`, con `message=…`, en otro orden y todo vacío
  (R19); `destinoRestaurar` con consulta, sin guardada y con guardada vacía (R19);
  `diasRestaurables` con otro periodo, intersección y orden (R12, R16); `filtrosRepuestos`
  (R17).
- `test_f064_filtros_js.py`, DOM falso mínimo (como F-043): `restaurar` repone por (tabla,
  columna) aunque se hayan movido las columnas, hace **una** escritura, ignora una columna
  inexistente, y un `lineas:cambio` posterior guarda (R10, R11, R15, R16, R18).
- `test_f064_filtros_js.py`, leyendo el fuente: `redirigir()` es la primera línea del
  `DOMContentLoaded` principal y `restaurar(` va antes de `restaurarVista()` (R15, R19); las
  tres listas llevan `?search=` en «Limpiar» (R20); `FiltrosSesion` no menciona `PartidaSel` ni
  `sel-linea` (R21); los cuerpos de `conjuntoAprobacion`, `restaurarVista`, `vistaRestaurable`
  y `_ctKey` no cambian respecto de `dev` (hash del texto de cada función fijado en el test)
  (R22, R23). El límite (R24) se comprueba en T8 con `git diff --stat dev`, no en un test.

## 7. Riesgos y decisiones

- **Aprobar menos de lo que se cree.** Con un filtro repuesto, «✓ Aprobar visibles (n)» aprueba
  solo lo visible (F-022 R6); lo demás queda pendiente, que es el sentido seguro. El aviso de
  R17 y el texto del botón lo hacen visible. Aprobar una línea oculta es imposible: la selección
  no se guarda (R21) y una seleccionada oculta nunca se envía.
- **Ordenador compartido.** Las claves por usuario separan los filtros. Las de un usuario siguen
  hasta 8 h en el navegador, legibles con las herramientas de desarrollo; contienen filtros, no
  datos, y hoy todos los usuarios del portal ven lo mismo (sin roles, F-008).
- **Doble carga en listas.** Llegar sin consulta a una lista con búsqueda guardada cuesta un
  render de más. Reescribir los enlaces de la barra se descarta: no cubre `/`, F-061 ni una URL
  tecleada.
- **F-043.** Su reposición por posición sigue funcionando: llega después de la de F-064 y, con
  los mismos valores, no hace nada (`valor === f.value`).
- **Varias pestañas**: gana la última escritura. **Columnas condicionales**
  (`transfer_enabled`, `preview_enabled`): van por clave, no por posición; lo que falta se ignora.

## 8. Verificación manual

- **M0** (líder, solo lectura, antes de T1):
  `az containerapp auth show -n ca-sv4-front -g rg-partes-dev --query login.cookieExpiration`.
  Si da `08:00:00` o no está fijado (8 h por defecto según la documentación de Easy Auth),
  `SESION_MS` = 8 h; si da otro valor, se usa ese y se anota en `progress/current.md`.
- **M1** (humano o líder; portal local con `python main.py` contra la base de desarrollo
  habitual; solo se mira, no se aprueba nada fuera de la 0404):
  1. `/obras`: busca «04» y filtra Empresa; entra en una obra y vuelve con la barra ⇒ ambos
     repuestos, con el aviso.
  2. `/obras/<key>`: Tipo = extra, dos casillas de la matriz y casilla desmarcada; sal, vuelve
     y Ctrl+F5 ⇒ todo repuesto («Filtrando por 2»); otro mes ⇒ sin días; de vuelta ⇒ días.
  3. «Quitar filtros» ⇒ limpio, también al volver; «Limpiar» de `/obras` ⇒ no vuelve la búsqueda.
  4. Pestaña nueva ⇒ los mismos filtros.
  5. Con un filtro repuesto, el botón dice «Aprobar visibles (n)» y no hay filas seleccionadas.
  6. En las herramientas de desarrollo, baja `t` 8 h y recarga ⇒ limpio y clave borrada.
- **M2** (humano, tras desplegar sv4): A filtra `/partes`; `/.auth/logout` y entra B en el mismo
  navegador ⇒ sin filtros; vuelve A ⇒ los suyos; dos claves `partes.filtros.v1:*`, sin UPN.

## 9. Decisiones abiertas (recomendada: A en todas)

- **DA1 · Qué filtros entran.** **A**: los de cliente de §2 (columnas de todas las tablas, días,
  casilla de la matriz) más la búsqueda del servidor de las tres listas. B: solo los de cliente.
  C: A más `period` y `modo` de los detalles; se descarta porque un mes repuesto en silencio
  cambia lo que se aprueba sin tocar ningún filtro, y mañana el mes por defecto es otro.
- **DA2 · Dónde y qué es «sesión».** **A**: `localStorage` con clave por usuario y caducidad a
  las 8 h sin actividad (la de Easy Auth, M0); sobrevive a pestañas nuevas y a cerrar el
  navegador dentro de la jornada. B: `sessionStorage` (por pestaña) con clave por usuario; una
  pestaña nueva empieza vacía. C: el servidor, con una tabla por actor en `partes`: esquema nuevo
  (`orm_models.py` de sv3 y sv4), una escritura por tecla y otro rigor. Con A y B, otro usuario
  en el mismo navegador no ve nada del primero.
- **DA3 · Ámbito.** **A**: por pantalla concreta (la ruta): cada obra y cada trabajador tiene los
  suyos, y los días además por periodo. B: por tipo de pantalla (el filtro de líneas sigue a
  otra obra). C: global por nombre de columna. B y C hacen aparecer el filtro donde no se puso.
- **DA4 · Limpieza.** **A**: «Limpiar» y «Quitar filtro» guardan el vacío; aviso con «Quitar
  filtros» al reponer; caducidad de 8 h y barrido de caducados. B: A más un «Olvidar mis
  filtros» global en la barra. C: sin aviso. El portal no tiene «cerrar sesión»: lo cubren la
  clave por usuario y la caducidad.
- **DA5 · «Actualizar» (F-043).** **A**: no se toca; F-064 repone antes. B: quitarle los filtros
  a F-043 (cambia sus tests).
- **DA6 · Selección de líneas.** **A**: nunca se guarda (R21, R22). B: guardarla; se descarta
  porque reaparecerían marcas en líneas ya cambiadas u ocultas.
- **DA7 · Sin identidad estando desplegado.** **A**: no se guarda nada (R2, R5). B: una clave
  común, que mezclaría a todos justo cuando la autenticación falla.
