<!-- progress/mutacion_F-010.md -->
# F-010 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-010` el 2026-08-18 21:37.

## Alcance

Origen del diff: **rama** (`716a4f717f28571ef5987c586d69ac6d31d5035f` .. `feature/F-010-resincronizar-orm-models`).

| Fichero | Líneas en alcance |
|---|---|
| `services/partes-front/infrastructure/database/orm_models.py` | 113 |
| `services/partes-front/infrastructure/database/parte_repository.py` | 24 |
| `services/partes-persistencia/infrastructure/database/orm_models.py` | 106 |
| `services/partes-persistencia/infrastructure/database/sqlalchemy_parte_repository.py` | 14 |
| **Total** | **257** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 23 |
| Mutantes evaluados | 23 |
| Muertos | 5 |
| Supervivientes | 18 |
| Timeouts | 0 |
| Tiempo total | 67.1 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/partes-front/infrastructure/database/orm_models.py:251` [booleano]

- Original: `Boolean, nullable=False, default=False, server_default="false"`
- Mutado:   `Boolean, nullable=True, default=False, server_default="false"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/partes-front/infrastructure/database/orm_models.py:251` [booleano]

- Original: `Boolean, nullable=False, default=False, server_default="false"`
- Mutado:   `Boolean, nullable=False, default=True, server_default="false"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/partes-front/infrastructure/database/orm_models.py:344` [logico]

- Original: `for indice in sorted(tabla.indexes, key=lambda i: i.name or ""):`
- Mutado:   `for indice in sorted(tabla.indexes, key=lambda i: i.name and ""):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/partes-front/infrastructure/database/orm_models.py:346` [booleano]

- Original: `str(CreateIndex(indice, if_not_exists=True).compile(dialect=dialecto))`
- Mutado:   `str(CreateIndex(indice, if_not_exists=False).compile(dialect=dialecto))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/partes-persistencia/infrastructure/database/orm_models.py:221` [entero]

- Original: `sigrid_registrado_at_utc: Mapped[str | None] = mapped_column(String(64))`
- Mutado:   `sigrid_registrado_at_utc: Mapped[str | None] = mapped_column(String(65))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/partes-persistencia/infrastructure/database/orm_models.py:222` [entero]

- Original: `sigrid_registrado_by: Mapped[str | None] = mapped_column(String(255))`
- Mutado:   `sigrid_registrado_by: Mapped[str | None] = mapped_column(String(256))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/partes-persistencia/infrastructure/database/orm_models.py:225` [entero]

- Original: `sigrid_parte_cod: Mapped[str | None] = mapped_column(String(64))`
- Mutado:   `sigrid_parte_cod: Mapped[str | None] = mapped_column(String(65))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/partes-persistencia/infrastructure/database/orm_models.py:226` [entero]

- Original: `sigrid_motivo: Mapped[str | None] = mapped_column(String(255))`
- Mutado:   `sigrid_motivo: Mapped[str | None] = mapped_column(String(256))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/partes-persistencia/infrastructure/database/orm_models.py:290` [booleano]

- Original: `id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)`
- Mutado:   `id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/partes-persistencia/infrastructure/database/orm_models.py:291` [entero]

- Original: `created_at_utc: Mapped[str] = mapped_column(String(40), nullable=False)`
- Mutado:   `created_at_utc: Mapped[str] = mapped_column(String(41), nullable=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/partes-persistencia/infrastructure/database/orm_models.py:291` [booleano]

- Original: `created_at_utc: Mapped[str] = mapped_column(String(40), nullable=False)`
- Mutado:   `created_at_utc: Mapped[str] = mapped_column(String(40), nullable=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/partes-persistencia/infrastructure/database/orm_models.py:292` [entero]

- Original: `action: Mapped[str] = mapped_column(String(40), nullable=False)`
- Mutado:   `action: Mapped[str] = mapped_column(String(41), nullable=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/partes-persistencia/infrastructure/database/orm_models.py:292` [booleano]

- Original: `action: Mapped[str] = mapped_column(String(40), nullable=False)`
- Mutado:   `action: Mapped[str] = mapped_column(String(40), nullable=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/partes-persistencia/infrastructure/database/orm_models.py:293` [booleano]

- Original: `description: Mapped[str] = mapped_column(Text, nullable=False)`
- Mutado:   `description: Mapped[str] = mapped_column(Text, nullable=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/partes-persistencia/infrastructure/database/orm_models.py:294` [booleano]

- Original: `payload: Mapped[str] = mapped_column(Text, nullable=False)`
- Mutado:   `payload: Mapped[str] = mapped_column(Text, nullable=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/partes-persistencia/infrastructure/database/orm_models.py:295` [booleano]

- Original: `undone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)`
- Mutado:   `undone: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/partes-persistencia/infrastructure/database/orm_models.py:295` [booleano]

- Original: `undone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)`
- Mutado:   `undone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/partes-persistencia/infrastructure/database/orm_models.py:344` [logico]

- Original: `for indice in sorted(tabla.indexes, key=lambda i: i.name or ""):`
- Mutado:   `for indice in sorted(tabla.indexes, key=lambda i: i.name and ""):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

