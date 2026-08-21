<!-- progress/mutacion_F-017.md -->
# F-017 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-017` el 2026-08-21 09:06.

## Alcance

Origen del diff: **rama** (`4ca131c1f13f953e7f5811b5cf9075ff0ab17ece` .. `feature/F-017-identidad-easy-auth`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/interface_adapters/web/app.py` | 146 |
| `services/partes-front/interface_adapters/web/identidad.py` | 272 |
| `services/partes-front/interface_adapters/workers/resultado_consumer.py` | 44 |
| **Total** | **462** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 32 |
| Mutantes evaluados | 32 |
| Muertos | 24 |
| Supervivientes | 0 |
| Timeouts | 8 |
| Tiempo total | 208.7 s |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

## Timeouts

- `services/partes-front/interface_adapters/web/app.py:470` services/partes-front/interface_adapters/web/app.py:470 [booleano] app.state.identidad_anunciada = False -> app.state.identidad_anunciada = True
- `services/partes-front/interface_adapters/web/app.py:509` services/partes-front/interface_adapters/web/app.py:509 [booleano] app.state.easy_auth_visto = True                  # senal B -> app.state.easy_auth_visto = False                  # senal B
- `services/partes-front/interface_adapters/web/app.py:510` services/partes-front/interface_adapters/web/app.py:510 [comparacion] elif origen == "sin-identidad-desplegado": -> elif origen != "sin-identidad-desplegado":
- `services/partes-front/interface_adapters/web/app.py:524` services/partes-front/interface_adapters/web/app.py:524 [not] if not app.state.identidad_anunciada: -> if app.state.identidad_anunciada:
- `services/partes-front/interface_adapters/web/app.py:525` services/partes-front/interface_adapters/web/app.py:525 [booleano] app.state.identidad_anunciada = True -> app.state.identidad_anunciada = False
- `services/partes-front/interface_adapters/web/identidad.py:67` services/partes-front/interface_adapters/web/identidad.py:67 [entero] ACTOR_MAX_LEN = 120 -> ACTOR_MAX_LEN = 121
- `services/partes-front/interface_adapters/web/identidad.py:123` services/partes-front/interface_adapters/web/identidad.py:123 [booleano] return False -> return True
- `services/partes-front/interface_adapters/web/identidad.py:125` services/partes-front/interface_adapters/web/identidad.py:125 [logico] or normalizado == ACTOR_SIN_IDENTIDAD) -> and normalizado == ACTOR_SIN_IDENTIDAD)

