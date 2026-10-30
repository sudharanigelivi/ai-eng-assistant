import json

import pytest
from fastapi.testclient import TestClient

from planner.api import app
from planner.cli import main
from planner.engine import _assign_waves, analyze
from planner.models import AIAssist, Task
from planner.render import to_markdown

GREENFIELD = "Build a scalable URL shortener service with APIs, persistence, and analytics."
BROWNFIELD = "Fix the bug in the existing checkout service where duplicate orders are created."
AMBIGUOUS = "Make the app better and faster"


def _task(tid, deps):
    return Task(tid, "t", "code", deps, [], AIAssist("p", "r", "e"), [])


def test_greenfield_classification():
    p = analyze(GREENFIELD)
    assert p.requirement_type == "greenfield"
    assert len(p.tasks) >= 10
    assert p.risks and p.trade_offs and p.limitations


def test_brownfield_classification():
    p = analyze(BROWNFIELD)
    assert p.requirement_type == "brownfield"
    assert p.ambiguity_level == "low"


def test_ambiguous_classification_adds_clarify_task():
    p = analyze(AMBIGUOUS)
    assert p.requirement_type == "ambiguous"
    assert p.ambiguity_level == "high"
    assert p.ambiguities
    assert p.tasks[0].category == "clarify"


@pytest.mark.parametrize("req", [GREENFIELD, BROWNFIELD, AMBIGUOUS])
def test_plan_dependencies_are_valid(req):
    p = analyze(req)
    ids = {t.id for t in p.tasks}
    assert len(ids) == len(p.tasks)
    waves = {t.id: t.wave for t in p.tasks}
    for t in p.tasks:
        for d in t.depends_on:
            assert d in ids
            assert waves[d] < t.wave
        assert t.ai_assist.prompt and t.ai_assist.engineer_owns and t.validation


def test_empty_requirement_rejected():
    with pytest.raises(ValueError):
        analyze("   ")


def test_unknown_dependency_and_cycle_detected():
    with pytest.raises(ValueError, match="unknown"):
        _assign_waves([_task("T1", ["T9"])])
    with pytest.raises(ValueError, match="cycle"):
        _assign_waves([_task("T1", ["T2"]), _task("T2", ["T1"])])


def test_waves_assigned_by_longest_chain():
    ts = _assign_waves([_task("T1", []), _task("T2", ["T1"]), _task("T3", ["T1", "T2"])])
    assert [t.wave for t in ts] == [1, 2, 3] or [t.wave for t in ts] == [0, 1, 2]


def test_markdown_render_sections():
    md = to_markdown(analyze(GREENFIELD))
    for heading in ("## Problem statement", "## Task breakdown", "## Risks and mitigations", "## Trade-offs"):
        assert heading in md


def test_cli_json_and_markdown(capsys):
    assert main([GREENFIELD, "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["requirement_type"] == "greenfield"
    assert main([BROWNFIELD]) == 0
    assert capsys.readouterr().out.startswith("# Engineering plan")


def test_cli_file_and_errors(tmp_path, capsys):
    f = tmp_path / "r.txt"
    f.write_text(GREENFIELD)
    assert main(["--file", str(f), "--format", "json"]) == 0
    capsys.readouterr()
    f.write_text("  ")
    assert main(["--file", str(f)]) == 2
    assert "error" in capsys.readouterr().err


def test_planner_api():
    c = TestClient(app)
    r = c.post("/api/v1/analyze", json={"requirement": GREENFIELD})
    assert r.status_code == 200 and r.json()["requirement_type"] == "greenfield"
    r = c.post("/api/v1/analyze?format=md", json={"requirement": GREENFIELD})
    assert "# Engineering plan" in r.json()["markdown"]
    assert c.post("/api/v1/analyze", json={"requirement": "x"}).status_code == 422
    assert c.post("/api/v1/analyze", json={"requirement": "     "}).status_code == 422
