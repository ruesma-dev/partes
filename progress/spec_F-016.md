<!-- progress/spec_F-016.md -->
# F-016 · Informe del spec-author

Fecha: 2026-08-19. Rama: `feature/F-016-admin-empleado-jornada` (worktree
aislado; el árbol principal seguía con F-015). `harness/features.json` y
`progress/current.md` **no** se han tocado: F-016 sigue `pending`.

## Qué he redactado

`specs/F-016-admin-empleado-jornada/` con los tres ficheros:

- **`requirements.md`** — 19 requisitos EARS (R1–R19) con criterios de
  aceptación y nombre de test, tabla de trazabilidad requisito → test →
  fichero, fase RED marcada en R7/R12/R14/R15 y un bloque «fuera de alcance»
  explícito.
- **`design.md`** — límite de servicio (**solo sv4**), modelo de la pantalla,
  ficheros a crear/modificar/NO tocar con ruta exacta, firmas de las
  funciones nuevas por capa, las seis rutas HTTP, el plan de pruebas (con la
  tabla de casos del solape y las 5 verificaciones MANUAL), 4 riesgos, 10
  decisiones propias (DA1–DA10) y 6 dudas para el humano.
- **`tasks.md`** — T0–T10, ordenadas por dependencia, cada una con su
  verificación; T0 es la puerta de entrada (F-015 mergeada) y T10 es
  `bash harness/init.sh` en verde.

Diseñado contra la especificación de F-015 (§6 y R16/R18/R27/R30 de su rama),
no contra el árbol actual: hoy `empleado_jornada` todavía no existe.

## Decisiones que he tomado yo

1. **El humano escribe «último día incluido», nunca `hasta`** (DA1, R7). El
   formulario y el listado hablan en inclusivo; la conversión `+1 día` vive
   solo en la capa web. «Hasta el 31/07» se guarda como `2026-08-01` sin que
   el usuario tenga que saberlo. Era la trampa que F-015 dejó señalada.
2. **Cerrar ≠ desactivar** (DA2). Cerrar pone `hasta` (historia legítima);
   desactivar es la papelera lógica `is_active` (semántica 8). No se funden.
3. **Un solape se rechaza (409), nunca se resuelve solo** (DA3, R12). La
   respuesta nombra la fila en conflicto; el sistema no recorta la vigencia
   ajena, porque reescribiría en silencio un dato con el que sv3 ya calculó
   extras. Contiguas (`hasta` = `desde`) NO solapan: es el caso normal.
4. **`sv3` no se toca**, y está justificado (DA7): que sv3 «se entere» de un
   cambio exigiría acoplamiento nuevo entre servicios. Se acepta el TTL que
   ya existe y **se avisa en pantalla**, con los minutos derivados de
   `JORNADA_CACHE_TTL_S`, no cableados (R14). sv4 sí invalida su propio
   proveedor tras cada escritura con éxito — es el único cambio de F-016
   sobre lo que deja F-015.
5. **Cero cambios de schema** (R1): F-016 vive con las 16 columnas de F-015 y
   no toca ninguna copia de `orm_models.py`. Hay un test que lo vigila.
6. **La validación en `application/services/jornada_admin.py`**, funciones
   puras, siguiendo el precedente de `congelacion.py` (F-004), y los cinco
   métodos nuevos colgando del `ParteReviewRepository` único de sv4 (DA5,
   DA6): son los patrones reales del servicio, no un patrón nuevo.
7. **Puerta de acceso en una sola función** `_exigir_admin_jornadas()`
   (DA9, R15), gobernada por `JORNADAS_ADMIN_ENABLED` (default `true`, única
   variable nueva, sin cambios en `infra/`). Cuando llegue F-008, el rol se
   enchufa ahí y en ningún otro sitio.
8. **He añadido «Reactivar»** (DA4), que no estaba en el enunciado: sin él,
   una desactivación por error solo se arregla por SQL, que es justo lo que
   la feature viene a evitar. Marcado como lo primero que se recorta si el
   humano quiere menos alcance.

## Hallazgo que corrige una premisa del encargo

**sv4 NO lee hoy la identidad de Easy Auth.** No hay ni una referencia a
`X-MS-CLIENT-PRINCIPAL-*` en todo el repositorio: `approved_by` y
`deleted_by` se rellenan con la variable `DEFAULT_REVIEWER`, igual para
todos. Así que «la identidad que sv4 ya tiene» no existe. La spec propone el
helper `_actor(request)` (cabecera de Easy Auth, con `DEFAULT_REVIEWER` de
reserva) **acotado a las columnas de F-016** — ver duda 2.

## Dudas para el humano (las 6 están en `design.md` §13)

1. **Acceso mientras no exista F-008**: propuesta = abierta a cualquier
   usuario autenticado, como el reencolado de poison (precedente del
   2026-08-13), con interruptor `JORNADAS_ADMIN_ENABLED` para apagarla desde
   Azure. Alternativas: default apagado, o dejar F-016 en `blocked` hasta
   F-008. **Es la duda que más conviene contestar antes de implementar.**
2. **¿Se introduce la lectura de Easy Auth?** Acotada a F-016, o se extiende
   a `approved_by`/`deleted_by` (eso cambiaría el significado de datos ya
   guardados: parece material de F-008).
3. **¿Selector de trabajador o DNI a mano?** La spec pide el DNI a mano y
   solo **avisa** si no consta en el catálogo de Sigrid. Un combo como el de
   «+ Nuevo» es bastante más JS; si se quiere, hay que decirlo ahora.
4. **Tres normalizadores de DNI equivalentes en sv4.** F-016 no los unifica,
   pero deja un test que salta si divergen. ¿Feature de limpieza aparte?
5. **¿Se queda «Reactivar»?** (decisión 8 de arriba).
6. **`origen`**: cuando existan filas importadas de `sigrid`/`sesame`, ¿solo
   lectura o editables desde la pantalla? No urge.

## Estado

- `bash harness/init.sh`: **en verde** (exit 0) sobre la rama, con la puerta
  de cobertura en `N/A` con motivo (F-016 no cambia líneas Python: la spec es
  documentación).
- No se ha escrito ni una línea de código de producción, que es lo correcto
  para este rol.
- Siguiente paso del líder: PARADA 1 con el humano sobre las 6 dudas y, con
  su aprobación, `spec_ready`. **La implementación no puede empezar hasta que
  F-015 esté mergeada en `dev`** (T0 de `tasks.md`).
