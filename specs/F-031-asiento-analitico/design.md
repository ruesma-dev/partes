<!-- specs/F-031-asiento-analitico/design.md -->
# F-031 · Diseño técnico

Datos (solo lectura, agregados): `progress/spec_F-031.md`, anexo §D1–§D8.

## 1. Cómo contabiliza Sigrid un parte (lo que NO hay que construir)

- Estados del parte (`conest`, tipo 35): 1 «En registro», 3 «Cerrado», 10
  «Imputado» (los dos últimos solo los editan los roles ADM y COS).
- Administración cierra el parte del mes y, semanas o meses después, lanza
  el proceso de Sigrid «Contabilizar parte» (log: «Proceso de Cambio de
  estado (HMO …): Contabilizar parte», lotes de 12–32 partes; últimos
  2026-09-02 y 2026-09-14). El parte pasa a Imputado y Sigrid crea **un**
  asiento analítico por parte: `con` tipo 32 + `asa`, código `ANA<AA>/NNNNN`,
  mismo `con.res` y `con.fec` que el parte (497/497 en 2025–26), con apuntes
  `apa`: Debe = Σ `hmores.tot` por `hmores.caaide` (cuentas del centro de la
  obra; las líneas con `caaide = 0` no entran) y Haber = Σ por
  `res.caaconide` del recurso (centro `CP`, una cuenta por trabajador).
  465/497 asientos cuadran al céntimo con las líneas actuales; los 31
  restantes son partes tocados después de contabilizar (§D3).
- No hay clave entre el parte y su asiento (`apa.doc` vacío, `hmores` sin
  campo de asiento): se casan por empresa + resumen + fecha. `salapa`
  (saldos) está vacía: Sigrid calcula los saldos al vuelo.
- 2026, empresa 1: Imputados 33 de enero, 17 de febrero, 1–2 de marzo a
  julio; Cerrados 17–39 por mes de febrero a agosto; septiembre en
  registro. Empresa 28 (y 18): 0 asientos analíticos y 0 `caaide`, nunca.
- Hoy sv5 tiene en Sigrid solo 4 líneas (empresa 28, septiembre).

Conclusión: el asiento lo hace Sigrid y la cuenta ya la pone F-021. El fallo
posible está en **dónde** escribe sv5: `partes_existentes` coge el `hmo` más
reciente del periodo sin mirar `con.est` y `lineas_existentes` solo mira ese
parte. Línea añadida a un parte Imputado = fuera de la analítica para
siempre; pisar ahí = asiento que ya no cuadra.

## 2. Servicios que toca y por qué (límite de servicio)

- **sv5** (`partes-transfer`): única escritora de Sigrid; elige el parte.
- **sv4** (`partes-front`): solo pinta `partes[].aviso` en el modal.
- Ni sv3, ni la base `partes`, ni el ORM, ni sigrid-api. Ningún servicio
  nuevo: contabilizar sigue siendo de Administración en Sigrid (DA4).

## 3. Encaje en la arquitectura

Paso 5 del pipeline de sv5 (`_evaluar`, dentro del lock al escribir):
lectura nueva `partes_del_periodo` (infraestructura) + regla pura
`elegir_parte` (application). Paso 6 bis nuevo: choques con contabilizados
→ `omitir`. Paso 7 (conflictos pisables) sin cambios: solo ve el parte
elegido. Paso 8 crea el complementario igual que crea hoy un parte nuevo.

## 4. Ficheros a crear

- `services/partes-transfer/application/services/estado_parte.py` — regla
  pura (§6.1).
- `services/partes-transfer/comprobar_asiento_analitico.py` — consola, solo
  lectura (§6.4).
- Tests sv5: `tests/test_f031_estado_parte.py` (pura),
  `tests/test_f031_pipeline_estado.py` (pipeline con `SigridFake`),
  `tests/test_f031_cliente_partes.py` (SQL y parseo con `httpx` simulado,
  como `test_f021_cliente_cuenta.py`), `tests/test_f031_comprobar_asiento.py`.
- Test sv4: `services/partes-front/tests/test_f031_preflight_aviso_parte.py`.

## 5. Ficheros a modificar

- `services/partes-transfer/domain/models/registro_models.py`:
  `ParteSigrid` (frozen: `ide`, `cod`, `est`); `ParteDestino` gana
  `estado: Optional[int] = None`, `complementario: bool = False`,
  `contabilizados: list[str]`, `contabilizados_ide: list[int]` (ambas
  `field(default_factory=list)`) y `aviso: Optional[str] = None`.
- `.../infrastructure/sigrid/sigrid_write_client.py`: `partes_del_periodo`
  (§7). `partes_existentes` NO cambia (lo sigue usando el paso 8 para
  releer el parte recién creado: `ORDER BY ide DESC` lo devuelve primero).
- `.../application/pipelines/registro_pipeline.py`: paso 5 y paso 6 bis
  (§6.2), docstring de pasos.
- `.../config/settings.py`: `est_parte_imputado` (`EST_PARTE_IMPUTADO`,
  10) y `est_parte_cerrado` (`EST_PARTE_CERRADO`, 3); el pipeline los lee
  con `getattr(..., 10/3)` como `mensuales_a_dedicacion` (F-019 DA8).
- `services/partes-transfer/tests/dobles.py`: `SigridFake.partes_del_periodo`
  (estado `p.get("est", 1)`) y `partes_existentes` devolviendo el de mayor
  `ide` como el SQL real (hoy devuelve el primero); `SettingsFake` con los
  dos estados. Ningún test ajeno cambia.
- `services/partes-front/static/app.js`: en `resumenHtml`, tras cada parte,
  `" — " + esc(p.aviso)` si viene.
- `docs/ARCHITECTURE.md` (semántica 16, ≤ 8 líneas; herramienta en
  «Herramientas de consola»), `docs/referencia/partes-proyecto.md` (§3.5) y
  `C:\Users\pgris\PycharmProjects\azure-apps\partes.md` (§3.5: lectura de
  `con.est` del `hmo`, parte complementario; commit en ese repo, sin push).

## 6. Clases y funciones

### 6.1 `application/services/estado_parte.py` (pura, sin E/S)

```python
MOTIVO_PARTE_CONTABILIZADO = "parte_contabilizado"
def elegir_parte(ano: int, mes: int, partes: list[ParteSigrid], *,
                 est_imputado: int) -> ParteDestino
def aviso_de_parte(p: ParteDestino, *, est_cerrado: int) -> str | None
def motivo_contabilizado(cod: str) -> str
```

- `elegir_parte`: ordena por `ide` desc; el primero con `est !=
  est_imputado` es el elegido (`existe=True`, `ide`, `cod`, `estado`); los
  Imputados van a `contabilizados(_ide)`. Sin ninguno no Imputado:
  `existe=False`, `complementario = bool(contabilizados)`. Sin partes:
  `ParteDestino(ano, mes)` como hoy (R2, R3, R6).
- `aviso_de_parte` (se llama tras asignar `cod` propuesto): complementario →
  «los partes X, Y de MM/AAAA ya están contabilizados (Imputado); las líneas
  irán al parte nuevo PT…, que Administración tendrá que contabilizar»;
  `estado == est_cerrado` → texto de R5; resto → `None`.
- `motivo_contabilizado(cod)` → «ya hay horas de ese recurso, día y tipo en
  el parte {cod}, contabilizado (Imputado): corregirlo en Sigrid con
  Administración».

### 6.2 `RegistroPipeline._evaluar`

- Paso 5: `self._cli.partes_del_periodo(obra_ide, periodos)` → por periodo
  `elegir_parte(...)`; si `not existe`, `cod = siguiente_cod_pt(...)` (como
  hoy); `p.aviso = aviso_de_parte(...)`; INFO de R14.
- Paso 6 (synckey) sin cambios.
- Paso 6 bis: por cada periodo con `contabilizados_ide`, para cada `ide`,
  `lineas_existentes(ide, recursos, fechas)` del grupo `escribir`; una
  acción cuya clave (recurso, día, `horide`) choca con una línea sin su
  synckey → `accion="omitir"`, `motivo=motivo_contabilizado(cod)`,
  `caa_ide=0`, `caa_cod=caa_motivo=caa_aviso=None` (R8, F-021 R16).
- Paso 7 sin cambios: usa `parte.existe/parte.ide`, que ya es el elegido;
  un complementario (`existe=False`) no puede tener conflictos (R9).
- Paso 8: sin cambios de código; `p.creado=True` marca el complementario.

### 6.3 Contrato JSON

`asdict(ParteDestino)` ya viaja en `partes` del preflight (`api/app.py`) y
del resultado (`resultado_json.py`): los campos nuevos aparecen solos, sin
tocar esos ficheros (R13); sv4 no usa `contabilizados_ide`.

### 6.4 `comprobar_asiento_analitico.py` (consola, raíz de sv5)

`argparse` (`--empresa --obra --ano --mes`), `Settings()` y
`SigridWriteClient` (solo `_read`, nunca `escribir`). Función pura
`comparar(lineas_por_cuenta: dict[str, float], debe_por_cuenta: dict[str,
float], n_asientos: int) -> str` (`cuadra`/`descuadre`/`sin_asiento`/
`varios_asientos`, tolerancia 0,01). Imprime una tabla por parte y por
cuenta del centro; del Haber, solo el total (R23). `print` permitido
(script de consola, CONVENTIONS).

## 7. SQL (solo lecturas de Sigrid; ningún SQL de PostgreSQL)

`partes_del_periodo` (una por periodo, como `partes_existentes`):

```sql
SELECT hmo.ide AS ide, con.cod AS cod, con.est AS est FROM hmo
JOIN con ON con.ide = hmo.ide
WHERE hmo.obride = ? AND hmo.ano = ? AND hmo.mes = ?
  AND ISNULL(hmo.reside, 0) = 0 AND con.tip = ? ORDER BY hmo.ide DESC
```

Herramienta (tres lecturas, por `?`): partes del periodo por código y
empresa de obra (`con o ON o.ide = hmo.obride WHERE o.cod = ? AND o.emp =
?`, más `con.res`, `con.fec`); `hmores` agrupado por `hmoide` y código de
`caaide` con `SUM(tot)`, `COUNT(*)` y `SUM(CASE WHEN synckey LIKE
'partes:%' …)`; y `apa` del asiento (`asa` + `con` tipo 32, misma
`emp`, `res`, `fec`) agrupado por cuenta con `SUM(deb)`, `SUM(hab)`.
Todas con `truncated` → excepción (lo hace `_read`).

## 8. Decisiones abiertas (el humano aprueba; las contables, con Juan Romero)

- **DA1 (contable).** Todos los partes del periodo Imputados. (a) **Parte
  complementario** nuevo en registro, con su propio asiento cuando
  Administración lo contabilice — **recomendada** (Sigrid ya admite varios
  partes por obra y mes: 35 casos desde 2015; nada se pierde ni se toca lo
  contabilizado). (b) Omitir con motivo y que Administración reabra el
  parte. (c) Escribir en el Imputado (hoy) — descartada: queda fuera de la
  analítica sin aviso. Preguntas a Juan: ¿vale un asiento fechado a fin del
  mes del trabajo si ese mes ya está cerrado?, ¿«Contabilizar» se puede
  deshacer y rehacer?, ¿resumen igual «Parte <obra>»?
- **DA2 (contable).** Parte Cerrado: escribir y avisar — **recomendada** (el
  asiento aún no existe y las incluirá; el portal lo maneja la propia
  Administración) — frente a tratarlo como Imputado (abriría complementarios
  en casi todos los meses de 2026).
- **DA3.** Recurso sin contrapartida (`res.caaconide = 0`): su línea entra
  en el Debe sin Haber (asiento descuadrado). 2026: 3 recursos, 206 líneas,
  12.169 €. (a) Fuera: es dato maestro; se informa a Administración —
  **recomendada**. (b) Aviso en el preflight (otra lectura de `res`).
- **DA4.** sv5 **no** contabiliza ni escribe asientos — **recomendada**.
  Descartadas: replicar «Contabilizar» por SQL (`con`/`asa`/`apa`, serie
  ANA, cambio de estado reservado a ADM/COS, sin endpoint de dominio ni
  triggers, §7.1 de `sigrid_api.md`) y escribir un asiento propio (doble
  imputación cuando Administración contabilice el parte).
- **DA5.** Choque con una línea de un parte contabilizado: `omitir` con
  motivo — **recomendada** (vuelve a sv4 como `omitido`, editable) — frente
  a un conflicto «no pisable» en el modal (más sv4).
- **DA6 (contable, no cambia código).** La mano de obra entra en CI·MO
  (subcuenta de `reshor` por categoría: 12,8 M€ de Debe en CIMO, 0 en CD en
  2025–26). Si Juan quiere CD para operarios, se cambian plantillas `reshor`
  en Sigrid; F-021/F-031 lo siguen solas.
- **DA7.** Estados como ajustes con defectos 10/3 (catálogo configurable por
  instalación, `sigrid_api.md` §9.3) — **recomendada** — frente a constantes.
- **DA8.** Incluir la herramienta de comprobación — **recomendada**: es la
  prueba objetiva de «el parte genera su asiento» para Juan y el humano.

## 9. Fase RED exigible (traza en `progress/impl_F-031.md`)

En rojo contra el código de hoy, antes de implementar: **R2** (elige el no
Imputado aunque haya uno más reciente Imputado), **R3** (todo Imputado ⇒
`existe=False` + `complementario`), **R4** (ningún INSERT/DELETE con un
`hmoide` Imputado), **R5** (aviso de Cerrado), **R8** (choque ⇒ `omitir`
con `parte_contabilizado`), **R9** (pisar no borra en Imputado), **R13**
(campos en el JSON), **R15** (sv4 pinta `p.aviso`), **R22** (`comparar`).
Caracterización en verde antes de tocar nada: **R6**, **R10**, **R18**,
**R19**.

## 10. Verificaciones manuales (humano)

- **M0 (antes de implementar).** Juan Romero valida DA1, DA2, DA5 y DA6; el
  humano aprueba DA1–DA8. Preguntas listas en `progress/spec_F-031.md`.
- **M1 (solo lectura, ya ejecutable tras T-herramienta).**
  `cd services/partes-transfer && ../../.venv/Scripts/python.exe comprobar_asiento_analitico.py --empresa 1 --obra 0696 --ano 2026 --mes 1`
  → PT26/00004 Imputado, asiento ANA26/00017, `cuadra` (dato §D3).
- **M2 (solo lectura).** Mismo comando con `--obra 0404 --ano 2026 --mes 7`
  → PT26/00296 en registro, 0 líneas, sin asiento.
- **M3 (producción, sin escribir).** Tras desplegar, abrir el modal de
  aprobación de una obra con líneas de agosto de 2026 y **cancelar**: el
  parte sale con el aviso de Cerrado (el preflight no escribe).
- **M4 (cuando Administración contabilice el primer parte con líneas de
  sv5).** M1 sobre esa obra y mes: `cuadra` y «nuestras» > 0.

## 11. Orden de despliegue

`redeploy_partes.ps1 -Solo sv5` y después `-Solo sv4` (orden seguro
sv2→sv3→sv5→sv4→sv1). Campos nuevos aditivos: un sv4 viejo los ignora y un
sv5 viejo no los manda (R16). Sin variables nuevas en Azure (defectos 10/3).
Rollback: imagen anterior de sv5. Lo despliega el humano.

## 12. Ficheros que NO se tocan y fuera de alcance

- No se tocan: `cuenta_analitica.py`, `reglas_registro.py`,
  `coherencia_recurso.py`, `comprobacion_lineas.py`, `resultado_json.py`,
  `interface_adapters/api/app.py`, `transfer_consumer.py`,
  `prueba_escritura_sigrid.py`, sv1–sv3, `orm_models.py`, `infra/`.
- Fuera: escribir asientos/apuntes o cambiar estados (DA4); contrapartida
  (DA3); los 31 asientos que ya no cuadran (§D3: se informa a Juan);
  regenerar asientos; analítica de la empresa 28 (no la usa); el
  apunte financiero (nóminas, facturas) del correo de Juan.

## 13. Riesgos

- **Carrera con Administración** (contabiliza entre la lectura del estado y
  el INSERT, segundos bajo lock): aceptado; M1 lo detectaría (`descuadre`).
- **Complementarios en masa** si se contabiliza antes de aprobar: DA1.
- **Parte↔asiento sin clave** (resumen y fecha, 497/497): si se edita el
  resumen, la herramienta dice `sin_asiento`, nunca un falso `cuadra`.
