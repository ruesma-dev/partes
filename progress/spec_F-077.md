# F-077 · Resumen de la spec (spec-author, 2026-11-18)

Spec: `specs/F-077-sesame-directo-sin-pasarela/` (requirements 137/150, design 248/250, tasks
T1–T19). Rama `feature/F-077-sesame-directo-sin-pasarela`. Rigor `critico` (disparadores 1,
dinero, y 3, seguridad y datos personales). F-077 pasa a `spec_ready`, pendiente de aprobación.

## Qué propone

- **sv3** llama directamente a la API oficial de Sesame HR con el mismo mecanismo que
  sesame-api. Hay dos piezas nuevas en `infrastructure/sesame/`:
  - `SesameHrClient`: Bearer, solo GET, paginación `limit/page/lastPage`, reintentos 429/5xx
    con `Retry-After`.
  - `FestivosSesameHr`: índice DNI → empleado en memoria con TTL de 600 s, más un corte de 60 s
    tras un fallo de disponibilidad.
  - Las dos dan a `RefrescoFestivos` el mismo contrato `festivos(dni, ano)` que hoy, así que
    F-032 no cambia: ni la tabla, ni la cascada, ni la semántica 404/fallo/revisión.
- **sv4** ya no llama a Sesame:
  - se retiran su cliente, `SESAME_API_*`, `SESAME_CACHE_TTL_S`, `jornada_contrato` con su badge
    (nunca salía, 0/218 contratos) y `validar_datos_sesame.py`;
  - la tabla se lee con un interruptor nuevo, `FESTIVOS_SESAME_ENABLED`.
- **Herramienta de contraste**: lista los calendarios de Sesame HR (`/schedule/v1/holiday-calendar`);
  el token sale del entorno o se pide por consola, nunca por la línea de órdenes.
- **Infra**: secreto `SESAME-TOKEN` en el Key Vault y `sesame-token` en la app. El script
  `add_sesame_partes.ps1`:
  - cablea sv3 y después sv4 (solo el interruptor);
  - retira las variables viejas solo si existen.
- **Privacidad**: el test usa la `configure_logging` real y el cliente real sobre
  `MockTransport`, sin DNI, nombre, email, token ni id de empleado en logs ni en excepciones. Del
  listado de empleados solo se guarda en memoria el id, el DNI normalizado y si está activo.
- **Corrección de formato**: la descripción de F-077 dice que `/holidays` trae `daysOff`. En el
  código de sesame-api, cada fila de `/schedule/v1/holidays` trae `dayOff` (objeto) y `daysOff`
  es de `/holiday-calendar`. La spec sigue el código y acepta los dos.

## Decisiones para el humano (DA1–DA4 ya decididas el 2026-11-18)

| Decisión | Opciones | Recomendado |
|---|---|---|
| DA5 Normalización del DNI del índice | (A) `normalize_dni` de sv3 (la de `dni_norm` y del pipeline); (B) `norm_dni` de sesame-api | (A) |
| DA6 «No encontrado» | (A) DNI ausente de un índice bien cargado ⇒ sin fila y sin revisión; un 404 de festivos de un empleado conocido ⇒ fallo; (B) los dos ⇒ sin fila | (A) |
| DA7 Inactivos en el índice | (A) activos e inactivos; con DNI repetido, el activo (como sesame-api); (B) solo activos | (A) |
| DA8 Índice que falla a mitad | (A) todo o nada: no se guarda, cuenta como fallo y abre un corte de 60 s sin red; (B) índice parcial, como sesame-api (DNIs perdidos en silencio) | (A) |
| DA9 Cliente sesame de sv4 y su configuración | (A) quitarlo todo, incluidos `jornada_contrato` con su badge y `validar_datos_sesame.py`; (B) dejarlo muerto | (A) |
| DA10 Interruptor de la tabla en sv4 | (A) `FESTIVOS_SESAME_ENABLED` (defecto false), que fija el script; (B) leer siempre la tabla; (C) conservar `SESAME_API_*` solo como interruptor | (A) |
| DA11 Nombres | (A) `SESAME_BASE_URL`, `SESAME_TOKEN`, `SESAME_TIMEOUT_S` y `SESAME_FESTIVOS_MINIMOS`; secreto `SESAME-TOKEN` / `sesame-token`; (B) conservar `SESAME_API_TIMEOUT_S` | (A) |
| DA12 Token en la herramienta de contraste | (A) del entorno o `.env`, o pedido por consola sin eco, sin `--token`; (B) `--token` | (A) |
| DA13 URL en la infra versionada | (A) `$SESAME_BASE_URL` vacía en `00_vars` y el valor en el `.local`; (B) versionar la URL pública | (A) |
| DA14 Solo HTTPS | (A) sv3 y la herramienta rechazan una URL sin `https://`; (B) aceptar http | (A) |

## Lo que queda para el humano (design §7)

- **M0**: rotar el token (el `.env` de sesame-api estuvo en git) y, si Sesame lo permite, que
  sea de solo lectura; cargarlo como `SESAME-TOKEN` con `add_secrets_partes.ps1`.
- **M1–M2**: contraste e impacto.
- **M3–M6**: redespliegue apagado, encendido, portal y `-Quitar`.
- F-077 sustituye a M1–M7 y P0–P4 de F-032 (T28–T30 de F-032 quedan sin objeto; P5, RRHH,
  sigue). Actualizar el «pendiente» de F-032 en `features.json` le toca al líder.

## Lista cerrada de tests existentes que cambian

Está en design §4:
- sv3: se retiran 2, se reescribe `fixtures_sesame.py` y se adaptan 5;
- sv4: se retiran 4 y se adaptan 8;
- raíz: se retira `test_f032_infra_sesame.py` y lo sustituye `test_f077_infra_sesame.py`.
