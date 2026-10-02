-- infra/sql/01_dedicacion_lectura.sql
--
-- F-019 (R25, DA1, DA3): permiso de LECTURA de la aplicacion de dedicacion
-- sobre la bandeja de salida `dedicacion_bandeja` de la base `partes`, y
-- sobre nada mas.
--
-- Lo ejecuta EL HUMANO (nunca un agente ni un servicio), con un usuario
-- administrador de la base `partes`, DESPUES de desplegar sv3 y sv4 (son
-- ellos quienes crean la tabla al arrancar) y comprobar M1:
--
--   psql "host=<servidor> dbname=partes user=<admin> sslmode=require" -v rol=<rol_app_dedicacion> -f infra/sql/01_dedicacion_lectura.sql
--
-- `rol` es el rol de aplicacion que dedicacion YA usa en el servidor (DA3):
-- aqui no se crea ningun rol ni ninguna credencial. Idempotente: repetir
-- una concesion ya hecha no cambia nada.
--
-- Resultado esperado de las comprobaciones: true / false / false y la
-- version del servidor. Si la tercera sale true (en PostgreSQL < 15
-- cualquier rol puede crear en `public`), se AVISA y no se corrige aqui:
-- afecta a todo el servidor compartido y lo decide el humano (design §7).

\set ON_ERROR_STOP on

GRANT CONNECT ON DATABASE partes TO :"rol";
GRANT USAGE ON SCHEMA public TO :"rol";
GRANT SELECT ON TABLE public.dedicacion_bandeja TO :"rol";

-- Comprobaciones de lectura (no cambian nada).
SELECT has_table_privilege(:'rol', 'public.dedicacion_bandeja', 'SELECT') AS lee_la_bandeja;          -- debe ser true
SELECT has_table_privilege(:'rol', 'public.parte_registros', 'SELECT') AS lee_parte_registros;        -- debe ser false
SELECT has_schema_privilege(:'rol', 'public', 'CREATE') AS crea_en_public;                             -- false; si true, avisar
SELECT version();
