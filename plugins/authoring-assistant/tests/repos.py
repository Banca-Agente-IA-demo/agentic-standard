"""Repositorios de prueba equivalentes a los del banco de pruebas del diseño.

`crear-repo-prueba.sh` monta un repositorio con una unidad y un remoto local para que exista origen, y
`escenario.sh` lo deja en cada uno de los seis estados. Aquí se hace lo mismo, sin red.

El repositorio se crea **una vez** y cada escenario lo devuelve al punto de partida, igual que hace
`escenario.sh`. Crear uno por prueba costaba cuatro minutos de reloj en Windows: cada invocación de
git es un proceso, y son muchas.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

UNIT = "demo-unidad"
SCENARIOS = (
    "main_clean",
    "work_branch_clean",
    "dirty",
    "unknown_branch",
    "unit_not_found",
    "blocked",
)


def git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *args], capture_output=True, text=True, encoding="utf-8", check=True
    )
    return completed.stdout.strip()


def make_repository(base: Path, *, unit: str = UNIT) -> Path:
    """Un repositorio con una unidad, una rama principal y un remoto local que hace de origen."""
    remote = base / "repo-remoto.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True, capture_output=True)

    root = base / "repo-prueba"
    manifest = root / "plugins" / unit / ".claude-plugin"
    manifest.mkdir(parents=True)
    (manifest / "plugin.json").write_text(
        json.dumps({"name": unit, "version": "0.1.0-beta.1"}, ensure_ascii=False), encoding="utf-8"
    )
    (root / "README.md").write_text("repositorio de prueba\n", encoding="utf-8")

    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True, capture_output=True)
    git(root, "config", "user.email", "prueba@example.com")
    git(root, "config", "user.name", "prueba")
    git(root, "remote", "add", "origin", str(remote))
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "unidad inicial")
    git(root, "push", "-q", "-u", "origin", "main")
    return root


def reset(root: Path) -> None:
    """Devuelve el repositorio al punto de partida, como el preámbulo de `escenario.sh`."""
    subprocess.run(["git", "-C", str(root), "merge", "--abort"], capture_output=True)
    subprocess.run(["git", "-C", str(root), "rebase", "--abort"], capture_output=True)
    git(root, "checkout", "-q", "-f", "main")
    git(root, "reset", "-q", "--hard", "origin/main")
    git(root, "clean", "-qfd")
    for branch in git(root, "branch", "--format=%(refname:short)").splitlines():
        if branch.strip() and branch.strip() != "main":
            git(root, "branch", "-q", "-D", branch.strip())
    subprocess.run(["git", "-C", str(root), "config", "--local", "--unset", "authoring.pendingAction"], capture_output=True)
    subprocess.run(["git", "-C", str(root), "config", "--local", "--unset", "authoring.pendingUnit"], capture_output=True)


def apply_scenario(root: Path, scenario: str) -> None:
    """Deja el repositorio en uno de los seis estados, como hace `escenario.sh`."""
    reset(root)
    if scenario == "main_clean":
        return
    if scenario == "work_branch_clean":
        git(root, "switch", "-q", "-c", f"fix/{UNIT}")
    elif scenario == "dirty":
        (root / "README.md").write_text("cambio sin guardar\n", encoding="utf-8")
    elif scenario == "unknown_branch":
        git(root, "switch", "-q", "-c", "mi-rama-cualquiera")
    elif scenario == "unit_not_found":
        git(root, "switch", "-q", "-c", "fix/unidad-inexistente")
    elif scenario == "blocked":
        git(root, "checkout", "-q", "--detach", "HEAD")
    else:
        raise AssertionError(f"escenario desconocido: {scenario!r}")
