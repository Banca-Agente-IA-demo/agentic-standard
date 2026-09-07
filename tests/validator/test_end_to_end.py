"""De punta a punta: una unidad instanciada de las plantillas del repositorio pasa el validador.

Es la comprobación que impide que plantilla y reglas se separen (SC-002). Toca disco a propósito, y
sólo bajo `tmp_path`.
"""

from __future__ import annotations

import json

from agentic_validator.cli import main, review_unit
from agentic_validator.domain.model import Verdict

from tests.validator.units import CREDENTIAL, SERVER, add_agent, add_skill, build_unit, read_governance, write_governance


def test_una_unidad_instanciada_de_las_plantillas_no_tiene_hallazgos(tmp_path):
    root = build_unit(tmp_path)
    report = review_unit(root)
    assert report.findings == (), [f"{f.rule}: {f.message}" for f in report.findings]
    assert report.verdict is Verdict.COMPLIANT


def test_una_unidad_con_servidor_y_hooks_de_las_plantillas_tampoco_tiene_hallazgos(tmp_path):
    root = build_unit(tmp_path, with_mcp=True, with_hooks=True)
    report = review_unit(root)
    assert report.findings == (), [f"{f.rule}: {f.message}" for f in report.findings]


def test_el_repositorio_se_deduce_del_arbol_sin_indicarlo(tmp_path):
    # Una unidad vive en <repositorio>/<tipo>/<unidad>.
    root = build_unit(tmp_path)
    assert "identity.id-repository" not in [f.rule for f in review_unit(root).findings]


def test_una_unidad_con_un_skill_y_un_agente_de_ejemplo_pasa(tmp_path):
    root = build_unit(tmp_path)
    add_skill(root)
    add_agent(root)
    governance = read_governance(root)
    governance["permissions"]["tools"] = ["Read"]
    write_governance(root, governance)
    report = review_unit(root)
    assert report.findings == (), [f"{f.rule}: {f.message}" for f in report.findings]


def test_estropear_el_gobierno_produce_hallazgos_del_contrato_y_no_una_excepcion(tmp_path):
    root = build_unit(tmp_path)
    governance = read_governance(root)
    governance["domain"] = "modernization"  # campo retirado de la demo
    write_governance(root, governance)
    rules = [f.rule for f in review_unit(root).findings]
    assert "contract.governance" in rules


def test_un_gobierno_con_json_invalido_se_informa_y_no_rompe(tmp_path):
    root = build_unit(tmp_path)
    (root / "GOVERNANCE.json").write_text("{ no es json", encoding="utf-8")
    rules = [f.rule for f in review_unit(root).findings]
    assert "identity.governance-unreadable" in rules


def test_una_carpeta_que_no_es_una_unidad_termina_con_el_codigo_de_no_comprobable(tmp_path, capsys):
    codigo = main([str(tmp_path / "no-existe")])
    assert codigo == Verdict.UNREADABLE.exit_code


def test_el_comando_devuelve_cero_sobre_una_unidad_valida(tmp_path, capsys):
    root = build_unit(tmp_path)
    assert main([str(root)]) == Verdict.COMPLIANT.exit_code
    assert "Veredicto: CUMPLE" in capsys.readouterr().out


def test_el_comando_devuelve_uno_y_nombra_el_archivo_cuando_algo_incumple(tmp_path, capsys):
    root = build_unit(tmp_path)
    governance = read_governance(root)
    governance["id"] = "otro-repo/demo-unit"
    write_governance(root, governance)
    assert main([str(root)]) == Verdict.NOT_COMPLIANT.exit_code
    salida = capsys.readouterr().out
    assert "Veredicto: NO CUMPLE" in salida and "GOVERNANCE.json" in salida


def test_el_formato_estructurado_lleva_el_veredicto_en_un_campo(tmp_path, capsys):
    # La constitución (principio I) exige que el modelo lea un campo, no que interprete texto.
    root = build_unit(tmp_path)
    main([str(root), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["verdict"] == "compliant" and payload["findings"] == []


def test_una_credencial_en_claro_en_una_unidad_real_se_detecta(tmp_path):
    """C2: la unidad viaja sin el secreto.

    Sustituir la variable por un literal produce dos hallazgos y los dos son correctos: el valor en
    claro, y la credencial que el gobierno declara y la conexión ya no usa.
    """
    root = build_unit(tmp_path, with_mcp=True)
    connection = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))
    connection["mcpServers"][SERVER]["headers"]["Authorization"] = "Bearer ghp_0123456789abcdef0123"
    (root / ".mcp.json").write_text(json.dumps(connection, indent=2), encoding="utf-8")
    findings = review_unit(root).findings
    rules = [f.rule for f in findings]
    assert "mcp.literal-secret" in rules
    assert "mcp.credential-unused" in rules
    assert CREDENTIAL in str(findings)
