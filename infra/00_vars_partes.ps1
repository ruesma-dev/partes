# 00_vars_partes.ps1
# Variables compartidas de la infraestructura de PARTES (Fase 1).
# Clon del patron de albaranes, pero:
#   - Recursos PROPIOS de partes en rg-partes-dev.
#   - REUTILIZA el ACR y el SERVIDOR PostgreSQL de albaranes (cross-RG).
#
# Dot-source este fichero en cada consola nueva ANTES de los demas scripts:
#     . .\00_vars_partes.ps1

# --- Identidad de la suscripcion (igual que albaranes) ----------------------
$Global:SUBSCRIPTION = "REDACTADO-VER-COPIA-LOCAL"
$Global:TENANT       = "REDACTADO-VER-COPIA-LOCAL"
$Global:LOCATION     = "spaincentral"

# --- Sufijo unico global ----------------------------------------------------
# STORAGE y KV comparten namespace MUNDIAL: deben ser unicos en todo Azure.
# Si la creacion falla por "already taken", cambia este sufijo por otro corto
# (minusculas/digitos).
$Global:SUFFIX = "pt7m3"               # <-- cambialo si algo sigue pillado

# --- Recursos PROPIOS de partes (rg-partes-dev) -----------------------------
$Global:RG       = "rg-partes-dev"
$Global:MI       = "id-partes-dev"                 # managed identity (la crea fase1)
$Global:LAW      = "log-partes-dev"
$Global:STORAGE  = "stpartes$SUFFIX"               # 3-24 minusc/digitos, unico
$Global:CAE      = "cae-partes-dev"
$Global:KV       = "kv-partes-$SUFFIX"             # 3-24, unico global

# --- REUTILIZADOS de albaranes (cross-RG; NO se crean aqui) -----------------
$Global:ACR      = "acralbaranesdev"               # registro de imagenes compartido
$Global:ACR_RG   = "rg-albaranes-dev"
$Global:PG       = "psql-albaranes-rs9k2"          # servidor PostgreSQL compartido
$Global:PG_RG    = "rg-albaranes-dev"
$Global:PG_DB    = "partes"                        # BBDD NUEVA en ese servidor
$Global:PG_ADMIN = "ruesmaadmin"                   # admin del servidor (lo conoces)

# --- Mapa de imagen por servicio (FUENTE UNICA: build y create lo comparten) -
# 'repo:tag' REAL que usa cada Container App en el ACR compartido. Si
# reconstruyes un servicio con nueva version, sube el tag AQUI y reconstruye
# SOLO ese servicio (asi build y app nunca discrepan).
$Global:IMG = [ordered]@{
  "sv1" = "sv1-partes:latest"     # webhook + Job de suscripcion (productor)
  "sv2" = "sv2-partes:latest"     # worker extraccion (Gemini)
  "sv3" = "sv3-partes:latest"     # worker persistencia (PG + SharePoint + Sigrid)
  "sv4" = "sv4-partes:latest"     # portal de revision
  "sv5" = "sv5-partes:latest"     # transfer: registro de partes en Sigrid
}

# --- Tags acens (OBLIGATORIOS por Azure Policy) -----------------------------
$Global:TAGS = @(
  "acens-customer=Construcciones-Ruesma",
  "acens-environment=dev",
  "acens-project=partes",
  "acens-responsable-so-app=pgris"
)

# --- PostgreSQL: IP de admin para reglas de firewall (reutiliza el servidor) -
$Global:MY_IP = "AUTO"                 # o "88.x.x.x"

# --- sigrid-api (informativo) ----------------------------------------------
$Global:SIGRID_BASE_URL = "https://func-sigridapi-dev-huyke.azurewebsites.net"

# --- Sesame HR (F-003, F-032, F-077): festivos reales por trabajador --------
# URL de la API oficial de Sesame HR de nuestra region (https://). sv3 la
# llama con un token Bearer, sin la pasarela sesame-api (F-077); sv4 no
# llama a Sesame, solo lee la tabla festivos_trabajador.
#
# VACIO A PROPOSITO (DA13 de F-077): la URL va SOLO en tu copia
# 00_vars_partes.local.ps1, no en esta, que se versiona (infra/README_partes.md
# dice cual es). Mientras siga vacia, sv3 y sv4 se despliegan APAGADOS y usan
# su calendario de festivos local, que es el comportamiento de siempre.
#
# Para encender (guia de F-077, M0-M4):
#   1. rota el token de Sesame HR y, si Sesame lo permite, hazlo de solo
#      lectura; cargalo en el Key Vault con add_secrets_partes.ps1
#      (secreto SESAME-TOKEN),
#   2. pon la URL en tu 00_vars_partes.local.ps1,
#   3. antes de encender, el contraste (M1-M2):
#      services/partes-persistencia/contrastar_festivos_sesame.py,
#   4. enciende con add_sesame_partes.ps1 (-Quitar apaga).
# Un trabajador sin festivos de Sesame NO bloquea el registro: el portal
# solo avisa y usa el calendario local.
$Global:SESAME_BASE_URL = ""

# Minimo de festivos de un ano para dar por completa la respuesta de Sesame
# (F-032, solo sv3): con menos, se conserva la fila guardada o el parte va
# a revision. 1 = basta con que haya alguno.
$Global:SESAME_FESTIVOS_MINIMOS = 1

Write-Host "[vars-partes] cargadas. RG=$RG  STORAGE=$STORAGE  KV=$KV" -ForegroundColor Cyan
Write-Host "[vars-partes] REUTILIZA ACR=$ACR ($ACR_RG)  PG=$PG/$PG_DB ($PG_RG)" -ForegroundColor Cyan
