<!-- progress/review_F-012.md -->
# Review · F-012 · Estudio: candef de 9 h, viernes y jornada semanal particularizable

> **VEREDICTO FINAL: APPROVED** (segunda pasada, al final de este documento).
> Lo que sigue es la PRIMERA pasada, que rechazó la spec; se conserva entera
> porque es el registro de qué se pidió corregir y por qué.

## Primera pasada · 2026-08-18

- **Veredicto: CHANGES_REQUESTED**
- Fecha: 2026-08-18 · Rama revisada: `feature/F-004-congelar-aprobados` (HEAD `6a29e77`)
- Entregable revisado: `specs/F-012-estudio-jornada-semanal/{requirements,design,tasks}.md`
  (commits `f83cde8`, `c13b524`), alta de backlog (`093ee41`, `765cab8`) y
  `progress/current.md`.
- No hay `progress/impl_F-012.md` y **no se echa en falta**: F-012 es un ESTUDIO
  sin código cuyo entregable es la propia spec. Se ha validado el estudio en sí,
  reproduciendo sus datos contra Sigrid en solo lectura.

## Resumen en dos líneas

El estudio es sólido: **todas las cifras que sostienen la propuesta se han
reproducido contra Sigrid y salen exactas**. Se rechaza el cierre por dos
defectos concretos y baratos de arreglar: (1) el bloque B —el que F-015 hereda
«tal cual»— **contradice una decisión firme del humano** (candef fuera del mapa);
(2) `tasks.md` deja sin marcar tareas que están hechas, de modo que la spec no
refleja su propio estado (C5 vacío).

## Nivel de rigor

- Declarado en `harness/features.json`: **`documental`**. Valor válido.
- Lo que exige (`harness/rigor.json` + `CHECKPOINTS.md`): C1–C3, C3 bis y C5.
  `fase_red: false`, `cobertura: false`, `mutacion: false`. Una feature
  documental no puede requerir mutation testing.
- Lo que NO relaja: la coherencia interna del documento, el barrido de datos
  sensibles y el cierre de la sesión.

## Verificación independiente de los datos (R1, R2)

Reproducidas por el reviewer el 2026-08-18 vía `sigrid-api`
`POST /api/sql/read`, base `ruesma`, **solo lectura**, con las credenciales de
`services/partes-front/.env` (no se copian aquí). Script de usar y tirar fuera
del repositorio.

| Hallazgo | Afirma la spec | Medido por el reviewer | ¿Cuadra? |
|---|---|---|---|
| H1 · candef=1.0 | 561 recursos | 561 | exacto |
| H1 · candef=0.0 | 199 | 199 | exacto |
| H1 · candef=8.0 | 106 | 106 | exacto |
| H1 · **candef=9.0** | **1** | **1** | exacto |
| H1 · «otros >2: 0» | ningún 7/10/35/40 | la consulta devuelve 4 valores distintos y ninguno más | exacto |
| H2 · quién es | `MO/0037`, sin DNI en `emp`, con código HE | `MO/0037`, `tiene_dni='sin'`, `n_he=1` | exacto |
| H3 · viernes con ordinarias (candef 8) | 3.498 | 3.498 | exacto |
| H3 · neto de extras en viernes | −1.101 h | −1.100,5 h | exacto |
| H3 · «ningún viernes de 4 h» | n=0 de 3.498 | 0 filas | exacto |
| H3 · «ni de 9 h» | n=1 | 1 fila, (9, −2) | exacto |
| H4 · 8→40 h | 2.351 semanas / 81 recursos | 2.351 / 81 | exacto |
| H4 · 8→35 h | 362 / 69 | 362 / 69 | exacto |
| H4 · 8→48 h | 222 / 9 | 222 / 9 | exacto |
| H4 · 8→42 h | 46 / 7 | 46 / 7 | exacto |
| H4 · 8→41 h | 4 / 4 | 4 / 4 | exacto |
| H4 · 9→35 h | 4 / 1 | 4 / 1 | exacto |
| H5 · grupo >40 h | **7 recursos**: `MO/0006`, `MO/0007`, `MO/0008`, `MO/0031`, `MO/0366`, `MO/0405`, `MO/0456`, todos candef 8 | exactamente esos 7, todos `candef=8.0`, con 15–54 semanas por encima de 40 h | exacto |

**Conclusión: la base empírica del estudio es real y reproducible.** Las dos
cifras clave que pedía la revisión (candef=9 → 1 recurso; los 7 recursos
`MO/0006…` con semanas >40 h) salen idénticas. Esto no es lo que se rechaza.

Dos observaciones menores sobre los datos, sin efecto en ninguna conclusión:

- **H3, frecuencias por par**: los totales y las cuatro afirmaciones que el
  estudio saca de la tabla reproducen exactos, pero las frecuencias fila a fila
  salen algo por debajo de lo publicado: (8, 0) 803 vs 836; (8, −2) 764 vs 810;
  (8, +1) 648 vs 678; (8, −3) 326 vs 328; (7, 0) 241 vs 247; (8, +2) 230 vs 234;
  (8, −1) 154 vs 157. Mismo total (3.498) y mismo orden. Compatible con ediciones
  de Administración sobre partes del mes en curso entre ambas medidas; se anota
  para que nadie tome esas siete cifras como exactas.
- **H4 omite las filas de candef 0 y 1**: existen 91 semanas de 40 h en 3
  recursos con candef 0, 10 de 35 h en 2, y 10 de 40 h en 2 recursos con
  candef 1. La tabla se presenta como «semanas completas» sin decir que filtra a
  candef 8/9. No cambia la conclusión (esos recursos caen al fallback de 8 h).

## Checkpoints

### C1 — El arnés está completo y en verde — **[x]**

- [x] `bash harness/init.sh` termina en exit code 0 (`ENTORNO LISTO`). Ejecutado
      tal cual, sin pipes ni decoración.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
      `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
      `docs/CONVENTIONS.md`.
- Avisos no bloqueantes conocidos: ruff (450, deuda previa), sv1/sv2/infra sin
      directorio de tests.

### C2 — El estado es coherente — **[x] con dos salvedades escritas**

- [x] UNA sola feature `in_progress` (`F-012`); init.sh lo confirma.
- **N/A justificado** · «la rama actual es `feature/F-XXX-slug`»: F-012 es un
      estudio **sin código** y por decisión del líder no tiene rama propia; sus
      cinco commits (`f83cde8`, `c13b524`, `765cab8`, `093ee41`, `6a29e77`)
      viven en `feature/F-004-congelar-aprobados`, que es la rama activa y NO es
      `main`. El espíritu del checkpoint (no commitear a `main`/`dev`) se
      respeta. **Nit**: `features.json` declara para F-012 la rama
      `feature/F-012-estudio-jornada-semanal`, que **no existe** (`git branch -a`).
      O se crea, o el campo debe reflejar dónde vive de verdad el trabajo.
- [x] `progress/current.md` describe la sesión activa (F-012) más notas de
      contexto etiquetadas como tales.
- [x] Toda feature `done` tiene resumen en `progress/history.md` (F-003, F-004,
      F-013 comprobados).
- **Nit de coherencia**: `current.md` dice «F-011 REPRIORIZADA A BAJA (prio 12)»
      y `features.json` le da `priority: 14`.

### C3 — El código respeta arquitectura y convenciones — **N/A justificado**

F-012 no crea ni modifica **ningún** fichero fuera de
`specs/F-012-estudio-jornada-semanal/` (verificado con `git show --stat` sobre
los cinco commits: solo `specs/`, `harness/features.json` y `progress/`). No hay
código que evaluar: ni arquitectura hexagonal, ni cabecera de ruta, ni imports,
ni dependencias nuevas. Las tres trampas del monorepo se han comprobado a nivel
de **propuesta** y están bien tratadas (empleado ≠ recurso: §H2 y R22 arrastran
DNI y recurso; schema duplicado: R18 y §7 exigen las DOS copias de
`orm_models.py`, con F-010 como prerrequisito).

### C3 bis — Documentos de fuera — **N/A justificado**

La feature no añade ni modifica nada en `docs/referencia/`, ni entra ningún PDF
u ofimática al árbol. Aun así se ejecutó el **barrido de datos sensibles** sobre
los tres ficheros de la spec, porque R7 lo exige:

| patrón | resultado |
|---|---|
| `[0-9]{8}[A-Z]` (DNIs) | **0 coincidencias** |
| `https?://\|api[_-]?key\|apikey\|x-api-key\|password\|passwd\|token\|secret\|Bearer\|\.azurecontainerapps\|@ruesma\.es` | 2 coincidencias, ambas **falsos positivos**: la palabra «secreta/secreto» en prosa (`design.md:407` «variable NO secreta», `design.md:483` «no es secreto») |
| `\b([0-9]{1,3}\.){3}[0-9]{1,3}\b` (IPs) | **0 coincidencias** |

Los recursos se citan siempre por código `MO/NNNN`; el único `res.ide` que
aparece (2798044, `design.md:114`) está expresamente permitido por R7. Ni URL ni
clave de sigrid-api en la spec. **R7 se cumple.**

### C4 — La verificación es real — **[ ]**

- **N/A justificado** · «cada requisito tiene ≥ 1 test `test_fXXX_rN_*`»: F-012
      es un estudio; sus requisitos del bloque A se verifican leyendo el
      documento y reproduciendo sus datos, no con pytest. El bloque B es
      normativo **para F-015** y allí sí traerá tests (ya nombrados requisito a
      requisito, lo cual es buena práctica).
- [x] Los unit tests existentes no se tocan y siguen en verde (6 en raíz, más
      sv3/sv4/sv5 por caché de árbol sin cambios).
- [x] Los MANUAL del humano están listados en `progress/current.md` (petición a
      RRHH de F-014, con la lista de los 8 recursos).
- **[ ] R6 NO se cumple** (ver hallazgo 1): el requisito pide «registrar las
      decisiones ya tomadas por el humano con su fecha, dejar numeradas **SOLO
      las que sigan abiertas**». Las tres de §9.2 (D-A1, D-A2, D-A3) ya fueron
      decididas por el humano el 2026-08-18 y siguen figurando como abiertas; en
      D-A2, además, la recomendación escrita es **la contraria** a lo decidido.

Trazabilidad requisito → evidencia (bloque A):

| Req | Dónde se cumple | Evidencia del reviewer | Estado |
|---|---|---|---|
| R1 · candef con datos reales | `design.md` §3 H1–H2 + anexo A | reproducido: 561/199/106/**1**; `MO/0037` sin DNI, con HE | **[x]** |
| R2 · histórico de viernes y semanas | §3 H3–H6 | reproducido: 3.498 viernes, neto −1.100,5 h, 0 viernes de 4 h; H4 y H5 exactos | **[x]** |
| R3 · inventario de fuentes | §5 (6 fuentes con «¿datos hoy?», mantenedor y decisión) | completo y con decisión marcada | **[x]** |
| R4 · regla y casos límite | §4 tabla A–R | cubre festivo en V (B), X (C), J+V (D), solo lunes (E), semana entera festiva (F), semana partida (G), incompleta (H), ausencia (I), sábado (J), sin HE (O), candef inválido (P), fuera del mapa (M) | **[x]** salvo que el caso M codifica la opción descartada |
| R5 · servicios y ficheros | §1, §7, §8 | LÍMITE DE SERVICIO argumentado; tablas crear/modificar/NO tocar | **[x]** |
| R6 · decisiones tomadas vs abiertas | §9.1 / §9.2 + `tasks.md` | §9.2 lista como abiertas tres decisiones ya cerradas; D-A2 recomienda lo contrario a lo decidido | **[ ]** |
| R7 · sin datos personales ni claves | los tres ficheros | barrido de C3 bis: limpio | **[x]** |

### C4 bis — El rigor declarado se cumple — **[x]**

- [x] La feature declara `rigor: "documental"` en `harness/features.json`, valor
      válido; init.sh lo valida.
- **N/A justificado** · **fase RED**: `harness/rigor.json` fija
      `documental.fase_red = false`. No hay código de producción ni test cuyo
      fallo previo pudiera enseñarse: el entregable es un documento. No es una
      herramienta que se haya omitido, es una puerta que el nivel no exige.
- **N/A justificado** · **cobertura**: `documental.cobertura = false`. A mayor
      abundamiento, la puerta salió `[OK] 96.7% de 1067 líneas cambiadas`, pero
      esas líneas son de F-003/F-004, no de F-012, que no cambia ni una.
- **N/A justificado** · **mutación**: `documental.mutacion = false`. No existe
      `progress/mutacion_F-012.md` ni debe existir: no hay ni una línea de
      Python en el diff de la feature que mutar. No procede la prueba de control
      de «cero mutantes», porque no hay campaña que verificar.
- **N/A justificado** · sección **«Evidencias»** del implementer: no hay
      implementer en una feature cuyo entregable es la spec. Su papel lo cumple
      esta sección «Verificación independiente de los datos», donde el reviewer
      ha reproducido las cifras contra la fuente en lugar de creérselas.
- [x] Ningún punto de este bloque queda N/A sin motivo escrito.

### C4 ter — Rutas sensibles — **N/A, sin nada que justificar**

`harness/rutas_sensibles.json` no existe en el repositorio (solo el
`.ejemplo.json`). Sin declaración, el bloque es N/A por configuración.

### C5 — La sesión se cerró bien — **[ ]**

- **[ ]** `tasks.md` **no** tiene todas las tareas `[x]`: T2, T3, T4, T5 y T6
      siguen en `[ ]` cuando al menos T4 y T6 están hechas y T2/T3 las cerró el
      humano el 2026-08-18 (ver hallazgo 2).
- [x] Sin ficheros temporales ni artefactos sin trackear (`git status` limpio;
      el script de verificación del reviewer vive en el scratchpad, fuera del
      repositorio).
- [x] `features.json` refleja el estado real de la feature (`in_progress`,
      `sdd: true`, `rigor: documental`, `priority: 4`), salvo el campo `branch`
      apuntando a una rama inexistente (nit de C2).
- **Observación, no bloqueante**: no hay commits con el formato `F-012 Tn: ...`;
      los cinco son `F-012: <descripción>`. En un estudio cuyas tareas son de
      validación y cierre no tiene mucho sentido un commit por tarea, y así se
      acepta, pero conviene que `tasks.md` diga qué commit cierra cada tarea.

## Lo que se ha verificado de la propuesta (§6, R10–R25) contra las decisiones firmes

| Decisión firme del humano (765cab8 + `current.md`) | ¿La spec la refleja? |
|---|---|
| Jornada semanal DERIVADA del candef, mapa `{8:40, 9:42}` configurable | **Sí** — §9.1 D1, R10, §6.1 paso 3, settings en §7 |
| Env espejo en sv3 y sv4 | **Sí en sustancia** (§1, §7, §9.2 D-A1(a)), pero la decisión sigue etiquetada «abierta» |
| Resto en el ÚLTIMO DÍA LABORABLE, festivo contando como jornada | **Sí** — §4 regla y casos B–E, R13, §6.1 paso 4; §10.2 descarta explícitamente la lectura alternativa |
| Excepciones en tabla `empleado_jornada` (UI en F-016) | **Sí** — §5, §6.1 paso 2, §8 (schema completo con vigencia, `origen` y auditoría), R16–R18, R27 |
| **Candef desconocido → jornada plana 5×candef + WARNING** | **NO** — la spec dice S = 40 en R10, R13, §4 caso M y §6.1, y §9.2 D-A2 recomienda esa opción (a) frente a la (b) que es la decidida |
| Sin calendario → viernes | **Sí en sustancia** (§6.3 último punto, §9.2 D-A3), pero sigue etiquetada «abierta» |
| F-010 antes de F-015 | **Sí** — §9.1 D6, §1, y en el orden de prioridades (F-010 prio 6 < F-015 prio 7) |
| F-014 prerrequisito | **Sí** — §1, §9.1 D3/D4, §10.6, y en `features.json` (F-014 prio 5, descripción de F-015) |

Coherencia del backlog (T4), comprobada en `harness/features.json`:

- **F-015** de alta: `sdd: true`, `rigor: estandar`, `priority: 7`, con los
  prerrequisitos F-014 y F-010 escritos en la descripción. Correcto.
- **F-016** de alta: `sdd: true`, `rigor: estandar`, `priority: 8`, «después de
  F-015». Correcto.
- **F-011** anotada con la NOTA F-012 (`empleado_jornada` + `emphis.porjorlab`
  como fuente candidata, no los contratos de Sesame). Correcto.
- **F-014** ya estaba de alta (`093ee41`), `sdd: false`, `rigor: documental`,
  `priority: 5`, con los 8 recursos y el SQL de verificación en `acceptance`.
- El orden por prioridad resultante (F-014 → F-010 → F-015 → F-016) respeta D6 y
  el riesgo §10.6.
- **T5 queda correctamente como MANUAL del humano** y está listada en
  `progress/current.md` con los recursos concretos.

## Cambios requeridos

1. **BLOQUEANTE · El bloque B contradice la decisión firme del humano sobre el
   candef fuera del mapa.** El humano decidió el 2026-08-18 «candef desconocido
   → **jornada plana 5×candef** + WARNING» (registrado por el líder en
   `harness/features.json`, descripción de F-012 y de F-015, y en
   `progress/current.md:15`). La spec dice lo contrario en cuatro sitios, y es
   justo el bloque que F-015 hereda «tal cual» (`requirements.md:9`):
   - `requirements.md:83-90` (**R10**): «SI el candef efectivo no está en el
     mapa, ENTONCES S = `JORNADA_SEMANAL_POR_DEFECTO` (40.0)». Con la decisión
     debe ser S = 5 × candef efectivo, y `JORNADA_SEMANAL_POR_DEFECTO` cambia de
     sentido o desaparece.
   - `requirements.md:113-117` (**R13**, lista de casos del test): «Candef 10,
     S 40 (fuera del mapa) → último 0». Con la decisión, candef 10 → S 50 →
     último laborable 10 (jornada plana, comportamiento actual).
   - `design.md:270` (**caso M** de la tabla §4): «V jornada max(0, 40−40)=0 →
     8 extra». Ese resultado —8 h de extra automática un viernes normal— es
     exactamente lo que la decisión del humano evita.
   - `design.md:309` (**§6.1 paso 3**): `S = mapa.get(c, S_defecto)` debe pasar a
     `mapa.get(c, 5 * c)` con WARNING.
   Ninguno de los cuatro menciona el WARNING como obligatorio (hoy es la opción
   (c) «recomendada» de D-A2, no un requisito EARS).
2. **BLOQUEANTE · §9.2 mantiene como «abiertas» tres decisiones ya cerradas, y en
   una de ellas recomienda lo contrario a lo decidido** (`design.md:479-501`).
   Incumple R6 («dejar numeradas SOLO las que sigan abiertas»). Mover D-A1
   (mapa en env espejo sv3+sv4), D-A2 (5×candef + WARNING) y D-A3 (sin
   calendario → viernes) a §9.1 con su fecha (2026-08-18), y dejar §9.2 vacía o
   suprimida. Actualizar en consecuencia `tasks.md:29-34` (**T3**), que hoy
   describe D-A2 como «S=40 + WARNING recomendado».
3. **BLOQUEANTE · `tasks.md` no refleja su propio estado (C5).** Marcar `[x]` y
   anotar la evidencia:
   - **T4** (backlog): hecha por el líder en `093ee41` (F-014) y `765cab8`
     (F-015, F-016, nota en F-011); verificada por este reviewer contra
     `features.json`. Sigue en `[ ]` (`tasks.md:36`).
   - **T6** (`init.sh` en verde): ejecutado hoy con exit code 0. Sigue en `[ ]`
     (`tasks.md:54`).
   - **T2** y **T3** (MANUAL del humano): el humano aprobó la spec y dejó sus
     decisiones escritas el 2026-08-18 (`765cab8`, `current.md:12-17`). O se
     marcan `[x]` citando esa evidencia, o se dice por escrito qué falta.
   - **T5** es la única que debe quedar pendiente: es MANUAL del humano y
     pertenece de hecho a F-014. Déjese `[ ]` con la nota de que no bloquea el
     cierre de F-012 pero sí el merge de F-015.
4. **MENOR · El anexo A no es reproducible tal cual**, y R1/R2 lo venden como
   «SQL reproducible». El bloque de H4/H5 (`design.md:590-606`) **no ejecuta**:
   empieza por una coma (`, s AS (`) sin las CTE `d`/`d2` delante y contiene
   puntos suspensivos literales dentro del `GROUP BY`
   (`DATEPART(isowk, ...), YEAR(...)`). El patrón por mes de H5
   (`design.md:608-609`) es prosa, no SQL. Este reviewer tuvo que reconstruir la
   consulta para verificar —y al reconstruirla los números salieron exactos—,
   pero quien la reproduzca mañana no debería tener que adivinarla. Pegar los
   dos bloques completos y ejecutables.
5. **MENOR · H3, frecuencias por par**: añadir la fecha/hora de la medición y una
   nota de que las frecuencias fila a fila se mueven con las ediciones de
   Administración (el reviewer midió 803/764/648/326/241/230/154 frente a las
   836/810/678/328/247/234/157 publicadas, con total idéntico de 3.498 y las
   mismas conclusiones). Alternativamente, refrescar la tabla.
6. **MENOR · H4** (`design.md:150-165`): decir explícitamente que la tabla filtra
   a candef 8 y 9. Existen además 91 semanas de 40 h en 3 recursos con candef 0
   y 10 en 2 recursos con candef 1, hoy invisibles en la tabla.
7. **MENOR · Coherencia de estado**: `features.json` declara para F-012 la rama
   `feature/F-012-estudio-jornada-semanal`, que no existe; y `current.md:44`
   dice que F-011 quedó en prioridad 12 mientras `features.json` le da 14.

Los puntos 1 a 3 son los que impiden el cierre. Los puntos 4 a 7 se pueden
arreglar en la misma pasada; ninguno afecta a las conclusiones del estudio.

## Lo que este reviewer quiere dejar dicho a favor del estudio

No es un documento de trámite. Reproduje cinco consultas contra Sigrid esperando
encontrar cifras redondeadas o inventadas y salieron **exactas hasta la última
unidad**, incluida la lista nominal de los siete recursos de la cuadrilla. El §4
razona los casos límite de verdad (el «solo lunes laborable» del caso E es una
consecuencia incómoda de la lectura A y está escrita, no escondida), el §10
descarta alternativas con motivos y el §5 admite sin adornos que las fuentes
ideales de Sigrid están vacías. La corrección que se pide es de coherencia con
una decisión posterior a la redacción, no de fondo.

## Automejora del arnés (propuesta, no aplicada)

Lo que este caso destapa: **cuando el humano aprueba una spec con decisiones que
cambian su contenido, hoy esas decisiones se escriben en `features.json` y en
`progress/current.md`, pero nadie obliga a devolverlas a la spec.** El resultado
es una spec aprobada que contradice a su propia aprobación, y una feature de
implementación (F-015) que hereda requisitos EARS equivocados. Ha pasado aquí con
D-A2 y ha estado a punto de pasar con D-A1 y D-A3.

Propuesta para el humano, a aplicar en este repositorio **y a portar a
`arnes-base`** (regla de propagación):

1. En `.claude/agents/leader.md`: cuando el humano apruebe una spec **con
   condiciones o decisiones**, el líder no pasa la feature a `in_progress` sin
   antes reflejar esas decisiones **en la spec** (requisitos y diseño), no solo
   en `features.json`/`current.md`. Un commit `F-XXX: spec actualizada con las
   decisiones de la aprobación`.
2. En `CHECKPOINTS.md`, C2 o C5: nuevo checkbox — «Las decisiones registradas en
   `features.json`/`progress/current.md` como tomadas por el humano **no
   contradicen** la spec aprobada; ninguna decisión cerrada figura como abierta
   en la sección de decisiones de `design.md`». Es barato de comprobar y es justo
   lo que aquí falló.
3. En `.claude/agents/reviewer.md`, sección de features documentales: dejar
   escrito que en un estudio **el reviewer reproduce al menos dos de las cifras
   que sostienen la propuesta contra la fuente real**, en solo lectura, y las
   pega en el informe. Es el equivalente documental de la verificación
   independiente de la campaña de mutación que ya exige C4 bis: sin ella, un
   estudio con números inventados pasa el filtro sin despeinarse.

---

# Segunda pasada · 2026-08-18

- **Veredicto final: APPROVED**
- Rama: `feature/F-012-estudio-jornada-semanal` (creada desde `dev` `9247c16`),
  HEAD `80aefc5`. Commits revisados: `37b50af` (corrección del spec-author),
  `80aefc5` (errata del caso M), `c31b24a` (punto 7, hecho por el líder).
- `git diff dev...HEAD` toca **solo** `specs/F-012-estudio-jornada-semanal/`
  (los tres ficheros), `progress/current.md` y `progress/review_F-012.md`.
  Sigue sin haber una línea de código: el estudio no cambia el producto.
- `bash harness/init.sh`: **exit code 0**, `ENTORNO LISTO`. Además la puerta de
  cobertura ahora imprime el motivo correcto por sí sola:
  `PUERTA COBERTURA: N/A (F-012 es de nivel documental: no exige cobertura)`,
  en vez del 96,7 % heredado de F-004 que confundía en la primera pasada.
- `git status` limpio. Rama activa = rama declarada en `features.json`.

## Punto por punto

### 1 · Bloque B con 5×candef + WARNING como requisito EARS — **RESUELTO**

- `requirements.md` **R10** reescrito: «SI el candef efectivo es válido pero NO
  está en el mapa, ENTONCES S = 5 × candef efectivo (jornada plana:
  comportamiento actual) **y el sistema debe emitir un WARNING**» con el texto
  del mensaje y la cadencia (una vez por recurso y pasada/vista). El WARNING deja
  de ser una recomendación y pasa a ser obligación EARS, que era justo el punto.
  Añade la frase que cierra la puerta: «No existe una "jornada semanal por
  defecto" aparte del mapa».
- **R13** corregido: «Candef 10 (fuera del mapa) → S 50 → último laborable 10
  (jornada plana)». Aritmética comprobada: 50 − 4×10 = 10. El antiguo «Candef 10,
  S 40 → último 0» ha desaparecido. El caso «candef 9 con mapa `9:40` → último 4»
  sigue siendo correcto (40 − 36 = 4) y ahora explicita el mapa que lo produce.
- **§4 caso M** rehecho: `10 / 50 (5c)`, «igual que hoy: V jornada 10 → −2;
  **WARNING**». Ya no promete 8 h de extra automática un viernes normal.
- **§6.1 paso 3**: `S = mapa.get(c, 5 * c)`; si c no estaba en el mapa, WARNING.
- Consistencia de arrastre verificada por grep: **cero apariciones** de
  `JORNADA_SEMANAL_POR_DEFECTO`, `semanal_por_defecto`, `S_defecto` en los tres
  ficheros. El parámetro se ha retirado también de la firma de `jornada_dia`
  (§6.2) y de la tabla de settings de §7, y §1 y §10.8 se han alineado. La
  corrección es completa, no un parche en el requisito.

### 2 · §9.2 sin decisiones ya cerradas — **RESUELTO**

Las tres pasan a §9.1 como **D9** (mapa en variable de entorno espejo sv3+sv4),
**D10** (5×candef + WARNING obligatorio) y **D11** (sin calendario → viernes),
cada una fechada 2026-08-18 y con las alternativas descartadas y su motivo. §9.2
queda con una línea: «Ninguna: todas las decisiones del estudio están tomadas por
el humano». La cabecera del documento se ha actualizado en coherencia
(«decisiones tomadas por el humano —ninguna queda abierta—»). Las referencias
`D-A1/D-A2/D-A3` han desaparecido del árbol (grep sin resultados): §1, §6.3, §7,
§10.8 y `tasks.md` citan ya D9/D10/D11. **R6 se cumple.**

### 3 · `tasks.md` al día — **RESUELTO**

T1, T2, T3, T4 y T6 en `[x]`, cada una con la evidencia citada (commits `765cab8`
y `093ee41` para el backlog, la aprobación del humano para T2/T3, el exit code 0
para T6). T5 queda en `[ ]` y **bien encuadrada**: se dice por escrito que es
MANUAL del humano, que pertenece de hecho a F-014, que **no bloquea el cierre de
F-012** y que **sí bloquea el merge de F-015** (riesgo §10.6). Eso es exactamente
lo que pedía C4 sobre los MANUAL. **C5 satisfecho.**

### 4 · Anexo A ejecutable tal cual — **RESUELTO, y verificado a lo bruto**

No me he fiado de la lectura: extraje con un script los **10 bloques sql del
anexo tal como están en el fichero**, sin retocar un carácter, y los lancé contra
`sigrid-api` (`POST /api/sql/read`, base `ruesma`, solo lectura). Son 18
sentencias contando las del bloque H7.

**Resultado: 18 de 18 ejecutan sin un solo error.** Ya no hay fragmentos que
empiecen por coma ni puntos suspensivos literales en el `GROUP BY`; los bloques
de H4 y H5 traen su propia cabecera `WITH d AS (...), d2 AS (...)` completa. El
anexo ha crecido además con cuatro consultas que antes eran prosa (categoría/DNI
del grupo H5, patrón por mes y día de semana, líneas de `MO/0037`, intensiva de
H6), todas ejecutables.

Cifras que devuelve el anexo ejecutado literalmente, contrastadas con el texto:

| Afirmación | Anexo ejecutado tal cual | ¿Cuadra? |
|---|---|---|
| H4 · 8→40 h: 2.351 semanas / 81 recursos | 2.351 / 81 | exacto |
| H4 · 8→35 / 8→48 / 8→42 / 8→41 | 362/69 · 222/9 · 46/7 · 4/4 | exacto |
| H4 · nota nueva: candef 0 → 91 semanas de 40 h en 3 recursos | 91 / 3 | exacto |
| H4 · nota nueva: candef 1 → 10 semanas de 40 h en 2 recursos | 10 / 2 | exacto |
| H4 · nota nueva: candef 0 → 10 de 35 h, 1 de 38, 1 de 39 | 10 · 1 · 1 | exacto |
| H5 · «≥ 15 semanas por encima de 40 h: 7 recursos» | 7 recursos con 54, 49, 42, 40, 39, 33 y 15; **el octavo baja a 1** | exacto y con corte limpio |
| H5 · «todos OFIC. 1ª ALBAÑIL, con DNI en `emp`, con código HE, candef 8» | los 7: `restip` OFIC. 1ª ALBAÑIL, `tiene_dni='si'`, `n_he=1`, `candef=8.0` | exacto |
| H5 · los códigos | `MO/0366`, `MO/0405`, `MO/0456`, `MO/0006`, `MO/0007`, `MO/0008`, `MO/0031` — los siete de F-014, ni uno más | exacto |
| H5 · «extras registradas ≈ 0» en los regímenes 48 y 42 | `ext_media` −0,1 (48 h) y 0,5 (42 h) | lo sostiene |
| H2 · «su histórico registrado (29 líneas)» | 29 filas | exacto |

La consulta nueva que mapea `res.ide` → `con.cod` es la que cierra el círculo:
permite a cualquiera comprobar que los siete `ide` del anexo son los siete
códigos `MO/NNNN` que F-014 va a pedir a RRHH, sin que el repositorio tenga que
guardar un solo nombre ni un solo DNI.

### 5 · H3 con fecha de medición — **RESUELTO**

La tabla lleva ahora «Medición del 2026-08-18 (sesión de redacción, mañana)» y
una *Nota de reproducibilidad* que recoge las siete frecuencias que midió este
reviewer por la tarde (803/764/648/326/241/230/154), el total idéntico de 3.498 y
la advertencia de que «lo estable es el orden y las proporciones, no la última
unidad». Es más honesto que refrescar los números y callar el efecto.

### 6 · H4 con el filtro explícito — **RESUELTO**

La tabla declara antes de empezar que se limita a candef 8 y 9, y enumera lo que
queda fuera con sus cifras. Las cinco están verificadas arriba.

### 7 · Coherencia de estado (lo arregló el líder en `c31b24a`) — **RESUELTO**

`features.json` declara para F-012 la rama `feature/F-012-estudio-jornada-semanal`
y **esa rama existe y es la activa**. F-011 figura con `priority: 14` en
`features.json` y `current.md` dice ahora «última del backlog, prio 14 tras el
alta de F-015/F-016»: coinciden. El orden del backlog sigue siendo
F-012 → F-014 → F-010 → F-015 → F-016 (prioridades 4, 5, 6, 7, 8), coherente con
D6 y con el riesgo §10.6.

## Barrido de datos sensibles, repetido sobre la spec corregida (R7)

Obligatorio repetirlo: el anexo ha crecido con listas de `res.ide` y con una
consulta que toca `emp.dni`.

| patrón | resultado |
|---|---|
| `[0-9]{8}[A-Z]` (DNIs) | **0 coincidencias** |
| `https?://`, `api[_-]?key`, `apikey`, `x-api-key`, `password`, `passwd`, `token`, `Bearer`, `.azurecontainerapps`, `@ruesma.es` | **0 coincidencias** |
| `\b([0-9]{1,3}\.){3}[0-9]{1,3}\b` (IPs) | **0 coincidencias** |

La consulta nueva del grupo H5 **no trae el DNI**: proyecta
`CASE WHEN emp.dni IS NULL THEN 'sin' ELSE 'si' END`, que es la forma correcta de
responder «¿tiene DNI?» sin escribirlo. Los recursos se citan por `MO/NNNN` y por
`res.ide`, ambos permitidos por R7. **R7 se cumple.**

## Checkpoints (segunda pasada)

- **C1 — [x]** · `init.sh` exit 0; los siete ficheros del arnés presentes.
- **C2 — [x]** · Una sola `in_progress` (F-012); la rama activa es la declarada
  para la feature en curso y no es `main` ni `dev`; `current.md` describe la
  sesión activa; las `done` tienen resumen en `history.md`. Desaparece el N/A que
  la primera pasada tuvo que justificar: ahora se cumple literalmente.
- **C3 — N/A justificado** · La feature no crea ni modifica ningún fichero de
  código (`git diff dev...HEAD`: solo `specs/` y `progress/`). No hay
  arquitectura, cabeceras de ruta, imports ni dependencias que evaluar.
- **C3 bis — N/A justificado** · No toca `docs/referencia/` ni entra ningún PDF u
  ofimática al árbol. El barrido de datos sensibles se ha ejecutado igualmente
  (arriba, con los patrones): limpio.
- **C4 — [x]** · R1–R7 del bloque A verificados uno a uno (tabla de la primera
  pasada, más las verificaciones de esta). Los tests existentes siguen en verde y
  no se han tocado. Los MANUAL del humano están listados en `current.md` y en
  `tasks.md` T5 con su SQL de comprobación. R6, que era el `[ ]` de la primera
  pasada, se cumple.
- **C4 bis — [x]** · Rigor `documental` declarado y válido. **Fase RED N/A
  justificada** (`rigor.json`: `documental.fase_red = false`; el entregable es un
  documento, no hay código cuyo fallo previo enseñar). **Cobertura N/A
  justificada** (`documental.cobertura = false`; init.sh lo imprime con su
  motivo). **Mutación N/A justificada** (`documental.mutacion = false`; cero
  líneas de Python en el diff, no hay campaña que verificar ni prueba de control
  que hacer). **Sección «Evidencias» N/A justificada**: no hay implementer; su
  papel lo hace la verificación independiente de este informe, que reprodujo las
  cifras contra la fuente en lugar de creérselas.
- **C4 ter — N/A** · `harness/rutas_sensibles.json` no existe: sin declaración,
  el bloque es N/A por configuración y no hay nada que justificar.
- **C5 — [x]** · `tasks.md` con todas las tareas en `[x]` salvo T5, que queda
  pendiente **por diseño** (MANUAL del humano, pertenece a F-014, con su
  condición de bloqueo escrita). `git status` limpio, sin artefactos sueltos.
  `features.json` refleja el estado real, rama incluida. Los commits siguen el
  formato `F-012: <descripción>` en vez de `F-012 Tn:`; se acepta en un estudio
  cuyas tareas son de validación y cierre, **porque `tasks.md` cita ahora el
  commit que cierra cada tarea**, que es la trazabilidad que el checkpoint busca.

## Errata detectada en esta pasada (no bloquea, pero hay que arreglarla)

**E1 · `design.md:283`, caso L de la tabla §4, quedó sin actualizar.** Dice:

`| L. c 9 sin corregir en Sigrid (S 40 por mapa) | 9 / 40 | 9,9,9,9,6 | V 9/−3 | V jornada 4 → ord 4 + 2 extra |`

Esa combinación **ya no puede darse** con la regla decidida: con el mapa por
defecto un candef 9 da S = 42, y si 9 no estuviera en el mapa, D10 da S = 45
(5×9), nunca 40. La aritmética de la celda (40 − 36 = 4) es el último resto de la
opción (a) descartada. Además no encaja con el riesgo §10.6, que cita este mismo
caso L pero describe el escenario correcto: la cuadrilla **aún a candef 8**, cuyo
viernes de 6 h daría +2 h/semana de extra automática. La fila debería decir
`8 / 40` con ese desenlace, o suprimirse y dejar que §10.6 cuente el riesgo.

**Por qué no bloquea**: es una fila ilustrativa de una tabla de 20, mientras que
todo lo normativo —R10, R13, §6.1, §6.2, §7, §9.1 D10— es ya correcto y
consistente, y es el bloque B lo que F-015 hereda «tal cual». Un implementador
que siga R10 no se equivoca. **No la señalé en la primera pasada** pese a estar en
la misma tabla que el caso M, así que rechazar ahora por ella sería cobrarle al
spec-author un fallo mío.

**Condición del APPROVED**: corregir E1 en un commit de errata sobre esta misma
rama (documentación, rigor documental, sin código y sin nueva pasada de review),
o —si se prefiere no tocar más F-012— arrastrarla explícitamente a la spec de
F-015, que es quien hereda §4 como material de trabajo. Queda anotado en
`progress/current.md` por el líder.

## Veredicto

**APPROVED.** Los seis puntos de la primera pasada están resueltos, y resueltos
de verdad: no se ha parcheado el requisito y dejado el resto, se ha propagado la
decisión D10 a los seis sitios donde vivía la opción contraria, se ha retirado el
parámetro que sobraba de la firma del resolutor y se ha reconstruido el anexo
hasta que **las 18 sentencias ejecutan literalmente contra Sigrid**. Las cifras
del estudio se han vuelto a comprobar contra la fuente y siguen saliendo exactas,
incluidas las cinco de la nota nueva de H4 y el mapeo `res.ide` → `MO/NNNN` de la
cuadrilla. Queda la errata E1, documentada arriba con su condición.

F-012 puede pasar a `done` con su resumen en `progress/history.md`. Recordatorio
para el líder: **F-014 (MANUAL del humano) bloquea el merge de F-015**, no el
cierre de F-012; y F-010 va antes que F-015 (D6).

## Automejora del arnés (se mantiene la propuesta de la primera pasada)

Las tres propuestas siguen en pie y esta segunda pasada refuerza la tercera: la
verificación que ha dado valor real aquí no ha sido leer el documento, sino
**ejecutar su anexo tal cual y comprobar que devuelve lo que el texto afirma**.
Una feature documental que presenta datos debe traer sus consultas ejecutables, y
el reviewer debe ejecutarlas. Propuesta concreta para `CHECKPOINTS.md`, a portar
a `arnes-base`: en features de nivel `documental` que presenten datos medidos,
nuevo checkbox — «las consultas o comandos que sostienen las cifras están en el
documento en forma **ejecutable sin edición**, y el reviewer ha ejecutado al
menos las que sostienen los hallazgos principales, dejando el resultado en el
informe». Es el equivalente documental de la verificación independiente de la
campaña de mutación que C4 bis ya exige para el código.
