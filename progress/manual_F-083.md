# F-083 · Verificaciones manuales M1–M3 (T7)

Las ejecuta el implementer el 2026-11-24, a petición del humano («2 hazlo tu»; M1 y M3
autorizadas: «aturoizo m1 y m3»). Copia `partes-wt-f083`, rama
`feature/F-083-ciz-solo-fin-de-racha`, HEAD b468ae7 (código de producción sin cambios). Ningún
secreto en este fichero: credenciales del Key Vault solo en memoria de cada proceso; ningún
`.env` leído ni tocado (la copia no tiene `.env` en los servicios).

**Estado: M1, M2 y M3 en verde, limpieza hecha (2026-11-25).** Sin fallos del código. Falta M4
(solo lectura, tras desplegar sv5), que cierra T7.

## Montaje

Lanzadores en el scratchpad de la sesión
(`C:\Users\pgris\AppData\Local\Temp\claude\df60977b71b41004\e7e805c0-0ecb-4470-8b9f-c7a943e77b59\scratchpad\f083m\`),
copia de los de F-072 apuntando al código de la copia `partes-wt-f083` (python del `.venv` de
`partes`):

- **sv5 local** `127.0.0.1:8005` (`sv5.ps1`): `OBRA_PRUEBAS_FORZAR=true`, `OBRA_PRUEBAS_COD=0404`,
  `MARCA_PRUEBAS=PRUEBA-IA`, **`MOVER_CIZ=true`**, `COLAS_*`/`BLOBS_*` vacías, las tres variables
  de obras agrupadas. `/health` ⇒
  `{"ok":true,"modo_pruebas":true,"obra_pruebas":"0404","database":"ruesma","franquicia":"apagada"}`.
  Log: `[transfer-cola] DESACTIVADO (faltan COLAS_*): sv5 atiende solo por HTTP`.
- **sv4 local** `127.0.0.1:8014` (`sv4.ps1`): base `partes`, **`MOVER_CIZ=true`**,
  `TRANSFER_BASE_URL=http://127.0.0.1:8005`, colas vacías. Log:
  `[transfer][wiring] CABLEADO base_url=http://127.0.0.1:8005` y
  `[transfer-cola][wiring] DESACTIVADO`.
- Portal operado por su API con los cuerpos de `static/app.js` (`portal.py`: alta
  `/api/partes/nuevo`; aprobar y ↻ = `/api/aprobar/preflight` + `/api/aprobar/ejecutar` con los
  ids de la línea).
- Relanzarlos igual (si se pararon): en PowerShell, `& <scratchpad>\f083m\sv5.ps1` y, cuando
  `/health` dé `modo_pruebas: true`, `& <scratchpad>\f083m\sv4.ps1`.

## Comprobaciones previas (solo lectura)

- `prueba_escritura_sigrid.py estado` (copia en el scratchpad `f083m\prueba_mayo.py`, solo
  `ANO, MES = 2026, 5`; `diff`: una línea) ⇒ `NO existe parte 2026/05 de obra 0404`.
- Recurso de pruebas **2717792** (MO/0753, gruista, `cla` 1, empresa 1, de alta, CIV y CIZ en
  `reshor`). Ojo: es un trabajador real con líneas reales en mayo (otros partes, sin `synckey`);
  no las lee la racha (solo synckeys de la racha y, en pruebas, la marca).
- `partes`: del 2717792 en mayo solo había las 5 líneas **inactivas** de F-072 (12–14).
- Sigrid: `synckey LIKE 'partes:%:ciz'` ⇒ 5 (antes y después de la prueba); `MAX(hmores.ide)` =
  416441; ninguna `partes:<id>` ni `partes:<id>:ciz` de los ids creados (colisión 0).

**Días elegidos** (todos laborables, sin festivo de Madrid): M1 = 4–7 (L–J), M2 = 18–21 (L–J) y
**M3 = 25–27** (L–X). M3 se movió de 11–13 a 25–27 para no cruzarse con las líneas inactivas de
F-072 del mismo recurso el 12 y el 13.

## Partes de prueba creados (alta manual, obra 0404, recurso 2717792)

| Prueba | Día | Documento | Registro | Línea |
|---|---|---|---|---|
| M1 | 05-04 | `1db48c6d-55e0-436b-b2a1-ddbb9e4a10ed` | 25277 | V |
| M1 | 05-05 | `8e5dda31-d07c-47ad-8ee5-43d1233ef030` | 25278 | V |
| M1 | 05-06 | `97d95adf-35e9-4e8f-b83c-ba87fb9051e6` | 25279 | V |
| M1 | 05-07 | `7e5d3cef-dc17-4635-a2a8-cd5c2cbdceaa` | 25280 | 8 h HLGR (sin aprobar) |
| M2 | 05-18 | `42aeaea1-7f53-475d-8c6d-4eb607e28bd6` | 25281 | V |
| M2 | 05-19 | `cfb8c8fa-1b5a-49c0-b28b-615cdec0ccda` | 25282 | V |
| M2 | 05-20 | `77d5e3fa-fbea-4fc8-b964-65709c643e6c` | 25283 | V |
| M2 | 05-21 | `164dddbc-2a83-4be3-be13-f8f02a1af47e` | 25284 | 8 h HLGR |
| M3 | 05-25 | `d973eafc-01dc-497e-b7dc-f484488335a5` | 25285 | V |
| M3 | 05-26 | `06e3e1fd-6ab6-4c84-9d22-6459cff211a4` | 25286 | V |
| M3 | 05-27 | `e0ccd5bd-6a01-4fd5-afeb-303d8defb68e` | 25287 | V |

Parte de Sigrid creado por sv5: **PT26/00417** (`hmo` 2879614, 2026/05, 0404).

## M2 · regresión (18–21): **OK**

1. Aprobar 18–20 juntos ⇒ sv5 `roles … {25281: 'inicio', 25282: 'intermedio', 25283: 'fin'}`;
   escritas CIV 18 (`hmores` 416442, `partes:25281`) y CIZ 20 (416443, `partes:25283`); 25282
   omitida «dia intermedio de la incidencia: solo se registran el inicio y el fin».
2. (sin cambio manual)
3. ↻ en el 19 ⇒ sv5 `roles … {25282: 'fin'}`, `preflight … escribir=0 omitir=1`, `nada que
   escribir`. Motivo en `partes`: «dia intermedio de la incidencia: solo se registran el inicio y
   el fin (el fin, CIZ linea 416443, ya esta el dia 2026-05-20)». `escritas: []`; ningún
   `partes:25282` ni `partes:25282:ciz` en Sigrid; sin `racha_fin_no_ciz` (correcto: hay CIZ).
4. Aprobado el 21 ⇒ HLGR 8 h (416444, `partes:25284`).

## M1 · caso 0730 (4–7): paso 1 **OK**, espera el paso 2

1. Aprobar 4–6 juntos ⇒ `roles … {25277: 'inicio', 25278: 'intermedio', 25279: 'fin'}`; CIV 04
   (**416445**, `partes:25277`) y CIZ 06 (**416446**, `partes:25279`); 25278 `omitido`
   intermedio.

## M3 · inicio desordenado (25–27): paso 1 **OK**, espera el paso 2

1. Aprobar solo el 27 ⇒ `roles … {25287: 'fin'}`; CIZ 27 (**416447**, `partes:25287`).

## Sigrid tras los pasos 1 (lectura, `truncated: False`)

PT26/00417: CIV 18 (416442, pos 64), CIZ 20 (416443, 128), HLGR 21 (416444, 192), CIV 04
(416445, 256), CIZ 06 (416446, 320), CIZ 27 (416447, 384). Todas `PRUEBA-IA`.

## Paso 2 · cambio de CIZ a CIV de dos líneas de pruebas (2026-11-25)

| `hmores.ide` | Fecha | Parte | Synckey | Antes | Después |
|---|---|---|---|---|---|
| 416446 | 2026-05-06 | PT26/00417 (`hmo` 2879614) | `partes:25279` | CIZ | CIV |
| 416447 | 2026-05-27 | PT26/00417 (`hmo` 2879614) | `partes:25287` | CIZ | CIV |

**Lo hizo el líder por sigrid-api, con autorización expresa del humano, en lugar del cambio a
mano previsto**: UPDATE solo de `horide` 35 → 33; `synckey`, `tex` PRUEBA-IA, `can`, `pre` y
`tot` sin tocar (script del líder: `f083m\civ.py` del scratchpad de la sesión). El implementer no escribió en
Sigrid fuera de sv5 y de la limpieza. Lectura de comprobación (`s.py mayo`): 416446 y 416447 con
`cod` CIV, misma synckey y marca.

Nota: el recuento global `synckey LIKE 'partes:%:ciz'` pasó de 5 a 4 entre el 24 y el 25 sin
intervención de esta prueba (ninguna de sus líneas lleva `:ciz`): es actividad de producción
(un `fin` que mueve un CIZ hermano cambia su synckey). Por eso la comprobación de «sin `:ciz`
nuevos» se hace sobre las synckeys de los ids de la prueba.

## M1 · paso 3: **OK**

↻ en el 5 (25278) ⇒ sv5 `roles … {25278: 'fin'}`, `preflight … escribir=0 omitir=1`, `nada que
escribir`; `escritas: []`. Consola de sv5 (WARNING, preflight y registro):

```
[registro] racha_fin_no_ciz registro_id=25278 motivo=dia intermedio de la incidencia: solo se registran el inicio y el fin (la racha sigue en Sigrid el dia 2026-05-06, linea 416446 con CIV, sin CIZ despues; no se escribe un fin en medio)
```

En `partes`, 25278 `omitido` con ese mismo motivo (el que ve el portal). Sigrid: ni
`partes:25278` ni `partes:25278:ciz`.

## M3 · paso 3: **OK**

Aprobar el 25 (25285) ⇒ sv5 `roles … {25285: 'inicio'}`, `escribir=1`; una sola fila en el
INSERT (`partes:25285`, `horide` 33 = CIV); `escritas=1 … filas=1`. Consola:

```
[registro] ciz_mismo_dia_omitido registro_id=25285 motivo=posterior_sin_ciz      (INFO)
[registro] racha_fin_no_ciz registro_id=25285 motivo=posterior_sin_ciz           (WARNING)
```

Sigrid: CIV 25 (**416462**, `partes:25285`), sin `partes:25285:ciz`; el 27 sigue CIV (416447).
`partes`: 25285 `registrado` 416462; 25286 sin aprobar.

## Sigrid antes de limpiar (lectura por synckeys de 25277–25287)

7 líneas, todas en PT26/00417 y `PRUEBA-IA`: 416445 CIV 04, 416446 CIV 06, 416442 CIV 18, 416443
CIZ 20, 416444 HLGR 21, 416462 CIV 25 y 416447 CIV 27. Ninguna `partes:<id>:ciz`; ninguna de
25278, 25280, 25282, 25286.

## Limpieza

- **Sigrid** (`prueba_mayo.py`, copia con 2026/05; el script del repo no se tocó): DRY-RUN de 3
  sentencias, todas sobre `2879614` (PT26/00417, creado en esta prueba) ⇒ `limpiar --ejecutar`:
  `affected_rows` 7 + 1 + 1, `committed: true` ⇒ `estado` ⇒ `NO existe parte 2026/05 de obra
  0404`. Lectura posterior: 0 líneas con las synckeys de la prueba.
- **`partes`**: comprobación de F-024 (`/api/sigrid/comprobar`, `forzar`) sobre los 7
  registrados ⇒ `borradas: 7`; después «Mover a la papelera» de los 11 documentos ⇒ los 11 «Parte
  movido a la papelera». Estado final (lectura): los 11 `is_active = false`; líneas
  `borrado_sigrid` 7, `omitido` 2 (25278, 25282) y sin estado 2 (25280, 25286).
- **sv4 y sv5 locales parados** (procesos de los puertos 8014 y 8005).

## Pendiente

- **M4** (producción, solo lectura, tras desplegar sv5): la consulta de design §8 con el
  `MAX(hmores.ide)` del momento del despliegue. Con ella se cierra T7.
  - **Desplegado el 2026-11-25** (sv5 `r20261125120627`, arranque ~11:11 UTC; `MOVER_CIZ=true`,
    `OBRA_PRUEBAS_FORZAR=false`). **Línea base: `MAX(hmores.ide)` = 416461**, leída tras el
    arranque (la última línea de la prueba, 416462, ya estaba borrada).
  - Primera pasada (líder, 2026-11-25, minutos después del arranque): 0 CIZ de partes con
    `ide > 416461` y 0 filas en la consulta de M4. Es lo esperado sin aprobaciones todavía:
    **M4 se repite dentro de unos días** con la misma base, y con ella se cierra T7.
