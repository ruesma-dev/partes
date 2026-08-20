<!-- progress/mutacion_F-017.md -->
# F-017 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-017` el 2026-08-20 16:44.

## Alcance

Origen del diff: **rama** (`4ca131c1f13f953e7f5811b5cf9075ff0ab17ece` .. `feature/F-017-identidad-easy-auth`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/interface_adapters/web/app.py` | 143 |
| `services/partes-front/interface_adapters/web/identidad.py` | 257 |
| **Total** | **400** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 31 |
| Mutantes evaluados | 31 |
| Muertos | 19 |
| Supervivientes | 1 |
| Timeouts | 11 |
| Tiempo total | 234.6 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/interface_adapters/web/identidad.py:136` [logico]

- Original: `if isinstance(tipo, str) and isinstance(valor, str):`
- Mutado:   `if isinstance(tipo, str) or isinstance(valor, str):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

## Timeouts

- `services/partes-front/interface_adapters/web/app.py:470` services/partes-front/interface_adapters/web/app.py:470 [booleano] app.state.identidad_anunciada = False -> app.state.identidad_anunciada = True
- `services/partes-front/interface_adapters/web/app.py:509` services/partes-front/interface_adapters/web/app.py:509 [booleano] app.state.easy_auth_visto = True                  # senal B -> app.state.easy_auth_visto = False                  # senal B
- `services/partes-front/interface_adapters/web/app.py:510` services/partes-front/interface_adapters/web/app.py:510 [comparacion] elif origen == "sin-identidad-desplegado": -> elif origen != "sin-identidad-desplegado":
- `services/partes-front/interface_adapters/web/app.py:524` services/partes-front/interface_adapters/web/app.py:524 [not] if not app.state.identidad_anunciada: -> if app.state.identidad_anunciada:
- `services/partes-front/interface_adapters/web/app.py:525` services/partes-front/interface_adapters/web/app.py:525 [booleano] app.state.identidad_anunciada = True -> app.state.identidad_anunciada = False
- `services/partes-front/interface_adapters/web/identidad.py:53` services/partes-front/interface_adapters/web/identidad.py:53 [entero] ACTOR_MAX_LEN = 120          # la columna mas estrecha: undo_log.actor -> ACTOR_MAX_LEN = 121          # la columna mas estrecha: undo_log.actor
- `services/partes-front/interface_adapters/web/identidad.py:94` services/partes-front/interface_adapters/web/identidad.py:94 [comparacion] limpio = "".join(c for c in str(valor) if c.isprintable() or c == " ") -> limpio = "".join(c for c in str(valor) if c.isprintable() or c != " ")
- `services/partes-front/interface_adapters/web/identidad.py:108` services/partes-front/interface_adapters/web/identidad.py:108 [not] if not normalizado: -> if normalizado:
- `services/partes-front/interface_adapters/web/identidad.py:109` services/partes-front/interface_adapters/web/identidad.py:109 [booleano] return False -> return True
- `services/partes-front/interface_adapters/web/identidad.py:111` services/partes-front/interface_adapters/web/identidad.py:111 [logico] or normalizado == ACTOR_SIN_IDENTIDAD) -> and normalizado == ACTOR_SIN_IDENTIDAD)
- `services/partes-front/interface_adapters/web/identidad.py:117` services/partes-front/interface_adapters/web/identidad.py:117 [booleano] crudo = base64.b64decode(token, validate=True) -> crudo = base64.b64decode(token, validate=False)

