<!-- progress/banco_F-058.md -->
# F-058 · T3: banco MB del líder (2026-10-25)

Banco fuera del repo (`scratchpad\bench`: `bateria.py`, `lanzar.ps1`, `corregir.py`), con el
código de la rama (`-Repo partes-wt-f058`, HEAD 0274b06), prompt `parte_trabajo_es` con el
párrafo de cabecera de DA9. Sin relectura (mide solo la lectura primaria y Gemini por separado).
OpenAI como en producción desde F-059 (página como imagen, `image_detail=high`); Gemini con el
PDF, como en la relectura de producción (no está en `PAGINA_COMO_IMAGEN_PROVEEDORES`). Claves
del Key Vault solo en el proceso; sin escrituras en ningún sistema. Sin nombres ni DNIs.

| Prueba | Qué | Resultado | Esperado (puerta DA9) |
|---|---|---|---|
| (a) | `paginas_sincab` × 2, `gpt-6.1-sol` | obra y fecha 12/12 (692 20/10; 678 21/10 y 22/10) | informativo (antes, como PDF y sin el párrafo: 0/12) |
| (b) | `paginas_control` × 2, `gpt-6.1-sol` | 4/4 (692 19/10, 678 20/10), igual que `control.jsonl` | sin empeorar |
| (c) | `paginas_sincab` × 1, `gemini-4-argon` | 6/6 | 6/6 |
| (d) | batería de F-051 (14 páginas × 3), `corregir.py` contra `verdad.json` | 42/42 perfectas, 21/21 difíciles, 123/123 filas, 0 errores, cabecera 42/42; 17,0 s y 0,0280 $ por parte | 42/42 |

Conclusión: ninguna de (b), (c) o (d) empeora; el párrafo de cabecera se queda (DA9).
