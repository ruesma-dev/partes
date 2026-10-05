<!-- progress/spec_F-030.md -->
# F-030 · Resumen de la spec para el humano (versión 2, con tus decisiones)

Spec: `specs/F-030-recurso-sin-ficha/` (requirements 116 líneas, design 232,
15 tareas). Sigue en `spec_ready`; DA1–DA9 **aprobadas** el 2026-10-05 y
marcadas así en design §8, con tus palabras citadas.

## Qué cambia respecto a la versión anterior

1. **DA1, el proceso es el mismo que con empleados.** Cuando una persona no
   tiene ficha de empleado, su «ficha» es su recurso (`MO/`, con DNI en
   `res.cif` y sin ficha enlazada). Se casa con **el mismo código** que hoy
   casa empleados: primero DNI (con el cero completado) y, si no hay DNI o no
   casa, alias (solo existen para fichas de empleado) y **nombre**, con el
   mismo umbral y las mismas reglas de empate. En el nombre compiten juntas
   las fichas de empleado y las de recurso: gana la mejor y un empate entre
   dos personas va a revisión. El formato «APELLIDOS, NOMBRE» de los recursos
   ya lo entiende el algoritmo (compara palabras sin orden y quita la coma).
   No se duplica nada: no se toca la lista cerrada ni `text_match.py`.
2. **DA2, nada del modelo cambia.** La línea se guarda en el recurso como
   siempre y no hay columnas nuevas. Solo se usan dos valores nuevos en el
   campo de método que ya existe, `recurso_dni` y `recurso_nombre`: son
   imprescindibles porque, sin ficha, es lo único que distingue a esta
   persona de un trabajador sin casar.
3. **DA4, portal al mínimo.** Sin badge ni plantillas: la persona se ve como
   cualquier trabajador casado. Se queda un helper que la cuenta como casada
   y el filtro que la saca de la pantalla de conciliación, porque confirmar
   allí le pondría una ficha ajena y le quitaría el recurso aunque se haya
   casado por nombre.
4. Recursos que ahora quedan **fuera**: los que apuntan a una ficha (casan
   por ella, como hoy; así desaparece el riesgo anterior de 3 omisiones en
   sv5) y los que no tienen `res.cif` (2 en la 28: casarlos obligaría a
   cambiar el conciliador).
5. El completado del cero del DNI se hace al leer el parte, no en
   `text_match.py` (ese fichero es idéntico en sv3 y sv4).

Lo demás (DA3, DA5–DA9), como lo recomendé: sin revisión por esto, motivos
no válidos siguen a alias y nombre, lista cerrada intacta, reproceso manual
de los 2 partes de Porsan y cuenta analítica 0 en Porsan sin tocar sv5
(hoy ya sale 0; queda fijado con un test).

## Riesgo nuevo que importa

**Nombre mal casado**: igual que con fichas de empleado, dos personas que
comparten apellidos pueden rozar el umbral y las horas irían a otra persona
en Sigrid. Lo mitigan el empate a revisión, el umbral estricto y el «Leído:
…» del portal junto al nombre del recurso.

## Despliegue y pruebas manuales (sin cambios)

sv3 → sv4 en la misma sesión; sv5 no se despliega. Luego M3: reprocesar los
2 partes de Porsan (papelera + mover sus correos a la bandeja de entrada no
leídos) y M4: preflight con `[registro] cuentas obra=0724 ok=0
recurso_sin_cuenta=N` en los logs de sv5. Detalle en design §9.
