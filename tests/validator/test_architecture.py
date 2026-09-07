"""La regla de dependencia de G5: la flecha apunta siempre hacia adentro.

Es lo que hace que las reglas se prueben con datos. Sin esta comprobación, un import cómodo desde el
dominio hacia un adaptador pasaría desapercibido y arrastraría disco a las pruebas de reglas.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[2] / "validator" / "agentic_validator"
DOMAIN = PACKAGE / "domain"
ADAPTERS = PACKAGE / "adapters"

# Módulos de entrada y salida que el dominio no puede tocar: si los necesita, la regla no es pura.
FORBIDDEN_IN_DOMAIN = ("pathlib", "subprocess", "json", "yaml", "jsonschema", "os")


def _modules(directory: Path) -> list[Path]:
    return sorted(path for path in directory.rglob("*.py") if path.name != "__init__.py")


def test_el_dominio_no_importa_adaptadores():
    for module in _modules(DOMAIN):
        text = module.read_text(encoding="utf-8")
        assert "agentic_validator.adapters" not in text, module.name


def test_el_dominio_no_importa_nada_de_entrada_ni_salida():
    for module in _modules(DOMAIN):
        lines = [line.strip() for line in module.read_text(encoding="utf-8").splitlines()]
        imports = [line for line in lines if line.startswith(("import ", "from "))]
        for forbidden in FORBIDDEN_IN_DOMAIN:
            offending = [line for line in imports if line.startswith((f"import {forbidden}", f"from {forbidden}"))]
            assert not offending, f"{module.name}: {offending}"


# Infra de adaptador compartida entre hermanos del mismo componente: parsear un frontmatter no es una
# implementación de puerto, es un ayudante. G5 lo permite explícitamente (DRY, G2); lo que prohíbe es
# que un adaptador importe la implementación de otro.
SHARED_ADAPTER_HELPERS = frozenset({"frontmatter"})


def test_ningun_adaptador_importa_a_otro_salvo_los_ayudantes_compartidos():
    for module in _modules(ADAPTERS):
        text = module.read_text(encoding="utf-8")
        others = [
            other.stem
            for other in _modules(ADAPTERS)
            if other != module
            and other.stem not in SHARED_ADAPTER_HELPERS
            and f"agentic_validator.adapters.{other.stem}" in text
        ]
        assert not others, f"{module.name} importa {others}"


@pytest.mark.parametrize("module", _modules(DOMAIN) + _modules(ADAPTERS) + [PACKAGE / "cli.py"])
def test_ningun_modulo_del_validador_supera_el_umbral_de_revision(module: Path):
    # AGENTS.md: ~300 líneas es señal de que el módulo acumula más de una responsabilidad.
    assert len(module.read_text(encoding="utf-8").splitlines()) <= 300, module.name
