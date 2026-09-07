"""Se hace cargo de la instantánea de una unidad: lo que las reglas reciben y el fallo de no tenerla.

Todo lo que una regla necesita se lee del disco una sola vez y llega aquí como datos, de modo que las
reglas se prueban sin disco (T1). Quien lee es `adapters/reading.py`, y la única forma de que no haya
instantánea es que la unidad no exista: por eso el fallo vive junto al tipo que no se pudo construir.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class ValidatorError(Exception):
    """Excepción base del validador."""


class UnitNotFoundError(ValidatorError):
    """La carpeta indicada no existe o no es una unidad publicable."""


@dataclass(frozen=True)
class TextArtifact:
    """Un skill, un agente o un prompt: lo que el cliente lee de su frontmatter."""

    path: str
    """Ruta relativa dentro de la unidad."""
    expected_name: str
    """Nombre que impone la ruta: el directorio para un skill, el archivo para los otros dos."""
    frontmatter: dict | None = None
    error: str | None = None


@dataclass(frozen=True)
class EvalSuite:
    path: str
    content: dict | None = None
    error: str | None = None


@dataclass(frozen=True)
class UnitSnapshot:
    """Todo lo que las reglas necesitan de una unidad, leído una sola vez.

    Un campo `*_error` con valor significa que el archivo existe pero no se pudo interpretar; el
    contenido a `None` sin error significa que el archivo no está.
    """

    name: str
    """Nombre del directorio de la unidad."""
    repository: str
    """Repositorio que la aloja."""
    governance: dict | None = None
    governance_error: str | None = None
    manifest: dict | None = None
    manifest_error: str | None = None
    skills: tuple[TextArtifact, ...] = ()
    agents: tuple[TextArtifact, ...] = ()
    prompts: tuple[TextArtifact, ...] = ()
    mcp: dict | None = None
    mcp_error: str | None = None
    hooks: dict | None = None
    hooks_error: str | None = None
    eval_suites: tuple[EvalSuite, ...] = ()
    files: tuple[str, ...] = field(default_factory=tuple)
    """Todas las rutas relativas de la unidad, para las reglas de layout y de presencia."""
    text_contents: dict[str, str] = field(default_factory=dict)
    """Contenido de los archivos de texto de la unidad, para las reglas de higiene. Nadie lo muta."""

    @property
    def text_artifacts(self) -> tuple[TextArtifact, ...]:
        return self.skills + self.agents + self.prompts

    @property
    def has_hooks(self) -> bool:
        return self.hooks is not None or self.hooks_error is not None

    @property
    def has_mcp(self) -> bool:
        return self.mcp is not None or self.mcp_error is not None

    def permissions(self, key: str) -> tuple[str, ...]:
        """Una de las tres listas de permisos declaradas, vacía si el gobierno no se pudo leer."""
        declared = (self.governance or {}).get("permissions") or {}
        values = declared.get(key)
        return tuple(values) if isinstance(values, list) else ()
