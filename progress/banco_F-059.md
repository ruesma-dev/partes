<!-- progress/banco_F-059.md -->
# F-059 · T9: banco M0–M3 del líder (2026-10-23)

Banco fuera del repo (`scratchpad\bench`: `bateria.py`, `lanzar.ps1`, `corregir.py`), con el
código de la rama (`-Repo partes-wt-f059`, commit 198fe85). Modo F-059: el adjunto lo prepara
`PaginaPdfImagenConversor` de la rama y el cliente OpenAI se crea con `image_detail="high"`.
Claves del Key Vault solo en el proceso; sin escrituras en ningún sistema. Modelo:
`gpt-6.1-sol`, esfuerzo por defecto. Sin nombres ni DNIs.

| Prueba | Qué | Resultado | Esperado |
|---|---|---|---|
| M0 | Los 22 PDF (6 sin cabecera, 2 de control, 14 de F-051) por el conversor | 22/22 `convertida`, giro 270; medidas y píxeles idénticos a `jpeg_derecho` del banco (diferencia máxima 0) | 22/22 |
| M1 | `paginas_sincab` × 2 | obra y fecha 12/12, iguales a las de `gemini-4-argon` (692 20/10, 678 21/10 y 22/10) | 12/12 (antes, como PDF: 0/12) |
| M2 | `paginas_control` × 2 | 4/4 (692 19/10, 678 20/10) | 4/4 |
| M3 | `paginas` (14) × 3, imagen frente a PDF, `corregir.py` contra `verdad.json` | imagen: 42/42 páginas perfectas, 21/21 difíciles, 123/123 filas, 0 errores, 21,5 s y 0,0274 $ por parte; PDF: 42/42, 21/21, 123/123, 0 errores, 22,7 s y 0,0262 $; cabecera con obra y fecha 42/42 en los dos | sin regresión |

Conclusión: M0–M3 se cumplen. Coste por parte +0,0012 $ (más tokens de entrada por la imagen
en `detail: high`); tiempo igual o algo menor. Queda M4 tras desplegar sv2 (humano).
