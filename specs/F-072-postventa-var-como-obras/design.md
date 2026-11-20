# F-072 · Postventa y VAR como obras — Diseño

**Rigor: `critico`.** Disparador 2 de «Niveles de rigor» (`CHECKPOINTS.md`): cambia en qué obra y
partida escribe sv5 en la base `ruesma` de Sigrid, que es producción
(`services/partes-transfer/application/pipelines/registro_pipeline.py`, `hmores.obride` y
`hmores.paride`). Las reglas de referencia son `#regla-p5` y `#regla-var` de
`porcentajes/docs/ARCHITECTURE.md` y su código (`universo_postventa.py`, `universo_var.py` y
`partida_resolver.resolver_postventa`), leídos en `5381243`, solo lectura.

## 0. Quién hace qué (LÍMITE DE SERVICIO)

| Servicio | Papel en F-072 |
|---|---|
| sv2 | Copia la marca del papel en `obra_numero`. No consulta Sigrid por una obra con marca (no relee). No casa nada. |
| sv3 | Lee la forma, elige la obra agrupada de la empresa y casa la entrada. Deja la partida y la marca en las líneas. Sin entrada, el parte va a revisión. |
| sv4 | Catálogo de entradas (selector, cambio de obra, alta manual), clave `agr-` de las vistas, partida fija. |
| sv5 | Guarda antes de escribir: entrada, hoja activa y universo VAR. Conflictos por partida en las obras agrupadas. |

La lógica común (casado P5, universo VAR, lectura de la forma) es **un módulo puro gemelo**,
byte-idéntico en sv3, sv4 y sv5 (DA4). No hay canal sv3→sv4 ni librería compartida, y el
transfer de porcentajes tiene ingress interno en otro entorno, `cae-dedicacion-dev` («solo la
api», `azure-apps/dedicacion.md`). Por eso se reimplementa con tests de equivalencia (R10).

## 1. Modelo: la entrada vive en la línea, sin columnas nuevas (DA5)

- Línea de una entrada: `obra_ide` = la obra agrupada de su empresa, `partida_*` = la de la
  entrada y `partida_match_method` = `postventa`/`var` (la **marca**). Con eso, sv4 deriva la
  clave `agr-<obra_ide>-<partida_ide>` y el rótulo sin configuración (R23, R24), el conciliador
  de sv3 la salta como a `manual` (R20) y sv5 recibe la marca como `partida_metodo` (R33, R36).
- El documento lleva la obra agrupada en sus `obra_*`; `obra_numero_leido` guarda lo leído.
- **Clones**: `_campos_extra` (sv3) y `_CAMPOS_CLON_CELDA` (sv4) ya clonan `partida*` y el
  método (R21, un test lo fija); la extra del popup de sv4 (`parte_repository.py` ~l. 1956) no,
  y se corrige (R31).
- **Descartado**: columnas nuevas (9 en el ORM gemelo, que habría que copiar en los 6 sitios que
  crean líneas, con riesgo de una extra con otra clave que su base) y `obra_ide` negativo como
  en porcentajes (rompería sv5, la jornada y el sincronizar).

## 2. Reglas puras: `application/services/obras_agrupadas.py` (sv3, sv4, sv5; gemelo)

Solo biblioteca estándar (`re`, `unicodedata`, `dataclasses`), sin importar `text_match` (sv5 no
lo tiene). Las hojas llegan por duck typing (`ide`, `cod`, `res`, `es_hoja`, `activa`):
`PartidaNodo` en sv3 y sv4, y en sv5 la fila de §6.

```python
POSTVENTA, VAR = "postventa", "var"            # marcas (= partida_match_method)
def normalizar(cod) -> str                      # mayúsculas, sin acentos, espacios ni guiones
def casar_postventa(hojas, codigo_obra) -> Hoja | None          # R4-R6
def numero_inicial(cod) -> int | None; def es_partida_var(hoja, desde) -> bool  # R7
def casar_var(partidas_var, leido) -> Hoja | None               # R8
@dataclass(frozen=True) class Forma: tipo: str; resto: str      # resto "" = base
def leer_forma(leido, *, postventa: Sequence[str], var: str | None) -> Forma | None  # R9
def es_obra_agrupada(codigo, *, postventa: str | None, var: str | None) -> str | None
def codigo_entrada(tipo, var_cod, partida_cod) -> str          # «Postv-0578» / «VAR-29»
```

Para R6, entre exactas gana la de menor `ide`. Porcentajes toma `exactas[0]` en el orden de sus
filas. No hay ningún caso conocido con dos exactas: se anota en R10, no se copia.

## 3. sv2 (`services/partes-api`)

- `config/settings.py`: lee los cuatro ajustes (R1). sv2 solo usa los códigos y los alias.
- `domain/models/clave_obra.py`: `tiene_marca(codigo, marcas) -> bool`. La clave (R9 sobre
  `clave_obra`) empieza o acaba por una marca y tiene algo más. Es una regla de «no consultes»,
  no el casado.
- `application/services/obra_sigrid.py`: `ComprobadorObra(marcas=…)`. Con marca devuelve
  `existe=None` sin llamar al cliente (R13). `motivo_relectura` ya trata `None` como «no se
  sabe» y no se toca.
- `config/prompts.yaml`: una línea en la cabecera para que `obra_numero` copie la marca entera
  con su separador (R12). El esquema no cambia.
- Cableado en `main_worker.py` / `main.py`, donde hoy se crea `ComprobadorObra`.

## 4. sv3 (`services/partes-persistencia`)

- `config/settings.py`: cuatro ajustes con validación R2.
- **Nuevo** `application/services/entrada_agrupada.py`:
  `ResolutorEntradas(lookup, ajustes, ttl_seconds=600)` con
  `resolver(parte, matchers, empresa_m, discriminantes) -> ResultadoEntrada(obra: ObraMatch,
  partida: PartidaNodo | None, tipo: str | None)`. Cachea las hojas de cada obra agrupada
  (`fetch_partidas_obra` + `build_arbol_partidas`). Los fallos no se cachean y suben (R19).
  - **VAR** (R14): `matchers.obra.match(codigo=VAR_OBRA_COD, nombre=None, …)` elige entre
    gemelas como cualquier código; luego `casar_var` sobre `es_partida_var`.
  - **Postventa** (R15): primero `matchers.obra.match(codigo=resto, nombre=None, …)`; X
    agrupada ⇒ `postventa_obra_no_casa`. La obra de postventa de `X.empresa` se toma de
    `ObraMatcher.obras_de_codigo(cod)` (método nuevo de solo lectura): ninguna o varias ⇒
    `agrupada_sin_obra`. Después, `casar_postventa(hojas, X.codigo)`.
  - **Base** (R16): por cada `partida` leída distinta y no vacía, lo mismo; el conjunto de
    entradas `(obra, partida.ide)` tiene que tener un solo elemento.
- `application/pipelines/persist_parte_pipeline.py::_match`: antes del casado de obra,
  `leer_forma(parte.obra_numero_leido, …)`.
  - Con forma, `ResolutorEntradas`. Con entrada, `parte.obra` y cada registro reciben
    `partida_*` (`partida_capitulo` del nodo, método = tipo, puntuación 1.0). Sin entrada,
    `ObraMatch(method=<motivo R17>)`; `empresa_del_parte` y F-054 siguen igual.
  - Sin forma, el casado de siempre. Si da una obra agrupada (`es_obra_agrupada`), se repite
    como forma base (R18).
  - `_compute_review_required` ya manda a revisión el parte sin obra.
- `domain/models/parte_records.py`: `ParteDocumento.entrada: EntradaPartida | None` (`ide`,
  `cod`, `res`, `capitulo`, `tipo`). `save_parte` (`sqlalchemy_parte_repository.py`) hoy solo
  guarda `partida` leída: con entrada, escribe `partida_*` y la marca en cada línea.
- `application/services/partida_conciliador.py::conciliar_todos`:
  - salta los métodos `postventa` y `var` como salta `manual`;
  - un registro sin marca cuya obra sea agrupada recibe `_sin` (R20).
  Para eso `fetch_registros_para_partida` devuelve además `obra_codigo`, y el conciliador
  recibe los códigos con `es_obra_agrupada`.
- Cableado en `main_worker.py` y `main.py`, junto a `PartidaConciliador`.
- Jornada, extras y franquicia (R22): sin cambios. `reparto_ponderado` agrupa por `obra_ide`:
  dos entradas de la misma obra agrupada el mismo día pesan como una obra, y entre líneas el
  reparto sigue siendo proporcional. Solo puede cambiar el redondeo a medias horas. Un test lo
  documenta.

## 5. sv4 (`services/partes-front`)

- `config/settings.py`: cuatro ajustes (R2). `POSTVENTA_ALIAS` no se usa en sv4.
- **Nuevo** `application/services/catalogo_entradas.py`: `CatalogoEntradas(obra_catalog,
  sigrid_client, ajustes, ttl_seconds)` con `entradas() -> list[Entrada]` y
  `entrada(obra_ide, partida_ide) -> Entrada | None`.
  - `Entrada(tipo, obra_ide, obra_codigo, obra_nombre, empresa, partida_ide, partida_cod,
    partida_res, partida_capitulo, codigo, nombre)`.
  - Por empresa, la obra agrupada única (R25) y sus hojas con
    `fetch_partidas_obra` + `build_arbol_partidas`.
  - Postventa: cada `ObraOption` de esa empresa no agrupada con `casar_postventa` (índice por
    código normalizado, no un bucle obras × hojas).
  - Un fallo de lectura deja `[]` con WARNING; las obras normales siguen.
- `infrastructure/database/parte_repository.py`:
  - `obra_key_for_registro`: con marca y `partida_ide`, `agr-<obra_ide>-<partida_ide>` (R23).
    `_obra_key_for_doc` usa la clave común de las líneas activas; con varias devuelve
    `mixta-<id>` (sin vista) y `soft_delete_obra` lo salta con WARNING.
  - `list_obras` / `get_obra`: rótulo con `codigo_entrada` y la descripción de la partida
    (R24). La configuración no hace falta: `VAR_OBRA_COD` se toma de `obra_codigo`.
  - `update_parte_obra(…, entrada: Entrada | None)`: con entrada pone la partida y la marca en
    las líneas no congeladas (R27). Al salir de una entrada devuelve los objetivos sin código
    para que queden en `sin` (R29). La congelación no cambia (F-004).
  - `crear_parte_manual(…, entrada=None)`: busca el documento activo del día y la obra, y
    además la misma entrada (R30).
  - `set_registro_partida`: con marca, `PartidaFijaError` (R32). La extra del popup copia la
    partida y la marca de su base (R31).
- `interface_adapters/web/app.py`:
  - `/api/sigrid/obras` añade las entradas y quita las agrupadas (R26).
  - `ObraPayload.partida_ide: int | None`.
  - `patch_parte_obra` y `/api/partes/nuevo`: una obra agrupada sin entrada válida ⇒ 422
    (R27, R28). Con entrada no se recasa por código.
  - `api_set_registro_partida` traduce `PartidaFijaError` a 409.
  - Cableado de `CatalogoEntradas`.
- `lineas_para_registro` / payload a sv5: cada línea lleva `partida_metodo` (R33). El reparto
  por `obra_key_for_registro` ya da una petición por entrada.
- `application/services/sincronizar_ambito.py`: `agr-` no lleva ide ⇒ `motivo_no_sincronizable`
  ya responde. Se añade un motivo propio, «entrada de obra agrupada: se sincroniza la obra
  entera en Sigrid» (R34).
- `static/app.js`: los tres usos de `/api/sigrid/obras` (l. ~1088, 2443 y 2650) muestran
  `codigo · nombre` y mandan `partida_ide` si el ítem lo trae (R35).

## 6. sv5 (`services/partes-transfer`)

- `config/settings.py`: tres ajustes (sin alias) y R2.
- `domain/models/registro_models.py`: `LineaEntrada.partida_metodo: Optional[str] = None`;
  `LineaSigrid.paride: Optional[int] = None`.
- `infrastructure/sigrid/sigrid_write_client.py`:
  - **nuevo** `partidas_de_obra(obra_ide) -> list[PartidaHoja]` (`ide`, `cod`, `res`,
    `es_hoja`, `activa`; `tipdes` y `EXISTS` de un hijo en `obrparpar`), una lectura con
    `SIGRID_API_MAX_ROWS`, `truncated` ⇒ error (R37, R39);
  - `lineas_existentes` añade `hmores.paride`.
- `application/pipelines/registro_pipeline.py`: tras `_con_empresa`, si
  `es_obra_agrupada(obra_origen.codigo)`, una lectura de `partidas_de_obra(obra_origen.ide)` y,
  antes de `ReglasRegistro.decidir`, `omisiones[registro_id] = motivo` (mecanismo que ya
  existe), con el motivo de la función pura nueva `motivo_partida_agrupada(linea, hojas, tipo,
  desde)` en `application/services/reglas_registro.py` (R36). El preflight comparte pipeline.
- `application/services/pisado.py::choques(…, por_partida: bool = False)`: con `True` exige
  además `ls.paride == accion.paride` (R38). El pipeline lo activa en las obras agrupadas, en
  `_choques`, `_motivo_sin_pisado` y R11.
- `tests/test_f038_lectores_sigrid.py` (raíz): suma `partidas_de_obra` (R39).

## 7. Configuración, despliegue y orden

- Valores para producción, leídos de lo versionado en porcentajes (`settings.py` del transfer e
  `infra/create_transfer_dedicacion.ps1`): `POSTVENTA_OBRA_COD=POSTV2`, `VAR_OBRA_COD=VAR`,
  `VAR_PARTIDA_DESDE=29`. `POSTVENTA_ALIAS=POSTVENTA,POSTV` es la propuesta (DA2). No son
  secretos: se ponen con `az containerapp update --set-env-vars`, documentado en
  `infra/README_partes.md` y `azure-apps/partes.md`.
- Código con todo vacío, sin efecto (R3), en el orden seguro sv2 → sv3 → sv5 → sv4 (sv5 antes
  que sv4, que manda `partida_metodo`). Encendido: **sv5 → sv3 → sv2 → sv4** (guarda primero,
  selector al final). Apagado = vaciar las variables; las líneas marcadas conservan su entrada
  (la clave no depende de la configuración).

## 8. Partes ya guardados (DA9)

No se recasa nada ingerido. Un parte que hoy esté en POSTV2 o VAR (sin marca) sigue con la clave
`obr-<ide>`. Desde F-072 sus líneas sin marca quedan en `sin` (R20), y sv5 las omite con
`partida_agrupada: … sin entrada` (R36). Se arreglan con «cambiar obra» a la entrada (R27). Lo
`registrado` está congelado y no se toca. M0 mide cuántos hay.

## 9. Ficheros

**Crear**: `services/partes-{persistencia,front,transfer}/application/services/obras_agrupadas.py`,
`services/partes-persistencia/application/services/entrada_agrupada.py`,
`services/partes-front/application/services/catalogo_entradas.py`; en `tests/` de la raíz
`test_f072_obras_agrupadas_gemelos.py` (R11), `test_f072_equivalencia_porcentajes.py` (R10) y
`test_f072_documentacion.py` (R40); y los `test_f072_*.py` de cada servicio.

**Modificar**: los de §3–§6, `docs/ARCHITECTURE.md` (semántica 24), `CLAUDE.md` (lista cerrada),
`infra/README_partes.md` (variables) y `harness/servicios.json` (`depende_de` de los gemelos,
para que la caché de suites no los salte). En `azure-apps`, commit aparte: `partes.md` §3.3–§3.5,
§4.5 bis, §5.6 y el aviso a porcentajes.

## 10. Qué NO se toca

`orm_models.py` (ni columnas ni DDL) y `dedicacion_bandeja` (DA10); sv1, colas y mensajes;
`reajuste_pipeline.py` y `franquicia_pipeline.py` (copian obra y partida de líneas que ya pasaron
la guarda); `jornada_resolver`, `festivos_guardados`, `congelacion.py`, `incidencias_horas.py`;
el repo `porcentajes` y su regla de los seis dígitos (no se pide); el filtro por estado (DA6) y
sincronizar por entrada (DA12).

## 11. Riesgos y alternativas

- **El papel es la incógnita** (DA1): si escriben otra cosa, el parte va a revisión sin obra
  (R17), nunca a una obra equivocada. M0 lo mide antes del encendido.
- **Configuración distinta entre servicios**: sv5 es la red (sin marca no escribe en una obra
  agrupada); las variables se ponen a la vez (§7).
- **Divergencia con porcentajes**: R10 la detecta; una línea de los dos en la misma obra, mes y
  partida ya la gestiona el pisado de F-031 y F-053.
- **Coste en sv4**: 2 lecturas de `obrparpar` por empresa con obra agrupada cada 10 min; hoy
  solo la empresa 1 (porcentajes F-025, D4).
- **Descartado**: el universo del transfer de porcentajes (otro entorno, ingress que su documento
  prohíbe abrir) y la lógica solo en sv4 (sv3 no puede llamarlo).

## 12. Frontera

**¿Cruza la frontera del proyecto? Sí.** sv5 escribe en Sigrid (`hmores`) en las obras POSTV2 y
VAR y en sus partidas, las mismas de `porcentajes`; hay variables nuevas en sv2–sv5; y
`dedicacion_bandeja` llevará líneas con obra agrupada y partida, sin columnas nuevas. Se
actualiza `azure-apps/partes.md` (variables, «qué se rompe si cambia» y el aviso a porcentajes:
POSTV2 + partida es `Postv-X` y VAR + partida, su entrada). `dedicacion.md` es de porcentajes y
no se toca.

## 13. Decisiones

| Decisión | Opciones | Recomendado | Decidido |
|---|---|---|---|
| DA1 Qué escribe el encargado en el papel | (a) marca en «Nº OBRA», delante o detrás: `VAR-29`, `POSTVENTA 578`; con solo `VAR`/`POSTV2`, la partida de la sección de partidas (R9, R16); (b) solo la marca en «Nº OBRA»; (c) solo la obra agrupada más la sección de partidas | (a) | |
| DA2 Palabras de postventa | (a) `POSTVENTA_OBRA_COD` + `POSTVENTA_ALIAS=POSTVENTA,POSTV`; (b) también `PV`; (c) solo el código | (a) | |
| DA3 Relectura de sv2 con marca | (a) no consulta ni relee; (b) sin cambio: relee, y en el peor caso el parte va a revisión | (a) | |
| DA4 Dónde vive la lógica común | (a) gemelo byte-idéntico en sv3, sv4 y sv5 en la lista cerrada de `CLAUDE.md`, reimplementado de porcentajes con R10; (b) pedirla al transfer de porcentajes por HTTP; (c) solo en sv4 | (a) | |
| DA5 Cómo se guarda la entrada | (a) en la línea: obra agrupada + partida + marca, sin columnas; (b) columnas nuevas en `parte_documents`/`parte_registros` | (a) | |
| DA6 «Obra cerrada del universo, solo como postventa» | (a) no aplica: partes no filtra obras por estado y ofrece X y `Postv-X`; (b) leer el estado y ofrecer solo `Postv-X` si X está cerrada; (c) (b) y además mandar a revisión el parte de una X cerrada sin marca | (a); (b)/(c) en otra feature | |
| DA7 Obras agrupadas como obra normal | (a) ni VAR ni POSTV2 se ofrecen; sin entrada ⇒ 422; (b) solo VAR, como porcentajes | (a) | |
| DA8 Conflictos en sv5 | (a) en una obra agrupada solo choca la misma partida (como `#regla-conflicto` de porcentajes); (b) como hoy: falsos conflictos entre entradas del mismo día | (a) | |
| DA9 Partes ya guardados en POSTV2/VAR | (a) no se recasan; se arreglan con «cambiar obra» y sv5 omite lo que no tenga entrada; (b) script de migración | (a) | |
| DA10 Bandeja de dedicación | (a) sin columnas nuevas; documentar y avisar a porcentajes; (b) añadir `es_postventa` y la obra origen | (a) | |
| DA11 Valores de configuración | (a) sin defecto en el código (vacío = apagado), valores en el despliegue; (b) defectos en el código como porcentajes (`POSTV2`, `VAR`, `29`) | (a) | |
| DA12 Sincronizar (F-052) una entrada | (a) fuera: «no sincronizable» con motivo; (b) filtrar las líneas de Sigrid por partida | (a) | |
