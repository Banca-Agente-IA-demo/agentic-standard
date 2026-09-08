"""Se hace cargo de mirar el repositorio del autor. Sólo lee, nunca escribe.

Los únicos comandos que el asistente tiene permitido ejecutar contra el repositorio están en el plan:
`fetch`, `switch -c`, `add`, `commit` y `push` de la rama de trabajo actual. Aquí no se usa ninguno de
ellos, porque clasificar no es actuar: todo lo de este módulo es lectura.

El ejecutor se recibe por parámetro para que las pruebas no necesiten un repositorio de verdad donde
no aporta nada (T4).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from authoring_core.domain.git_state import MAIN_BRANCH, Observation

MANIFEST_GLOB = "**/.claude-plugin/plugin.json"
GIT_TIMEOUT_SECONDS = 30
DETACHED_HEAD = "HEAD"


class GitUnavailable(RuntimeError):
    """No se pudo preguntar a git: no está, o el directorio no es un repositorio."""


def run_git(args: list[str], cwd: Path | None = None) -> str:
    """Ejecuta git y devuelve su salida, o levanta si no se pudo preguntar."""
    try:
        completed = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=cwd,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as failure:
        raise GitUnavailable(str(failure)) from failure
    if completed.returncode != 0:
        lines = (completed.stderr or "").strip().splitlines()
        raise GitUnavailable(lines[-1] if lines else f"git terminó con código {completed.returncode}")
    return completed.stdout.strip()


def _quiet(args: list[str], cwd: Path | None, default: str = "") -> str:
    """Lo que git responda, o el valor por defecto si la pregunta no tiene respuesta aquí."""
    try:
        return run_git(args, cwd)
    except GitUnavailable:
        return default


def _units(root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Los nombres de las unidades del repositorio y los manifiestos que no se pudieron leer."""
    names: list[str] = []
    unreadable: list[str] = []
    for manifest in sorted(root.glob(MANIFEST_GLOB)):
        try:
            names.append(json.loads(manifest.read_text(encoding="utf-8"))["name"])
        except (json.JSONDecodeError, KeyError, TypeError, OSError):
            unreadable.append(manifest.relative_to(root).as_posix())
    return tuple(sorted(set(names))), tuple(unreadable)


def _blocked_reason(root: Path, branch: str, cwd: Path | None) -> str | None:
    """Lo que impide trabajar aquí, ya redactado, o `None` si nada lo impide."""
    git_dir = Path(_quiet(["rev-parse", "--git-dir"], cwd, ".git"))
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    if (git_dir / "MERGE_HEAD").exists():
        return "merge a medias"
    if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
        return "rebase a medias"
    if branch == DETACHED_HEAD:
        return "HEAD suelto (detached)"
    if not _quiet(["remote", "get-url", "origin"], cwd):
        return "sin remoto origin"
    return None


def _is_behind(reference: str, cwd: Path | None) -> bool:
    """Si la rama actual tiene commits por detrás de esa referencia.

    Se cuenta con lo que hay en la copia local, sin traer novedades: traerlas sería una escritura y
    aquí no se escribe. El aviso refleja la última vez que alguien las trajo.
    """
    count = _quiet(["rev-list", "--count", f"HEAD..{reference}"], cwd, "0")
    return count.isdigit() and int(count) > 0


def observe(cwd: Path | None = None) -> Observation:
    """Todo lo que las reglas necesitan saber del repositorio, leído una sola vez."""
    root = Path(run_git(["rev-parse", "--show-toplevel"], cwd))
    branch = _quiet(["rev-parse", "--abbrev-ref", "HEAD"], cwd, DETACHED_HEAD)
    units, unreadable = _units(root)
    return Observation(
        branch=branch,
        is_dirty=bool(_quiet(["status", "--porcelain"], cwd)),
        units=units,
        blocked_reason=_blocked_reason(root, branch, cwd),
        behind_remote=branch == MAIN_BRANCH and _is_behind(f"origin/{MAIN_BRANCH}", cwd),
        behind_main=branch != MAIN_BRANCH and _is_behind(MAIN_BRANCH, cwd),
        unreadable_manifests=unreadable,
    )
