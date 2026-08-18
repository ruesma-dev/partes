<!-- progress/mutacion_F-010.md -->
# F-010 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-010` el 2026-08-18 21:43.

## Alcance

Origen del diff: **rama** (`716a4f717f28571ef5987c586d69ac6d31d5035f` .. `feature/F-010-resincronizar-orm-models`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/infrastructure/database/orm_models.py` | 113 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 24 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 106 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 14 |
| **Total** | **257** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 23 |
| Mutantes evaluados | 23 |
| Muertos | 23 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Tiempo total | 61.0 s |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Nota del implementer (2026-08-18)

Esta es la **segunda** campaña. La primera, con el mismo alcance (23
mutantes), dio **5 muertos y 18 supervivientes**, y el diagnóstico fue el
mismo para casi todos:

1. **Cada suite solo ejecuta el código de SU servicio.** El guardián que
   compara las dos copias (R1/R2/R4) vive en la suite de la **raíz**, así
   que la herramienta no lo lanza al mutar el `orm_models.py` de un
   servicio. Mutaciones que el guardián caza en cada `init.sh` —cambiar
   `String(255)` por `String(256)` en una sola copia— sobrevivían aquí.
2. **La suite de cada servicio no miraba lo que ese servicio no usa.** En
   sv3 sobrevivían todas las mutaciones sobre `undo_log` y las siete
   `sigrid_*` (13 de los 18): son columnas que sv3 declara porque la base
   es una sola, pero que no lee nadie allí.
3. **En sv4 nadie probaba su copia del generador.** El test de `initialize()`
   (R8) compara lo ejecutado contra `ddl_complementario()` del **mismo**
   módulo: si el generador se estropea, los dos lados de la comparación
   cambian a la vez y el test sigue en verde. Es una tautología, y la
   mutación la destapó.

En lugar de justificar los 18 como equivalentes —que en parte lo eran, por
(1)— se taparon los huecos, porque describían algo que sí importa: el ORM
tiene que describir la BBDD real, columna a columna, en las dos copias.

- `services/partes-persistencia/tests/test_f010_r6_ddl_complementario.py`:
  DDL literal completo de `undo_log` y de las siete `sigrid_*`,
  autoincremento de las claves primarias, valores por defecto de Python
  (`extra_auto`, `es_incidencia`, `undone`) y orden alfabético de los
  índices.
- `services/partes-front/tests/test_f010_r6_ddl_complementario_sv4.py`
  (nuevo): las mismas propiedades sobre **la copia de sv4**, que es la que
  ejecuta el portal al arrancar.

Resultado: **23/23 muertos, 0 supervivientes**, y 11 tests más que sí
comprueban el esquema en vez de darlo por bueno.
