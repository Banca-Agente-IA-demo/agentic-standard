"""La máquina del autor tiene lo que hace falta: las reglas, con datos (T1)."""

from __future__ import annotations

from authoring_core.domain.tooling import (
    MINIMUM_PYTHON,
    STATE_MISSING_TOOL,
    STATE_OK,
    ToolObservation,
    check,
)

COMPLETO = (
    ToolObservation("python", present=True, version=MINIMUM_PYTHON),
    ToolObservation("git", present=True),
    ToolObservation("gh", present=True, authenticated=True),
)


def test_con_todo_lo_necesario_se_puede_seguir():
    assert check(COMPLETO).state == STATE_OK and check(COMPLETO).can_continue


def test_cada_herramienta_ausente_se_nombra():
    for indice, nombre in ((1, "git"), (2, "gh")):
        observado = list(COMPLETO)
        observado[indice] = ToolObservation(nombre, present=False, how_to_fix=f"instala {nombre}")
        estado = check(tuple(observado))
        assert estado.state == STATE_MISSING_TOOL and estado.missing == (nombre,), nombre
        assert f"instala {nombre}" in estado.details


def test_una_version_del_interprete_por_debajo_del_minimo_se_señala_igual_que_una_ausencia():
    bajo = (MINIMUM_PYTHON[0], MINIMUM_PYTHON[1] - 1)
    observado = (ToolObservation("python", present=True, version=bajo), *COMPLETO[1:])
    estado = check(observado)
    assert estado.state == STATE_MISSING_TOOL and "python" in estado.missing
    assert "por debajo del mínimo" in estado.message


def test_una_version_por_encima_del_minimo_pasa():
    alto = (MINIMUM_PYTHON[0], MINIMUM_PYTHON[1] + 5)
    assert check((ToolObservation("python", present=True, version=alto), *COMPLETO[1:])).state == STATE_OK


def test_la_herramienta_de_la_plataforma_instalada_pero_sin_sesion_no_basta():
    # Sin sesión no puede leer nada de la plataforma, así que estar instalada no sirve de nada.
    observado = (*COMPLETO[:2], ToolObservation("gh", present=True, authenticated=False))
    estado = check(observado)
    assert estado.state == STATE_MISSING_TOOL and "sesión activa" in estado.message


def test_varias_cosas_que_faltan_se_nombran_todas():
    # Decir sólo la primera obliga al autor a arreglar de una en una.
    observado = (
        ToolObservation("python", present=True, version=(3, 9)),
        ToolObservation("git", present=False),
        ToolObservation("gh", present=True, authenticated=False),
    )
    assert check(observado).missing == ("python", "git", "gh")
