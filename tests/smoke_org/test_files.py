"""Carga de archivos de entorno y del mapa de equipos."""

import json
from pathlib import Path

import pytest

from smoke_org.files import load_environment, load_team_roster
from smoke_org.model import EnvironmentFileError

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_ENVIRONMENT = REPO_ROOT / "tools" / "smoke_org" / "environments" / "demo.json"
TEAMS_FILE = REPO_ROOT / "config" / "teams.json"


def _write(tmp_path: Path, data) -> Path:
    path = tmp_path / "env.json"
    path.write_text(json.dumps(data) if not isinstance(data, str) else data, encoding="utf-8")
    return path


def test_el_entorno_demo_del_paquete_carga_y_es_valido():
    environment = load_environment(DEMO_ENVIRONMENT)
    assert environment.organization == "Banca-Agente-IA-demo" and environment.name == "demo"


def test_clave_desconocida_en_el_entorno_es_error(tmp_path):
    data = json.loads(DEMO_ENVIRONMENT.read_text(encoding="utf-8"))
    data["plann"] = "free"
    with pytest.raises(EnvironmentFileError, match="plann"):
        load_environment(_write(tmp_path, data))


def test_clave_obligatoria_ausente_es_error(tmp_path):
    data = json.loads(DEMO_ENVIRONMENT.read_text(encoding="utf-8"))
    del data["marketplaces"]
    with pytest.raises(EnvironmentFileError, match="marketplaces"):
        load_environment(_write(tmp_path, data))


def test_json_invalido_es_error(tmp_path):
    with pytest.raises(EnvironmentFileError, match="JSON inválido"):
        load_environment(_write(tmp_path, "{ no es json"))


def test_canal_desconocido_es_error(tmp_path):
    data = json.loads(DEMO_ENVIRONMENT.read_text(encoding="utf-8"))
    data["marketplaces"][0]["channel"] = "staging"
    with pytest.raises(EnvironmentFileError):
        load_environment(_write(tmp_path, data))


def test_archivo_inexistente_es_error(tmp_path):
    with pytest.raises(EnvironmentFileError, match="no se pudo leer"):
        load_environment(tmp_path / "nope.json")


def test_el_roster_recorre_todos_los_papeles_del_teams_json_real():
    # FR-002: los nombres de equipo salen del mapa del estándar, no de una lista propia.
    roster = load_team_roster(TEAMS_FILE)
    assert roster.slugs == {
        "platform-team", "cybersecurity", "operational-risk", "compliance", "pilot-team",
        "lt-modernization", "champion-modernization",
    }


def test_un_mapa_sin_equipos_es_error(tmp_path):
    with pytest.raises(EnvironmentFileError, match="ningún equipo"):
        load_team_roster(_write(tmp_path, {"domains": {}}))
