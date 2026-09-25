"""La frontera exterior del sembrador: el JSON que envía el formulario de Port.

Por qué es un modelo pydantic y no una dataclass. Es el punto exacto donde los datos entran al
sistema de tipos desde fuera, y `model_validate()` falla en el sitio y con el nombre del campo en vez
de tres funciones más tarde (C2). Lo que viaja de aquí hacia dentro ya no se vuelve a validar.

Qué cubre y qué no. Comprueba la FORMA de lo que llegó: que el nombre tenga la forma permitida, que
el riesgo sea uno de los tres, que una unidad individual traiga su tipo. No comprueba nada del
contenido de la unidad, que no existe todavía, ni si el nombre está libre, que es una pregunta al
catálogo y no al payload.

Por qué colapsa `skill_1`, `skill_2`, ... en una lista. Port no representa una lista de textos como
un campo repetible: la muestra como un recuadro bloqueado con un lápiz que abre un editor de JSON, y
el autoservicio existe precisamente para que nadie escriba JSON en un formulario. La acción declara
por tanto un campo por posición, y la frontera es el sitio donde esa forma de formulario se convierte
en la forma de dominio.

Trazabilidad. AGENTS.md C2, T1 y P7. `create-unit-action.json` para los nombres de los campos;
documento 02 §1.1, §4, §5 y §6 del entregable E2 para las formas de los nombres.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, model_validator

from unit_seed.errors import InvalidRequestError
from unit_seed.unit_kinds import ArtifactType, RiskLevel, UnitForm

__all__ = ["UnitRequest", "MAX_ARTIFACTS_PER_TYPE"]

# Cuántos campos por tipo declara el formulario. Es la misma cifra que `create-unit-action.json`, y
# el único sitio del código que la conoce: si la acción crece, se cambia aquí.
MAX_ARTIFACTS_PER_TYPE = 10

# Las dos formas de nombre del estándar. El agente y el prompt admiten punto, que separa los niveles
# de la convención `{app}.{dominio}.{rol}`; el skill no, porque su forma la fija la especificación de
# Agent Skills y el nombre es además el de su directorio.
_HYPHENATED_NAME = r"^[a-z0-9]+(-[a-z0-9]+)*$"
_DOTTED_NAME = r"^[a-z0-9]+([.-][a-z0-9]+)*$"
_MAX_NAME_CHARS = 64

# De qué campo del formulario sale cada lista, y con qué forma de nombre se valida cada una.
_NUMBERED_FIELDS = {
    "skills": ("skill", _HYPHENATED_NAME),
    "agents": ("agent", _DOTTED_NAME),
    "prompts": ("prompt", _DOTTED_NAME),
    "mcp_servers": ("mcp_server", _HYPHENATED_NAME),
}


def _flatten_entity_fields(payload: dict) -> dict:
    """Convierte en cadena los campos que Port envía como entidad entera.

    Medido el 25 de septiembre de 2026 en la primera ejecución real: un campo con `format: entity`
    NO llega como el identificador, llega como el objeto completo.

        owner_team -> {"identifier": "19716830", "title": "squad-cnf-migration",
                       "blueprint": "githubTeam", "properties": {"slug": "squad-cnf-migration", ...}}
        repository -> {"identifier": "Banca-Agente-IA-demo/agents-modernization", ...}

    De ahí salen dos cosas. Del equipo se toma el **slug**, porque el identificador es el id numérico
    de GitHub y un manifiesto que dijera `"author": {"name": "19716830"}` no serviría para avisar a
    nadie. Del repositorio se toma el **identificador**, que ya es `organizacion/repositorio`.
    """
    flattened = dict(payload)
    for field, prefer_slug in (("owner_team", True), ("repository", False)):
        value = flattened.get(field)
        if not isinstance(value, dict):
            continue
        if prefer_slug:
            slug = value.get("properties", {}).get("slug") or value.get("title")
            flattened[field] = slug or value.get("identifier", "")
        else:
            flattened[field] = value.get("identifier", "")
    return flattened


def _collapse_numbered_fields(payload: dict) -> dict:
    """Convierte `skill_1`, `skill_2`, ... en la lista `skills`, y lo mismo con los otros tres."""
    collapsed = dict(payload)
    for target, (prefix, _) in _NUMBERED_FIELDS.items():
        if target in collapsed:
            continue
        names = [collapsed.get("%s_%d" % (prefix, position))
                 for position in range(1, MAX_ARTIFACTS_PER_TYPE + 1)]
        collapsed[target] = tuple(str(name).strip() for name in names
                                  if name is not None and str(name).strip())
    return collapsed


class UnitRequest(BaseModel):
    """Lo que el formulario recogió. Nada aquí se deriva: todo lo tecleó o lo eligió una persona."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    name: str = Field(pattern=_HYPHENATED_NAME, max_length=_MAX_NAME_CHARS)
    description: str = Field(min_length=1)
    owner_team: str = Field(min_length=1)
    team_mailbox: str = Field(min_length=1)
    risk_level: RiskLevel
    unit_form: UnitForm
    artifact_type: ArtifactType | None = None
    skills: tuple[str, ...] = ()
    agents: tuple[str, ...] = ()
    prompts: tuple[str, ...] = ()
    mcp_servers: tuple[str, ...] = ()
    mcp_accountable_team: str = ""
    has_hooks: bool = False
    repository: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def _normalize_port_shape(cls, payload: object) -> object:
        """Adapta lo que envía el formulario a la forma del dominio.

        Son dos diferencias de forma, las dos del lado de Port, y las dos se resuelven aquí porque
        esta es la frontera: hacia dentro ya viaja la forma de dominio.
        """
        if not isinstance(payload, dict):
            return payload
        return _collapse_numbered_fields(_flatten_entity_fields(payload))

    @model_validator(mode="after")
    def _check_artifact_names(self) -> UnitRequest:
        """Cada nombre de artefacto cumple la forma de su tipo, y ninguno se repite dentro de él."""
        for target, (prefix, pattern) in _NUMBERED_FIELDS.items():
            names = getattr(self, target)
            if len(set(names)) != len(names):
                raise InvalidRequestError(
                    "hay nombres repetidos en %s: %s" % (prefix, ", ".join(names)))
            for name in names:
                if len(name) > _MAX_NAME_CHARS or not re.fullmatch(pattern, name):
                    raise InvalidRequestError(
                        "el nombre %r no tiene la forma admitida para %s" % (name, prefix))
        return self

    @model_validator(mode="after")
    def _check_individual_form(self) -> UnitRequest:
        """Una unidad individual declara su tipo, y su artefacto se llama como ella."""
        if self.unit_form is not UnitForm.INDIVIDUAL:
            return self
        if self.artifact_type is None:
            raise InvalidRequestError("una unidad individual necesita el tipo de artefacto")
        return self

    @model_validator(mode="after")
    def _check_mcp_accountability(self) -> UnitRequest:
        """Si hay servidores MCP, alguien del banco responde por ellos."""
        if self.mcp_servers and not self.mcp_accountable_team.strip():
            raise InvalidRequestError(
                "los servidores MCP declarados necesitan un equipo responsable")
        return self
