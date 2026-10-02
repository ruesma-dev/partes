# F-025 · Exploración de Sigrid: incidencias y horas el mismo día (solo lectura, 2026-10-01)

Autor: spec-author. Datos **agregados**: sin DNIs, nombres ni identificadores
de personas. Solo `SELECT` por `POST /api/sql/read` de sigrid-api, base
`ruesma`, con el cliente de lectura de sv3 (`SigridApiClient._post_sql_read`)
y su config local, desde scripts en el scratchpad (fuera del repo; el `.env`
no se abrió ni se imprimió). Ninguna escritura.

## 0. Diccionario (`azure-apps/sigrid_tablas.md`)

- `auxhor` («Recursos: Tipos de horas») no tiene ningún campo que diga si una
  incidencia es de día completo o parcial. Lo más parecido, `tipincnom` («Es
  incidencia de nóminas»), es un indicador sí/no.
- `auxincfic` («Incidencias de fichaje»: `tip` justif./incid., `gru`,
  `auslar` «Ausencia larga», `tipabs`) y `e_aus` («Ausencias»: `numhor`,
  `auspor` %, `auslar`) **sí** clasificarían, pero son del módulo de
  RRHH/fichajes, no del tipo de hora de los partes (`hmores.horide` →
  `auxhor`).

## 1. Catálogo real

| `auxhor.cod` | `res` | letra del parte |
|---|---|---|
| CIA | Accidente/Enf. Profesional(AT) | AT |
| CIE | Enfermedad/Acc. no laboral(B) | B |
| CIF | Falta injustificada(F) | F |
| CIH | **Huelga(H)** | H |
| CIM | Maternidad/Paternidad(M) | M |
| CIP | Falta Justificada/Permiso(FJ) | FJ |
| CIV | Vacaciones(V) | V |
| CIZ | Fin de Incidencia | — |

- 60 tipos de hora en total. `tipincnom = 0` en **todos**.
- `auxincfic` y `e_aus` están **vacías**: Sigrid no usa el módulo de ausencias.
- **Conclusión: Sigrid no clasifica las incidencias.** Hay que llevar una
  tabla versionada propia.
- `auxhor.ext = 0` en **todos** los códigos, también en los `HE%` (horas
  extra). Una extra solo se reconoce por su código (`HE%`) o, en partes, por
  `tipo_hora = 'extra'`; nunca por `hora_ext`.
- Discrepancia documental: `docs/referencia/partes-proyecto.md` §4.1 dice
  «H horas sindicales/permiso horario (CIH)». Sigrid, sv2
  (`parte_models.py`) y el formulario «+ Nuevo» dicen **Huelga**.

## 2. Uso en 2026 (`hmores`, fechas 2026)

29.756 líneas de 751 recursos; 1.278 son incidencias (`CI%`).

| código | líneas | `can = 0` | `can ≠ 0` (valores) | recursos |
|---|---|---|---|---|
| CIV | 497 | 451 | 46 (41 × 1; 7; 4 × 8) | 189 |
| CIZ | 654 | 605 | 49 (45 × 1; 4 × 8) | 193 |
| CIP | 56 | 51 | 5 (× 1) | 41 |
| CIE | 48 | 44 | 4 (1; 7; 2 × 8) | 33 |
| CIA | 12 | 12 | 0 | 9 |
| CIM | 6 | 5 | 1 (× 1) | 5 |
| CIF | 5 | 5 | 0 | 5 |
| CIH | 0 | — | — | — |

Las líneas a mano de Administración llevan a veces `can = 1` o `8`: lo que
marcan es el hecho, no una duración por horas. Ninguna incidencia de 2026
lleva una cantidad parcial «de permiso por horas» del tipo 2 o 3 horas.

## 3. Mismo recurso y mismo día: incidencia + horas (`can ≠ 0`)

| código | días con la incidencia | con horas `HL%` | con extra `HE%` | con códigos mensuales `M*` (1 ud.) |
|---|---|---|---|---|
| CIV | 469 | 0 | 0 | 11 |
| CIE | 47 | 0 | 0 | 0 |
| CIM | 5 | 0 | 0 | 0 |
| CIP | 56 | 0 | 0 | 0 |
| CIF | 5 | 0 | 0 | 0 |
| CIA | 12 | **1 (2 h)** | 0 | 0 |
| CIZ | 597 | 2 (1 h y 8 h) | **2 (1 h y 2 h)** | 30 |

- Lo que Administración teclea a mano **casi nunca** junta en un mismo día
  una incidencia con horas de trabajo: 5 días como mucho de 1.191, contando las
  horas `HL`/`HE`.
- El único caso de incidencia + horas en un día que no es fin de racha es
  **AT con 2 h**: trabajó dos horas y tuvo el accidente. Es **legítimo**, y
  por eso AT tiene que ser «parcial».
- Ni un solo permiso (CIP/FJ) de 2026 lleva horas el mismo día.
- Las líneas `M*` (mensuales, 1 unidad) junto a CIV/CIZ son de mensuales,
  que sv5 no registra (R2 de `reglas_registro.py`): fuera de F-025.
- CIZ = **último día de la incidencia, no el de vuelta**: si fuera el de
  vuelta, casi todos los CIZ de quien cobra por horas llevarían `HL`. Solo
  hay 2.

## 4. Trabajo DENTRO de una racha (CI\* → siguiente CIZ del recurso)

| código | rachas | cerradas con CIZ | con `HL` dentro | con `HE` dentro | duración media / máx. (días) |
|---|---|---|---|---|---|
| CIV | 469 | 403 | 3 | 4 | 8 / 125 |
| CIE | 47 | 35 | 0 | 0 | 26 / 189 |
| CIP | 56 | 32 | 4 | 6 | 11 / 83 |
| CIA | 12 | 9 | 0 | 0 | 15 / 51 |
| CIM | 5 | 2 | 1 | 0 | 17 / 21 |
| CIF | 5 | 0 | — | — | — |

Hay trabajo dentro de alguna racha (sobre todo en permisos), pero es poco y
es ambiguo: puede ser una racha mal cerrada o dos rachas seguidas. En
partes, los días intermedios no tienen línea («V……V»), así que esto no se
puede detectar con una regla de «mismo día»: queda **fuera de F-025**
(design §8, DA9).

## 5. Lo que se lleva la spec

1. La clasificación no existe en Sigrid ⇒ tabla versionada propia en sv4
   (DA1).
2. Día completo: V, B, M, F (0 casos legítimos con horas). Parcial: AT
   (caso real legítimo), FJ (permisos por horas), H (paros parciales) (DA2).
3. En partes, una extra se reconoce por `tipo_hora`, no por `hora_ext`.
4. Corregir la H de `partes-proyecto.md` §4.1: es Huelga.
5. No se ha consultado PostgreSQL `partes`: requiere firewall. El recuento de
   conflictos que ya hay en el portal es la verificación manual M1.
