"""Qué se puede retomar con lo que hay guardado: las reglas, con datos (T1)."""

from __future__ import annotations

from authoring_core.domain.git_state import Action
from authoring_core.domain.intent import interpret


def test_sin_nada_guardado_no_hay_nada_pendiente():
    assert interpret(None, None).pending is False
    assert interpret("", "").pending is False


def test_una_accion_y_una_unidad_guardadas_se_recuperan():
    intent = interpret("fix", "demo-unidad")
    assert intent.pending and intent.action is Action.MODIFY and intent.unit == "demo-unidad"


def test_una_accion_sin_unidad_sigue_siendo_algo_pendiente():
    # El autor eligió qué hacer aunque todavía no sobre qué, y esa mitad no hay que repetirla.
    intent = interpret("feat", None)
    assert intent.pending and intent.action is Action.CREATE and intent.unit is None


def test_cada_accion_valida_se_reconoce():
    for guardada, esperada in (("feat", Action.CREATE), ("fix", Action.MODIFY), ("deprecate", Action.DEPRECATE)):
        assert interpret(guardada, "u").action is esperada, guardada


def test_una_accion_corrupta_no_se_da_por_buena_y_se_dice_por_que():
    # Llevar el diálogo por un camino que el autor no eligió es peor que volver a preguntárselo.
    intent = interpret("borrar-todo", "demo-unidad")
    assert intent.pending is False
    assert "borrar-todo" in intent.message and "feat" in intent.message


def test_una_accion_corrupta_conserva_la_unidad_para_poder_mencionarla():
    assert interpret("basura", "demo-unidad").unit == "demo-unidad"
