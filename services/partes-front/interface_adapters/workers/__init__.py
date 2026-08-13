# interface_adapters/workers/__init__.py
"""Adaptadores de entrada por COLA del portal (sv4).

Hoy solo el consumidor de `q-transfer-result`, que cierra el lazo de la
aprobacion asincrona volcando el veredicto de sv5 en `parte_registros`.
"""
