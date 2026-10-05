<!-- progress/spec_F-030.md -->
# F-030 · Resumen de la spec para el humano

Spec: `specs/F-030-recurso-sin-ficha/` (requirements 102 líneas, design 250,
tasks 13 tareas). Estado `spec_ready`: **falta que apruebes DA1–DA9** antes
de implementar.

## Qué pasa hoy y por qué

sv3 casa primero el trabajador contra las fichas de empleado (`emp`) y llega
al recurso desde la persona. Si no hay ficha, la línea se queda sin persona
y sin recurso («Sin recurso»), aunque Sigrid tenga un recurso de alta cuyo
`res.cif` es ese DNI. Además, el DNI leído sin el cero inicial no casa nunca:
Sigrid guarda **siempre** 8 dígitos.

## Qué propone

1. **sv3**: el DNI leído se completa a 8 dígitos (con o sin el 0 da igual).
   Si no hay **ninguna** ficha con ese DNI, antes de probar el alias o el
   nombre, sv3 busca el recurso por `res.cif` entre los de la empresa del
   parte y de alta a su fecha. Si hay uno, el trabajador queda «casado por
   recurso»: sin ficha, con el DNI y el nombre del recurso de Sigrid y el
   método `recurso_dni`. El parte no va a revisión por eso.
2. El conciliador **no cambia**: con el DNI ya guardado elige el recurso por
   línea (empresa de la obra y alta a la fecha), como desde F-023, y aplica
   jornada, calendario y extras como a cualquiera.
3. **sv4**: esas personas se ven «Casado por recurso (sin ficha)» y salen de
   la pantalla de conciliación (donde casarlas por nombre soltaría su recurso).
4. **sv5**: sin código. Verifica el recurso igual que hoy y ya escribe cuenta
   analítica 0 en Porsan. Solo gana tests que lo fijan.

## Datos medidos en Sigrid (hoy, solo lectura)

- Quién entra por el camino nuevo (`res.cif` con DNI y ninguna ficha con ese
  DNI): **19 recursos en la empresa 1 y 6 en la 28**. Los otros 12 de la 28
  del recuento no tienen `cif`: 10 ya casan por su ficha (`conide`) y 2 no
  son identificables por DNI. 24 de esos recursos suman 1.289 líneas
  tecleadas a mano en 2026 (707 en la 1, 582 en la 28).
- Cuenta analítica en Porsan: **0 de 39** recursos de la 28 tienen cuenta en
  su ficha de horas y **0 de 5.123** líneas de 2026 de obras de la 28 llevan
  cuenta, aunque las 103 obras sí tienen cuentas en su centro. sv5 escribe
  hoy `caaide = 0` en la 28 (motivo «recurso sin cuenta», sin aviso).

## Decisiones (DA) y mi recomendación

| DA | Pregunta | Recomiendo |
|---|---|---|
| DA1 | ¿Casar también por nombre contra el recurso? | **No**, solo DNI. Un nombre mal casado escribe horas a otro en Sigrid; feature aparte si hace falta |
| DA2 | ¿Qué se guarda? | Ficha vacía, DNI y nombre del recurso, método `recurso_dni`. No tomar la ficha de `res.conide` (3 casos con otro DNI) ni crear columnas |
| DA3 | ¿Va a revisión? | **No** (el conciliador ya avisa si el recurso no vale a la fecha) |
| DA4 | ¿Tocar el portal? | **Sí**: badge propio y fuera de la cola de conciliación |
| DA5 | DNI con recurso de baja, de otra empresa o ambiguo | Seguir como hoy (alias y nombre): no cambia nada de lo que ya casa |
| DA6 | Lista cerrada de duplicación | **No tocar ninguna copia**: se usa `elegir_recurso` tal cual y el cero se arregla al leer |
| DA7 | DNI canónico | Completar a 8 solo `1–7 dígitos + letra`; arregla también el casado con ficha |
| DA8 | Partes ya entrados | El DNI leído no se guarda: **reprocesar a mano** los 2 de Porsan (papelera + correo de vuelta a la bandeja) |
| DA9 | Cuenta analítica en Porsan | **Sin código**: ya sale 0; se fija con test. Forzarlo por empresa sería feature aparte |

## Riesgos

- Un DNI mal leído que coincida con el de otra persona sin ficha se le
  imputaría a ella (mismo riesgo que con fichas); el portal enseña el nombre
  del recurso junto al leído para cazarlo.
- 3 recursos de la empresa 1 apuntan a una ficha con otro DNI: sv3 los casará
  y sv5 los **omitirá** con motivo. Falla seguro; se arregla en Sigrid.
- Más líneas con recurso significa más extras por jornada calculadas.
- Entre desplegar sv3 y sv4 estas personas se ven «Sin casar»: no tocarlas en
  conciliación durante ese rato.

## Despliegue y pruebas manuales

Orden **sv3 → sv4** en la misma sesión; sv5 no se despliega; sin cambio de
esquema. Después: M1 logs de arranque de sv3; M2 lectura en Sigrid de cuentas
de la 28 (debe dar 0); **M3** reprocesar los 2 partes de Porsan (marcar
pendiente si están aprobados, papelera, mover sus correos de `Procesados` a la
bandeja de entrada no leídos) y comprobar la persona sin ficha con recurso y
estado `ok`/`sin_parte`; **M4** abrir el modal de aprobación (solo lectura) y
ver en los logs de sv5 `[registro] cuentas obra=0724 ok=0
recurso_sin_cuenta=N`. Detalle exacto en design §9.

## Fuera

Nombre contra recursos, ficha desde `res.conide`, guardar el DNI leído,
re-casado automático de lo ya ingerido, alta manual o jornada de personas sin
ficha en el portal, regla «empresa sin analítica» en sv5, y los 2 recursos de
la 28 sin `cif` ni ficha.
