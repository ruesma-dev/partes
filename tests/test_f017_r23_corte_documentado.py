# tests/test_f017_r23_corte_documentado.py
"""R23: el corte de auditoría de F-017 está documentado, y bien.

Un test sobre documentación puede sonar a burocracia, así que conviene
decir qué protege exactamente. Dentro de un año, alguien va a mirar
`parte_documents` y va a ver un montón de `approved_by` a `NULL`. Sin este
apartado escrito, la lectura natural de eso es «el sistema no guarda quién
aprueba», y la reacción natural es abrir una incidencia — o peor, rellenar
esos huecos con algo. El apartado es lo que convierte un `NULL` sospechoso
en un dato con explicación.

Por eso no basta con comprobar que el apartado existe: se comprueba que
contiene **el criterio** (`autor IS NULL` ⇔ anterior a F-017), que explica
los dos marcadores reservados y que sigue reservado el hueco de la fecha
hasta que alguien despliegue.

Sin red y sin BBDD: solo lectura de los dos documentos.
"""

from __future__ import annotations

import pytest

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MAESTRO = RAIZ / "docs" / "referencia" / "partes-proyecto.md"
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"

MARCA_PENDIENTE = "⛔ PENDIENTE: fecha de despliegue"


@pytest.fixture(scope="module")
def maestro() -> str:
    return MAESTRO.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def corte(maestro: str) -> str:
    """El apartado «Corte de auditoría (F-017)», aislado."""
    inicio = maestro.index("Corte de auditoría (F-017)")
    resto = maestro[inicio:]
    fin = resto.find("\n## ")
    return resto if fin == -1 else resto[:fin]


# ====================================================================== #
# El apartado existe y dice lo que tiene que decir
# ====================================================================== #

def test_f017_r23_existe_el_apartado_del_corte(maestro: str) -> None:
    assert "Corte de auditoría (F-017)" in maestro


def test_f017_r23_el_criterio_del_corte_esta_escrito(corte: str) -> None:
    """Lo único que hay que recordar dentro de un año."""
    assert "IS NULL" in corte
    assert "anterior al despliegue de F-017" in corte


def test_f017_r23_explica_los_dos_marcadores_reservados(corte: str) -> None:
    """`local:…` y `sin-identidad` significan cosas MUY distintas.

    Confundirlos es lo que la enmienda del humano vino a evitar: uno dice
    «esto lo hizo un puesto de desarrollo» y el otro «la autenticación no
    está funcionando». Si el documento no los distingue, la distinción se
    pierde en cuanto nadie se acuerde.
    """
    assert "local:" in corte
    assert "sin-identidad" in corte
    assert "incidente" in corte.lower()


def test_f017_r23_dice_que_no_se_reescribio_nada(corte: str) -> None:
    """R22, por escrito: quien lea esto no debe intentar «arreglar» los
    `NULL` antiguos."""
    texto = corte.lower()
    assert "no se han tocado" in texto or "no se ha tocado" in texto
    assert "inventar una firma" in texto


def test_f017_r23_el_hueco_de_la_fecha_sigue_marcado(corte: str) -> None:
    """La fecha la pone quien despliega, y hasta entonces se ve el hueco.

    Cuando el despliegue ocurra, este test se pone rojo y obliga a
    actualizarlo: es deliberado. Un recordatorio que no molesta no
    recuerda nada.
    """
    assert MARCA_PENDIENTE in corte


def test_f017_r23_menciona_whoami(corte: str) -> None:
    """La forma de comprobar el corte sin escribir una fila."""
    assert "/whoami" in corte


def test_f017_r23_advierte_de_undo_log_actor(corte: str) -> None:
    """La excepción al criterio, dicha en voz alta.

    `undo_log.actor` no participa del corte porque no la escribe nadie.
    Callarlo dejaría el criterio con un agujero silencioso justo donde
    F-018 se va a apoyar.
    """
    assert "undo_log.actor" in corte


# ====================================================================== #
# La corrección del dato falso que había en §5.4
# ====================================================================== #

def test_f017_r23_ya_no_dice_que_la_jornada_lleve_default_reviewer(
        maestro: str) -> None:
    """§5.4 afirmaba que `created_by`/`updated_by` llevaban
    `DEFAULT_REVIEWER`. Era falso: llevaban `NULL`, porque esa variable
    nunca se configuró en `ca-sv4-front`."""
    assert "llevan hoy `DEFAULT_REVIEWER`" not in maestro


def test_f017_r23_se_explica_por_que_llevaban_null(maestro: str) -> None:
    inicio = maestro.index("### 5.4")
    seccion = maestro[inicio:maestro.index("### 5.5")]
    assert "NULL" in seccion
    assert "Easy Auth" in seccion


# ====================================================================== #
# La regla corta en ARCHITECTURE.md
# ====================================================================== #

def test_f017_r23_la_regla_esta_en_architecture() -> None:
    arquitectura = ARQUITECTURA.read_text(encoding="utf-8")
    assert "Identidad del portal (F-017" in arquitectura
    assert "_actor(request)" in arquitectura
    assert "anterior a F-017" in arquitectura
