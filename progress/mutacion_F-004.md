<!-- progress/mutacion_F-004.md -->
# F-004 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-004` el 2026-08-18 15:53.

## Alcance

Origen del diff: **rama** (`9772ba49bbb820698f7b0a79b9a7eb60ee148097` .. `feature/F-004-congelar-aprobados`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/application/services/congelacion.py` | 170 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 255 |
| `services/partes-front/interface_adapters/web/app.py` | 56 |
| **Total** | **481** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 54 |
| Mutantes evaluados | 54 |
| Muertos | 53 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Tiempo total | 678.9 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/interface_adapters/web/app.py:929` [entero]

- Original: `congeladas = 0`
- Mutado:   `congeladas = 1`

#### Análisis (completado por el implementer, 2026-08-18)

**Decisión: mutante EQUIVALENTE, justificado. No se añade test (no existe
ninguno capaz de distinguirlo sin cambiar el código).**

La línea es la inicialización de la variable justo antes del `try` de
`POST /api/empleado/reasignar`:

```python
updated = 0
congeladas = 0          # <- la línea mutada
leidos: list[str] = []
try:
    if isinstance(registro_ids_in, list) and registro_ids_in:
        updated, congeladas = repository.reassign_empleado_by_registro_ids(...)
    elif registro_id is not None:
        updated, congeladas = repository.reassign_empleado_by_leido(...)
    elif worker_key:
        updated, leidos, congeladas = repository.reassign_empleado_by_worker_key(...)
    elif nombre_leido_in:
        updated, congeladas = repository.reassign_empleado_by_leido(...)
    else:
        return JSONResponse({...}, status_code=400)   # sin `congeladas`
except Exception:
    return JSONResponse({...}, status_code=500)       # sin `congeladas`
return JSONResponse({..., "congeladas": congeladas, ...})
```

**Por qué ningún test lo caza:** el valor inicial nunca llega a la
respuesta. Los CUATRO caminos que alcanzan el `return` final reasignan
`congeladas` con lo que devuelve el repositorio; el quinto (ningún
selector en el cuerpo) sale por un 400 que no lleva ese campo, y una
excepción sale por un 500 que tampoco. No hay ejecución observable en la
que se distinga `0` de `1`, así que ningún test podría matarlo salvo
introduciendo un camino que hoy no existe.

**Y no se quita la inicialización**, que sería la otra forma de eliminar
el superviviente: si mañana se añade un quinto selector y se olvida
asignar `congeladas`, con la inicialización la respuesta dice `0` (un
dato malo, visible en un test) y sin ella el endpoint revienta con un
`NameError` en producción. La misma variable `updated` de al lado —código
anterior a F-004— sigue exactamente el mismo patrón.

**Los otros cuatro supervivientes de la campaña anterior SÍ eran huecos
reales y están tapados** (`progress/impl_F-004.md`, sección «Análisis del
superviviente»): el `ok` de los dos borrados masivos (`n > 0` mutado a
`n >= 0` y a `n > 1`) y el payload de la celda de la matriz (`h` y `p`)
no los comprobaba ningún test; ahora los cazan
`test_f004_r13_si_toda_la_obra_esta_congelada_la_respuesta_no_dice_ok`,
`test_f004_r13_si_todas_las_lineas_estan_congeladas_no_dice_ok`,
`test_f004_r15_la_celda_sigue_llevando_horas_tipo_y_partida` y
`test_f004_r15_una_linea_sin_partida_ni_horas_no_inventa_valores`.

