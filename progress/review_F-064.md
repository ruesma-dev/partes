Revisión completa (pasada 1) · delta `f940e67..5778ad0` (f940e67 = `dev` con F-061 fusionada)

# F-064 · Review (reviewer)

**Veredicto: APPROVED.** La implementación cumple R1–R25 con DA1–DA7 = A. Las dos desviaciones
declaradas son correctas. Quedan seis observaciones que no bloquean (§ Observaciones).

**Rigor:** `estandar`, declarado en `features.json`. Exige fase RED, cobertura de las líneas
cambiadas y mutación muestreada (tope 20) con los supervivientes analizados. RM5 es N/A por nivel.

## Verificación ejecutada por el reviewer

- `bash harness/init.sh`, tal cual: **ENTORNO LISTO**. Raíz: 522 passed, 3 skipped. COBERTURA
  `[OK]` 100 % (7/7). TAMAÑO `[OK]`. sv4 salió **de caché**, así que la suite de sv4 se lanzó
  entera aparte: `python -m pytest -q -p no:cacheprovider` ⇒ **2984 passed, 1 skipped** (508 s).
- Tests de F-064: 98 (9 de Python y 89 de node), todos en verde. node está instalado: ninguno se
  salta (`_node` hace `skip` sin node).
- **Mutación (Python).** Recalculada con `alcance_de_feature` y `generar_mutantes`: 2 ficheros,
  32 líneas y **4 mutantes**, igual que el informe (16→17, `not`, `or`→`and` y `==`→`!=` en
  `identidad.py`; ninguno es equivalente, RM3).
  - Tiempo total de 1874,7 s, más de 60 s: **la campaña no se reejecuta**. Vale el recálculo
    puro más RM1–RM6.
  - **RM1.** Se midió `ec1a689`. Hasta HEAD solo cambian `progress/` y `tasks.md`, fuera del
    alcance.
  - **RM2.** Media × W = 468,7 × 4 = 1875 s, frente a una línea base de ~630 s más la evaluación,
    con 4 workers compitiendo: coherente. Total = 4 × 468,7. Sin «⚠ CAMPAÑA NO VÁLIDA» y con
    «Sin veredicto» = 0.
  - **RM6.** No se quitó código defensivo.
- **Mutación manual del JS (RM4).** La herramienta no alcanza `app.js`. Hice 30 mutantes a mano
  sobre una **copia** en el scratchpad, sin tocar el árbol, con `test_f064_filtros_js.py`
  (~20 s cada uno). **24 muertos y 6 vivos.** Los vivos son equivalentes o casi:
  - quitar `restaurando` en `guardar` o en `quitarTodo` (los oyentes se enganchan después; en
    `quitarTodo` solo añade escrituras intermedias que la final deja igual);
  - quitar la guarda R5 de `restaurar` (`leer`, `guardar` y `escribir` ya cortan sin usuario);
  - `sinExtra: true` (la foto sigue siendo vacía) y admitir un valor de solo espacios (`foto`
    nunca lo escribe);
  - `claveColumna` por índice entre inputs en vez de `cellIndex` (observación 2).

  Mueren los centrales: borde de las 8 h, `t` futuro, poda a 50 y su orden, barrido solo con
  `PREFIJO`, clave de tabla, foto que conserva días de otro periodo y búsqueda ajena, redirección
  solo con `search === ""`, parámetros ajenos, periodo de los días, aviso solo si hay reposición,
  todo `quitarTodo`, el `input` de reposición, la escritura única, los enganches de
  `lineas:cambio` y de la casilla, `leer` que borra lo inválido, `seleccionar` (filtrado y
  `apply`) y la clave vacía sin usuario. **Conclusión:** los tests de node ejecutan el código
  real y vigilan de verdad R4–R19.

## Desviaciones declaradas

1. **Ancla de `test_f043_portal_fecha.py::_manejador_principal`: correcta.** Solo cambia cómo se
   localiza el manejador (`rindex` del `addEventListener` previo al comentario del visor de PDF);
   las aserciones de F-043 no cambian. Es el efecto obligado de R19 («primera línea») y queda en
   sv4, así que R24 se cumple. Solo falta en la lista de T8.
2. **La foto conserva lo que la página no ve: correcta, no hace falta consultar.**
   - Días de otro periodo: sin esto, la escritura única de R15 al abrir otro mes los borraría, y
     **M1.2** («otro mes ⇒ sin días; de vuelta ⇒ días»), del diseño aprobado, fallaría. «Quitar
     filtro» en el mismo periodo y «Quitar filtros» siguen borrándolos.
   - La búsqueda con `?message=`: R19 dice «ni guarda», y no pisar lo guardado es la lectura
     literal. Así, el `?message=` tras un borrado no hace perder la búsqueda.
   - Conviene que el humano lo vea en M1, pero no cambia nada de lo aprobado.

## Solape con F-061

No rompe nada. `partes_list.html` cambia solo en la l. 34 («Limpiar»). La insignia «Sin líneas»
(l. 69) y `_irTrasBorrar` / `destinoTrasBorrar` no se tocan. Ir a `/partes` sin consulta vuelve
a la búsqueda guardada, como prevé el diseño §3 (se mira en M1). Los tests de F-061 entran en la
suite de sv4.

## Privacidad

- El actor no queda en claro: en el HTML va el hash (lo prueba
  `test_f064_r1_r3_dos_usuarios_dos_claves_y_sin_el_actor`) y en `localStorage` la clave es
  `partes.filtros.v1:<16 hex>`. Sin sal, como acepta el diseño §4.1.
- Sí quedan textos tecleados y, en la matriz, claves de día con el nombre normalizado del
  trabajador (`lopez|2026-10-03`). Es la forma exacta del diseño §5 aprobado (observación 3).

## Checkpoints

- **C1** [x] init.sh con exit 0 · [x] los ficheros base existen.
- **C2** [x] una sola `in_progress` · [x] rama `feature/F-064-filtro-en-sesion` · [x]
  `current.md` solo con la sesión del 2026-10-26 (F-064 y F-061, cerrada hoy y pendiente de
  despliegue) · [x] las `done` tienen historia.
- **C3** [x] hexagonal (`clave_filtros` pura en `interface_adapters/web`; la global delega) ·
  [x] primera línea con la ruta · [x] sin prints, `console.log`, secretos ni dependencias nuevas
  · [x] trampas del dominio: no aplica (no toca registro, incidencias ni ORM).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazabilidad (tabla de abajo y observación 1) · [x] sin red ni BBDD (SQLite en
  memoria y DOM falso) · [x] M1 y M2 en `current.md` y en el diseño §8 (M0 hecha).
- **C4 bis** [x] rigor declarado · [x] fase RED con trazas reales de T1, T4 y T5 · [x] cobertura
  `[OK]` · [x] mutación verificada de forma independiente · [x] muertos no reejecutados (> 60 s,
  dicho arriba) · [x] coste por mutante 1875 s > 1 s · [x] sin campaña no válida · [x] RM1 ·
  [x] RM2 · N/A RM5 (rigor `estandar`) · [x] RM6 · N/A campaña manual (la automática dio 4) ·
  [x] sin supervivientes · [x] «Evidencias» con los 4 números (la mutación la completan
  `mutacion_F-064.md` y `current.md`, con 4 workers).
- **C4 ter** N/A: no hay `rutas_sensibles.json`.
- **C5** [x] T0–T10 `[x]` con commit `F-064 Tn:`; T11 (M1) y T12 (M2) son MANUAL, después del
  review y del despliegue, como en F-061: N/A justificado · [x] árbol limpio · [x]
  `features.json` en `in_progress`, el estado real.

## Cobertura: requisito → test

| R | Test(s) |
|---|---|
| R1–R3 | `test_f064_clave_usuario.py` (`r1_*`, `r2_*`, `r1_r3_*`); los de F-017 en verde sin tocarlos |
| R4 | `r10_con_pantalla_pone_la_foto_con_su_t` (forma `{v,t,pantallas}`), `r6_constantes_de_sesion` (`PREFIJO`) y bloque «DOM falso · R4…» |
| R5, R9 | `r5_r9_clave_de_almacen_por_usuario`, `r5_sin_clave_*`, `r5_localstorage_que_lanza_*`, `r9_lo_de_un_usuario_*` |
| R6, R8 | `r6_*` (borde de 8 h, inválidos, futuro), `r6_r8_barre_caducados_*`, `r6_estado_caducado_no_redirige` |
| R7 | `r7_poda_a_las_50_*`, `r7_con_pantalla_no_muta_*` |
| R10, R14 | `r10_un_cambio_de_filtro_guarda_*`, `r10_r14_foto_vacia_*`, `r14_foto_vacia` |
| R11 | `r11_r15_r18_repone_por_tabla_y_columna_*`, `r11_tabla_sin_id_*` |
| R12, R13, R16 | `r12_*` (5), `r13_casilla_*`, `r16_*` (4) |
| R15, R17, R18 | `r11_r15_r18_*`, `r15_restaurar_va_justo_antes_*`, `r17_quitar_filtros_*`, `r17_filtros_repuestos` |
| R19, R20 | `r19_*` (7), `r19_r20_limpiar_*`, `r20_limpiar_apunta_*` |
| R21–R23 | `r21_filtros_sesion_no_toca_la_seleccion`, `r22_r23_funciones_intactas` (5 huellas), `r23_vista_clave_intacta` |
| R24 | `git diff --stat f940e67..HEAD`: solo sv4, el doc, `specs/`, `progress/`, `features.json` y `BACKLOG.md` |
| R25 | lo revisé: el punto 11 cuenta la clave, el guardado por usuario y pantalla, las 8 h y que la selección no se guarda |

## Observaciones (no bloquean; propuestas al humano)

1. **R4 no tiene ningún `test_f064_r4_*`.** Se cubre por el contenido y por el comentario del
   bloque. Basta con renombrar `test_f064_r10_con_pantalla_…` a `test_f064_r4_r10_…`.
2. **Hueco del DOM falso.** No hay ninguna columna sin filtro **antes** de las filtrables, así
   que una `claveColumna` por índice entre inputs sobrevive. El código real (`cellIndex`) está
   bien. Un test con una primera columna sin input lo fijaría.
3. **Privacidad aceptada en el diseño, a tener presente.** Hasta 8 h quedan nombres
   normalizados de trabajador (claves de día de la matriz) y textos tecleados. Lo caducado solo
   se barre en la siguiente carga del portal en ese navegador.
4. **`conPantalla` falla si una pantalla guardada es `null`.** `pantallas[b].t` lanza
   `TypeError` dentro de `restaurar`, y entonces no corren `restaurarVista` ni
   `esperasDeLaPagina`. Solo se alcanza manipulando a mano el `localStorage` (el código nunca
   escribe `null`). Se podría blindar validando las entradas en `estadoVigente`.
5. **Commits sin tildes**: «limite» (8699741), «sesion» (29e1f43) y «dias» (98a751a). No se
   reescribe la historia.
6. **`current.md`** mantiene «Decisiones abiertas para el humano» en F-064, aunque ya están
   aprobadas. Es redacción vieja.

## Automejora (propuesta, no aplicada)

Si `init.sh` da en caché un servicio que toca la feature, la pasada del reviewer no ejecuta su
suite. Propongo que `reviewer.md` exija lanzarla a mano en ese caso y decirlo en el informe.
