"""Tipos del validador: hallazgos, informe, riesgo y la instantánea de una unidad.

Sin I/O. Las reglas reciben una instantánea ya construida y devuelven hallazgos, así que se prueban
con datos (T1). Quien lee el disco es `reading.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# --- Nombres contrato del estándar ----------------------------------------------------------------

GOVERNANCE_FILE = "GOVERNANCE.json"
MANIFEST_FILE = ".claude-plugin/plugin.json"
MCP_FILE = ".mcp.json"
HOOKS_FILE = "hooks/hooks.json"
EVALS_DIR = "evals"

# El formato de plugin permite estos campos de primer nivel. El estándar no publica un esquema suyo:
# es formato ajeno y una copia derivaría (revisión del hito 1 §3).
ALLOWED_MANIFEST_FIELDS = frozenset(
    {"$schema", "name", "version", "description", "author", "repository", "license", "keywords", "homepage", "category"}
)

# Eventos que disparan en los dos clientes con la misma grafía, medidos el 7 de septiembre de 2026
# (D3). Uno fuera de la lista no falla en el cliente: no dispara nunca, y el autor cree que su control
# está activo. Avisa hasta que el lineamiento 04 §2 fije la lista.
PORTABLE_HOOK_EVENTS = frozenset(
    {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop", "SessionEnd"}
)

# Variables que expande el cliente, no credenciales: aparecen como ${VAR} y no se cuentan (medido en
# la demo anterior).
CLIENT_VARIABLES = frozenset(
    {"CLAUDE_PLUGIN_ROOT", "CLAUDE_PROJECT_DIR", "CLAUDE_PLUGIN_DATA", "workspaceFolder"}
)
PLUGIN_ROOT_PREFIX = "${CLAUDE_PLUGIN_ROOT}/"

# Tope de tiempo de un hook, en segundos. El lineamiento 04 §2 exige que exista un techo pero todavía
# no fija el número; éste es el del estándar hasta que lo haga. Un hook que tarde más cuelga la sesión
# de quien lo instaló sin que pueda saber por qué.
MAX_HOOK_TIMEOUT_SECONDS = 60

# Límite de la descripción que fija la especificación de skills. Es lo único que se carga en CADA
# petición, así que pasarse degrada la selección de todos los artefactos instalados.
MAX_DESCRIPTION_LENGTH = 1024

HOOK_TESTS_DIR = "hooks/tests"

DETERMINISTIC_ASSERT_TYPES = frozenset(
    {"contains", "icontains", "not-contains", "regex", "is-json", "javascript"}
)
REQUIRED_EVAL_CATEGORIES = frozenset({"happy_path", "edge_case", "negative"})
MIN_EVAL_CASES = 3

# Clasificaciones de dato que elevan el riesgo mínimo al nivel más alto (03 §1).
SENSITIVE_CLASSIFICATIONS = frozenset({"confidential", "restricted"})


class ValidatorError(Exception):
    """Excepción base del validador."""


class UnitNotFoundError(ValidatorError):
    """La carpeta indicada no existe o no es una unidad publicable."""


# --- Hallazgos e informe --------------------------------------------------------------------------


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Finding:
    severity: Severity
    rule: str
    """Identificador estable de la regla; aparece en el informe y es contrato."""
    where: str
    """Ruta relativa dentro de la unidad, o el nombre de la unidad si es de toda ella."""
    message: str
    """Qué está mal y por qué importa, en una frase."""

    @property
    def blocks(self) -> bool:
        return self.severity is Severity.ERROR


def error(rule: str, where: str, message: str) -> Finding:
    return Finding(Severity.ERROR, rule, where, message)


def warning(rule: str, where: str, message: str) -> Finding:
    return Finding(Severity.WARNING, rule, where, message)


class Verdict(Enum):
    COMPLIANT = 0
    NOT_COMPLIANT = 1
    UNREADABLE = 2

    @property
    def exit_code(self) -> int:
        return self.value


@dataclass(frozen=True)
class Report:
    unit: str
    findings: tuple[Finding, ...]

    @property
    def errors(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.blocks)

    @property
    def warnings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if not f.blocks)

    @property
    def verdict(self) -> Verdict:
        return Verdict.NOT_COMPLIANT if self.errors else Verdict.COMPLIANT


# --- Riesgo ----------------------------------------------------------------------------------------


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def rank(self) -> int:
        return {"low": 0, "medium": 1, "high": 2}[self.value]


# --- Instantánea de la unidad ----------------------------------------------------------------------


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
