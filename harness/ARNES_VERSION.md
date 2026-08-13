<!-- harness/ARNES_VERSION.md -->
# Version del arnes instalada en este repositorio

Lo escribe `instalar_arnes.ps1`. **No lo edites a mano.**

| Dato | Valor |
|---|---|
| Version del arnes | `1.4.0` |
| Fecha de la version | 2026-08-13 |
| Instalado/actualizado el | 2026-08-13 13:22 |
| Modo | instalar |
| Origen | `arnes-base` |

Para actualizar a una version posterior, desde el repositorio `arnes-base`:

```powershell
.\instalar_arnes.ps1 -Destino "C:\Users\pgris\PycharmProjects\partes" -Modo actualizar
```

Antes de aceptar cambios, lee `GUIA_INSTALACION.md` en `arnes-base`: los
ficheros con marcas de adaptacion llevan contenido propio de este proyecto y
casi siempre hay que conservarlos, no sobrescribirlos.