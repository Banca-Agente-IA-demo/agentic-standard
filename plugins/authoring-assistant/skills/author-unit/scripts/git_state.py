"""Clasifica el estado del repositorio del autor y lo imprime.

No modifica nada: sólo lee. El modelo lee el campo `state` y no interpreta la salida de git.

Estados: main_clean, work_branch_clean, dirty, unknown_branch, unit_not_found, blocked.
"""

from __future__ import annotations

import sys

from _entry import configure_streams, emit, fail, without_nulls  # noqa: E402  (ajusta sys.path)

from authoring_core.adapters.git import GitUnavailable  # noqa: E402
from authoring_core.application.author_context import read_git_state  # noqa: E402


def main() -> int:
    configure_streams()
    try:
        state = read_git_state()
    except GitUnavailable as failure:
        return fail(f"no se pudo preguntar a git: {failure}")
    return emit(
        without_nulls(
            {
                "state": state.state,
                "branch": state.branch,
                "message": state.message,
                "action": state.action.value if state.action else None,
                "unit": state.unit,
                "units": list(state.units),
                "behind_remote": state.behind_remote or None,
                "behind_main": state.behind_main or None,
                "unreadable_manifests": list(state.unreadable_manifests),
            }
        )
    )


if __name__ == "__main__":
    sys.exit(main())
