<!-- progress/review_F-020.md -->
Revisión completa (pasada 1): `git diff dev...HEAD`, HEAD `67b0520` (merge-base `566286d`)

# F-020 · Review

**Veredicto: APPROVED**

**Nivel de rigor:** `estandar`, declarado en `harness/features.json`. Exige
fase RED en los requisitos centrales (R1, R10, R17, R20), cobertura de líneas
cambiadas ≥ 80 % y mutación muestreada (20, semilla 20260820) con los
supervivientes analizados.

## Qué se ha comprobado (con resultado real)

- `bash harness/init.sh`: **ENTORNO LISTO**. Raíz `402 passed, 1 skipped`,
  `servicio sv1-email: pytest en verde`, `PUERTA COBERTURA: 99.0% (200/202)`,
  `PUERTA TAMAÑO` en OK. Como sv1 salió de caché, relancé su suite a mano sin
  caché: `74 passed in 5.53s`.
- **Límite de servicio:** el diff solo toca `services/partes-email/` y
  `docs/ARCHITECTURE.md` (más `progress/`, `specs/` y las altas de backlog
  del líder, que no se han revisado). `harness/servicios.json` no cambia ni
  hacía falta (design §3).
- **sv2/sv3:** sv2 (`main_worker.py:77`) reenvía `context` opaco (su
  `extra="forbid"` es del esquema de la IA, no del contexto). sv3 solo lee
  `attachment.name` y `attachment.sha256` (`sqlalchemy_parte_repository.py:536-537`),
  que ahora llevan el PDF interior; `embedded_in` acaba solo en
  `raw_context_json`. No se rompe nada. R18 lo fija un dict literal escrito
  en T5 sobre el pipeline sin tocar.
- **Tope y bucles:** el extractor solo baja en `message/rfc822`, y
  `nivel + 1 > nivel_maximo` corta (5). El árbol MIME sale del parser, es
  finito y no tiene ciclos. Un multipart anidado de forma patológica acabaría
  en `RecursionError`, que el `except Exception` de `extraer` convierte en
  `CorreoAdjuntoIlegible` ⇒ `Errores`. La frontera 5/6 está probada, y D3
  (todo o nada) también, en el pipeline.
- **Descartes que se mantienen:** `referenceAttachment` sea cual sea su tipo
  (R2), `itemAttachment` que no es correo (R3), correo adjunto inline o por
  encima del límite (R4), `.msg`/TNEF (DA4) e imágenes interiores (R9).
- **D1–D4:** D1 hecho (solo entorno). D2, D3 y D4 implementados según la
  propuesta aprobada, con un test cada uno.
- **Sin red:** buzón y sumidero en memoria (`dobles.py`), `.eml` construidos
  en el propio test con `@example.com`, y `main.main()` con
  Settings/Graph/colas/blob sustituidos.
- **Barrido de secretos** en el diff (sin backlog), con los patrones `GUID`,
  `AccountKey|password|secret`, `@dominio.(es|com)` salvo `example.com`,
  IPv4, `print(`, `breakpoint|pdb` y `AAMk`: **0 coincidencias**.

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros del arnés presentes.
**C2** [x] una sola `in_progress` · [x] rama `feature/F-020-...` ·
[x] `current.md`: la parte de F-020 es correcta y lleva la MANUAL. Las
secciones antiguas ya estaban en `dev` y no las mete esta rama (Obs. 2) ·
[x] features `done` con su resumen.
**C3** [x] hexagonal: el pipeline depende del puerto y el extractor vive en
`infrastructure/document/`; dominio sin infraestructura · [x] ruta en la
primera línea de los 14 ficheros · [x] sin prints, sin TODOs ni secretos; la
única dependencia, pypdf en los tests, estaba prevista (D1) y ya figuraba en
`requirements.txt` · [x] trampas de dominio: N/A por contenido (sv1 no toca
Sigrid, incidencias ni el ORM).
**C3 bis** N/A: no toca `docs/referencia/`.
**C4** [x] R1–R26 trazados y en verde (tabla abajo) · [x] sin red ni BBDD ·
[x] MANUAL de design §10 en `current.md`, con los pasos y las líneas de log.
**C4 bis**
- [x] `rigor: estandar` declarado.
- [x] Fase RED con trazas reales en `impl_F-020.md`: R10 (`ModuleNotFoundError`),
  R1 (6 failed), R17+R20 (6 failed, con el que pasa explicado) y R25 (`KeyError`).
- [x] Cobertura `[OK] 99.0%`.
- [x] Mutación, recálculo puro al SHA medido `739f5b7`: **594 líneas, 76
  mutantes**, igual que el informe. Los 4 supervivientes existen, con el mismo
  operador y el mismo texto (306, 363, 618, 149).
- [x] Muertos comprobados. El «Tiempo total» (271.1 s) pasa de 60 s, pero
  **reejecuté la campaña a HEAD** por RM1: `20 evaluados, 19 muertos,
  1 superviviente, 0 timeouts, 0 sin veredicto, 54.0 s`, base en verde en los
  6 workers. Salida al scratchpad; `git status` limpio.
- [x] Coste por mutante: 271.1 × 6 / 20 = 81 s ≥ línea base ~63 s.
- [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0.
- [x] RM1: el SHA medido no es HEAD, y `cdf25ae` tocó el alcance después:
  quita de `mime_pdf_extractor.py` un `except CorreoAdjuntoIlegible: raise`
  inalcanzable. El recálculo a HEAD da 592 líneas y los mismos 76 mutantes, y
  mi reejecución saca la misma muestra: los 3 huecos reales mueren y solo
  sobrevive el equivalente (363). La campaña queda validada a HEAD.
- [x] RM2: media × W = 13.6 × 6 = 81.6 s contra ~63 s de base. Coherente.
- [x] RM3: ningún equivalente sale muerto; el 363 sobrevive, como debe.
- [x] RM5: N/A por nivel. En `estandar` basta la justificación escrita, y la
  hay: con `ok=False` el correo va a Errores y no se encola nada; solo cambia
  el recuento del log.
- [x] RM6: no se quitó ninguna guarda; `cdf25ae` borra código muerto, no
  defensa.
- [x] Campaña manual: N/A, la automática dio 76 mutantes.
- [x] Supervivientes analizados, ninguno `PENDIENTE`.
- [x] «Evidencias» completas, workers (6) incluidos.
- [x] Ningún N/A de este bloque sin justificar.

**C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
**C5** [x] T1–T12 `[x]`, un commit `F-020 Tn:` por tarea · [x] sin
artefactos sin trackear (el worktree `.claude/worktrees/agent-ad862…` es de
F-018) · [x] `features.json` en `in_progress`, a la espera de este veredicto.

## Cobertura requisito → test (`services/partes-email/tests/`)

| Req | Test(s) |
|---|---|
| R1 | `r1_correo_adjunto_se_abre_e_ingiere_su_pdf` (6 casos item/file/sin odata × mayúsculas), `r1_..._inline_no_se_abre` |
| R2 · R3 | `r2_reference_attachment_se_descarta_con_info` · `r3_item_attachment_no_correo_se_descarta_con_info` |
| R4 | `r4_..._mayor_que_el_limite`, `r4_..._justo_en_el_limite`, `r4_limite_cero_significa_sin_limite` |
| R5 · R6 | `r5_se_abre_sea_cual_sea_el_remitente` · `r6_..._solo_cuesta_su_descarga_de_value` |
| R7 · R8 · R9 | `r7_*` (6) · `r8_*` (3) · `r9_*` (2) |
| R10 | `r10_*` (5) + `r20_tope_excedido_no_ingiere_nada_y_va_a_errores` |
| R11 · R12 · R13 | `r11_*` · `r12_*` (7) · `r13_extractor_solo_importa_stdlib_pura_y_dominio` |
| R14 · R15 · R16 | `r14_varios_pdf_...` · `r15_*` (2) · `r16_contexto_describe_el_pdf_interior` |
| R17 · R18 | `r17_to_context_*` (2), `r17_embedded_in_*` (2) · `r18_*` (2, dict literal) |
| R19 · R20 · R21 | `r19_mezcla_...` · `r20_*` (6) · `r21_..._procesados` |
| R22 · R23 · R24 | `r22_*` (4) · `r23_..._nombrando_ambos_casos` · `r24_los_logs_no_llevan_bytes_ni_contenido` |
| R25 · R26 | `wiring_main::r25_*` (2), `pipeline::r25_...inyectado` · línea sv1-email de init.sh |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

1. `azure-apps/partes.md` §3.1 («Por cada correo con PDF: guarda el
   adjunto») no menciona los correos adjuntos. La spec aprobada decidió no
   tocarlo (design §4); una línea ayudaría. Lo decide el humano.
2. `progress/current.md` sigue con «F-020 · spec escrita, pendiente de
   aprobación» y D1–D4 como abiertas. Al cerrar, el líder debería condensarlo
   en `history.md`.
3. La descripción de F-020 en `features.json` (commit de backlog del líder,
   fuera del alcance revisado) cita la dirección real del remitente del
   escáner. No es un secreto, pero choca con la regla de «ningún dato real».
4. Cuando el único adjunto es un correo adjunto descartado por tamaño, el log
   de R23 («ni PDF/imagen directos ni correos adjuntos») es algo impreciso,
   aunque antes sale el WARNING específico.

## Automejora propuesta (no aplicada)

- RM1 en `reviewer.md`: si lo cambiado después de medir en el alcance es solo
  borrado de código muerto, bastaría el recálculo puro a HEAD (mismos
  mutantes, misma muestra) en lugar de repetir la campaña.
