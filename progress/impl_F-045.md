<!-- progress/impl_F-045.md -->
# F-045 · Informe del implementer (BORRADOR: feature `blocked` en T4)

Estado: **blocked** el 2026-10-14. Motivo y opciones en `progress/current.md`
(un test fuera de design §5, `test_f037_r9_la_unica_clave_nueva_es_la_marca`,
choca con R27/design §4; y R25 necesita enlazar extra automática y base).
Este borrador guarda lo hecho y las trazas RED para que no se pierdan.

## Hecho

| Tarea | Commit | Contenido |
|---|---|---|
| T1 | `f500429` | `application/services/reparto_ponderado.py`: `PASOS`, `elegir_paso`, `Participante`, `repartir` (mayor resto en enteros de paso). `tests/test_f045_reparto_puro.py` (125 tests, rejilla de 99 combinaciones para R4). |
| T2 | `1ca0ab8` | `LineaDia`, `Ajuste`, `ResultadoDia`, `repartir_dia`. `tests/test_f045_reparto_dia.py` (36 tests `repartir_dia`). |
| T3 | `4c9d3ae` | `diferencias_ideal` + 11 tests `ideal` (incluido el caso real 0678/0704). |

Sin commitear (árbol del worktree): T4 (`tests/dobles.py`,
`fetch_registros_para_recurso`) y el código de T5 en `recurso_conciliador.py`
(sin sus tests todavía). Con ellos, sv3: 1345 passed, 7 failed (6 de §5 +
`test_f037_r9`); raíz: 487 passed, 3 skipped.

## Desviación (pendiente de decisión del humano, bloqueo 2)

`LineaDia` gana `extra_auto: bool = False` y `base_id: int | None = None`
(no están en design §4). Sin ellos, `diferencias_ideal` no puede quitar la
extra automática del peso de su obra ni informar su `registro_id`
(«−4 → 1,5» de T3). El conciliador calcularía `base_id` con
`pareja_extra.clave_pareja`, para lo que la lectura lleva `line_index` y
`empleado_line_no`.

## Fase RED (trazas reales)

### T1 · R1-R6 (`tests/test_f045_reparto_puro.py`)

Comando (desde `services/partes-persistencia`):
`C:/Users/pgris/PycharmProjects/partes/.venv/Scripts/python.exe -m pytest -q tests/test_f045_reparto_puro.py`

```
tests\test_f045_reparto_puro.py:18: in <module>
    from application.services.reparto_ponderado import (
E   ModuleNotFoundError: No module named 'application.services.reparto_ponderado'
=========================== short test summary info ===========================
ERROR tests/test_f045_reparto_puro.py
1 error in 0.46s
```

Verde tras el código: `125 passed in 0.29s`.

### T2 · R7-R23, R26 (`repartir_dia`)

Comando: `... -m pytest -q tests/test_f045_reparto_dia.py -k "repartir_dia"`.
Primero sin el módulo (ImportError de `Ajuste`); después con las dataclasses
y un `repartir_dia` vacío (`ResultadoDia(True, 0.5, (), 0, 0)`):

```
____________________ test_f045_r11_repartir_dia_ejemplo_1 _____________________
    def test_f045_r11_repartir_dia_ejemplo_1() -> None:
>       assert _aj(repartir_dia([_o(1, A, 10.0), _o(2, B, 4.0)], 8.0)) == {
            1: (5.5, 4.5), 2: (2.5, 1.5)}
E       assert {} == {1: (5.5, 4.5), 2: (2.5, 1.5)}
...
31 failed, 5 passed in 1.38s
```

(Los 5 que pasaban con el vacío son los que esperan «sin ajustes»: R8 extra
explícita, R9 8 h, R22 extra congelada, R23 residuo cero; y R29, que compara
el resultado consigo mismo.) Verde tras el código: `36 passed`.

### T3 · R25 (`diferencias_ideal`)

Comando: `... -m pytest -q tests/test_f045_reparto_dia.py -k "ideal"`, con
`diferencias_ideal` devolviendo `()`:

```
___________________ test_f045_r25_ideal_caso_real_0678_0704 ___________________
E       assert () == ((1, 8.0, 2.5...2, -4.0, 1.5))
E         Right contains 2 more items, first extra item: (1, 8.0, 2.5)
7 failed, 4 passed, 36 deselected in 0.70s
```

Verde tras el código: `172 passed` (T1-T3 juntos).

## Pendiente

T4 (enmienda del test según la decisión) → T5 (tests de integración
`test_f045_conciliar.py`, R20, R21, R24, R27-R30) → T6 (tabla antes → después
de §5) → T7-T12 (lo que no se toca, documentación, `azure-apps`, cobertura,
mutación completa, M1/M2, `init.sh`).

## Evidencias

PENDIENTE: la feature está bloqueada antes de T10 (cobertura y mutación).
