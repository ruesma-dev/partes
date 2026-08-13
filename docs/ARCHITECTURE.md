<!-- docs/ARCHITECTURE.md -->
# Arquitectura · [ADAPTAR: nombre-del-proyecto]

> Este documento es NORMATIVO: el spec-author diseña contra él y el
> reviewer rechaza lo que lo incumpla. Si no está aquí, no es un requisito.
> Rellenar las secciones [ADAPTAR] al instalar el arnés (ver
> GUIA_INSTALACION.md — puede redactarlo el propio Claude Code leyendo el
> repo, pero el humano DEBE revisarlo antes del primer uso real).

## Qué hace este proyecto

[ADAPTAR: 2-4 frases. Qué problema resuelve, quién lo usa, dónde se
despliega (microservicio Azure Container Apps / Function App / job...).]

## Capas y estructura

[ADAPTAR: hexagonal concreto de este repo. Qué hay en domain, application,
infrastructure. Si hay pipeline: lista de steps y su orden. Punto de
entrada y comandos disponibles.]

## Semántica de dominio imprescindible

[ADAPTAR: las 3-10 reglas que un agente NO puede inferir del código y que
son fuente de bugs si se ignoran. Ejemplos del estilo: significados de
campos ambiguos, invariantes de negocio, qué NO se puede sumar/mezclar,
convenciones de fechas/importes, campos que se llaman distinto en tablas
distintas.]

## Acceso a datos y sistemas externos

[ADAPTAR: contra qué sistemas habla el proyecto, con qué límites (solo
lectura, timeouts, paginación) y qué está PROHIBIDO tocar desde local.]

## Infra y despliegue

[ADAPTAR: dónde se despliega, con qué scripts de `infra/`, y las reglas
duras (tags fechados, secretos como secrets, .env nunca viaja).]
