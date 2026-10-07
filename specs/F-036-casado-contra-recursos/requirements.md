<!-- specs/F-036-casado-contra-recursos/requirements.md -->
# F-036 · sv3: casar el trabajador leído contra los recursos persona de la empresa del parte — Requisitos

**Servicios tocados: sv3** (el casado, el maestro de recursos y una herramienta
de solo lectura) **y sv5** (una condición en el SQL de `recursos_por_dni`, por
la lista cerrada). **sv4 no cambia** (F-035 lleva sus selectores en paralelo),
tampoco sv1/sv2 ni el schema. Rigor **crítico**. Petición del humano del
2026-10-07: «que case contra la lista de recursos de la empresa, que viene de
pasos anteriores»; «si no hay dni en el recurso que lo traiga de empleado».

## Contexto

sv2 no recibe lista de personas. sv3 casa (DNI → alias → nombre) contra
**fichas `emp`** de alta de la empresa del parte, con el respaldo F-030 para
quien no tiene `emp`, y el conciliador elige después el recurso. Con ficha en
Ruesma y recurso en Porsan, hoy queda `dni_otra_empresa` en un parte de
Porsan. Aquí el casado elige **recurso**, de la lista que ya carga
`SigridMatcherProvider` (sin lecturas nuevas salvo una columna).

## Glosario

- **Recurso persona**: fila de `res` con `res.cla = 1` (criterio de
  `porcentajes`; 0 consumo, 2 medio). Columna «Clase» de `res`.
- **Ficha enlazada**: la `emp` con `emp.ide = res.conide` presente en el maestro.
- **DNI del recurso** (DA1): `emp.dni` de la ficha enlazada si no está vacío;
  si no, `res.cif`; normalizado como hoy (`normalize_dni`).
- **Recursos de un DNI**: los recursos persona con `res.cif` = ese DNI o
  enlazados a una ficha con ese DNI (lo que ya hace `_recursos_de`).
- **Candidato**: recurso persona de alta a la fecha del parte (`de_alta` sobre
  el `con.fecbaj` del recurso), de la empresa del parte (sin empresa, de
  cualquiera) y con DNI del recurso.

## Requisitos

### Maestro

- **R1.** sv3 debe leer `res.cla` en `_SQL_RECURSOS` y llevarlo en
  `RecursoRow.cla` (NULL ⇒ `None`).
- **R2.** Solo un recurso con `cla = 1` es de persona: ningún paso de sv3
  (casado, `elegir_recurso`, `empresas_con_recurso`) debe proponer otro. La
  búsqueda por ide (`recurso()`, `recursos`) sigue viendo todos.
- **R3.** Un recurso persona sin DNI del recurso no es candidato por nombre;
  el proveedor registra un INFO con cuántos hay.

### Casado por DNI

- **R4.** CUANDO la línea trae DNI leído, sv3 debe elegir entre los recursos de
  ese DNI que estén de alta a la fecha del parte y en la empresa del parte, con
  el desempate de hoy (`_desempatar`): uno solo; si no, el `emp.reside` de la
  ficha del DNI de alta en esa empresa (`elegir_ficha` ok); si no, el único
  enlazado a esa ficha.
- **R5.** SI el DNI tiene recursos persona pero ninguno candidato o varios sin
  desempate, ENTONCES la línea queda sin casar con `dni_ambiguo`,
  `dni_solo_baja` o `dni_otra_empresa`, sin seguir al alias ni al nombre.
- **R6.** SI no hay DNI leído o no tiene ningún recurso persona, ENTONCES sv3
  sigue al alias y después al nombre.
- **R7.** Una persona con ficha en una empresa A y recurso persona sin enlazar
  (`res.cif` = DNI) en otra B debe casar por ese recurso en un parte de B.

### Alias

- **R8.** CUANDO existe alias para el nombre leído, sv3 debe tomar su DNI
  (`empleado_alias.empleado_dni`; vacío ⇒ el de la ficha `empleado_ide` del
  alias en el maestro) y resolverlo con R4–R5. Sin DNI, o con uno sin recursos
  persona, `alias_no_valido`.
- **R9.** La tabla `empleado_alias` y su escritura desde sv4 no cambian.

### Casado por nombre

- **R10.** CUANDO no casa por DNI ni alias, sv3 debe puntuar cada candidato con
  la similitud de hoy (`name_similarity`) como el **máximo** entre el nombre
  del recurso (`con.res`) y el de su ficha enlazada, con el umbral de hoy.
- **R11.** La persona (DNI del recurso) de mayor puntuación gana; SI otra
  persona empata o la supera, ENTONCES `nombre_ambiguo`. Varios recursos de la
  misma persona no son ambigüedad: el recurso se elige con R4 sobre su DNI y,
  si R4 no da uno, `nombre_ambiguo`.
- **R12.** SI ningún candidato llega al umbral, ENTONCES la línea queda sin
  casar (`none`), como hoy.

### Lo que se guarda en la línea

- **R13.** CUANDO el recurso elegido tiene ficha enlazada, la línea debe quedar
  con `empleado_ide`, `empleado_codigo` y `empleado_nombre` de la ficha,
  `empleado_dni` = DNI del recurso, `empleado_reside` = `res.ide` elegido y
  método `dni`, `alias` o `nombre`.
- **R14.** CUANDO no la tiene, `empleado_ide` NULL, `empleado_codigo` y
  `empleado_nombre` del recurso (`con.cod`, `con.res`), `empleado_dni` = DNI
  del recurso, `empleado_reside` = `res.ide` y método `recurso_dni`, o
  `recurso_nombre` si casó por nombre o por alias (los dos ya están en
  `METODOS_RECURSO` de sv3 y sv4: el portal lo da por casado sin cambios).
- **R15.** Para toda línea casada con obra de la empresa del parte, la pasada
  siguiente del conciliador (`elegir_recurso` con los `empleado_*` guardados)
  debe devolver el mismo `res.ide` que eligió el casado.
- **R16.** `recurso_ide`, `recurso_cif`, `hmo_ide` y `parte_estado` los sigue
  escribiendo solo el conciliador, como hoy.

### Retirada del respaldo F-030

- **R17.** `fichas_de_recurso.py` y `Matchers.recursos` desaparecen (lo
  subsume R4–R14); ningún código ni test los importa.

### Lista cerrada, congelación y sv5

- **R18.** sv5 `recursos_por_dni` debe considerar solo recursos con
  `res.cla = 1` en sus dos ramas (DNI de ficha y `res.cif`), para que los
  candidatos de `elegir_por_dni` sigan siendo los de `elegir_recurso` (DA3).
- **R19.** El guardián `tests/test_f036_recurso_persona_gemelos.py` debe fallar
  si sv3 deja de filtrar por `CLA_PERSONA = 1` o deja de leer `res.cla`, o si
  alguna rama de `recursos_por_dni` pierde `res.cla = 1`.
- **R20.** `de_alta`, `esta_congelado`, `ESTADOS_CONGELADOS`, `congelacion.py`
  (sv4), `verificar_recurso`, `elegir_por_dni` y `datos_recursos` no cambian;
  `tests/test_f023_de_alta_gemelos.py` y `tests/test_f024_borrado_no_congela_gemelos.py`
  siguen en verde sin tocarlos.
- **R21.** Una línea congelada sigue sin re-resolver su recurso (F-023 R30).

### Despliegue y medición del impacto

- **R22.** sv3 no re-casa líneas ya ingeridas (DA2): tras desplegar, el casado
  nuevo solo se aplica a partes nuevos; las líneas activas no congeladas solo
  ven el filtro R2 en la pasada del conciliador.
- **R23.** La herramienta `services/partes-persistencia/medir_casado_recursos.py`
  debe ser de solo lectura: SELECT en la base `partes` y `/api/sql/read` en
  sigrid-api; ninguna escritura en ningún sistema.
- **R24.** Debe informar, por empresa: recursos persona de alta hoy, de ellos
  sin DNI, con DNI solo por ficha, con `res.cif` y DNI de ficha distintos
  (DA1), y recursos `MO/` de alta que no son persona (lo que F-030 casaba y
  R2 deja fuera).
- **R25.** Para las líneas activas no congeladas: recurso guardado frente al
  que dará el conciliador con R2 (igual / cambia / lo pierde / lo gana).
- **R26.** Para esas mismas líneas, el casado de hoy frente al que daría R4–R14
  con lo leído (igual / otra persona / casado nuevo / pierde el casado), solo
  informativo (DA2). Las congeladas se cuentan aparte.
- **R27.** El informe no lleva nombres ni DNIs: recuentos, empresa,
  `registro_id` y `document_id`; Markdown + CSV (UTF-8 BOM, `;`) en
  `services/partes-persistencia/logs/` (ignorada por git).
- **R28.** El cálculo de R24–R26 es una función pura, sin red ni base,
  probada con datos sintéticos.

### Documentación

- **R29.** `docs/ARCHITECTURE.md` (semánticas 2 y 12), `docs/referencia/partes-proyecto.md`,
  `azure-apps/partes.md` (Empleado y Recurso) y la lista cerrada de `CLAUDE.md`
  (DA3) deben describir el casado contra recursos persona y la retirada de F-030.

**Fuera de alcance**: sv4 (F-035), re-casar lo ingerido, casar recursos sin
DNI por `reside`, la verificación de sv5 y la escritura en Sigrid.

**Trazabilidad**: cada R tiene ≥ 1 test `test_f036_rN_...` (design §7); R20 y
R21 son de caracterización; R29 lo revisa el reviewer contra design §6.
