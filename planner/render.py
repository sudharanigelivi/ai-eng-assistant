from .models import Plan


def to_markdown(plan: Plan) -> str:
    out = [
        f"# Engineering plan: {plan.requirement}",
        "",
        f"- **Type:** {plan.requirement_type}  |  **Domain:** {plan.domain}  |  "
        f"**Ambiguity:** {plan.ambiguity_level}",
        "",
        "## Problem statement",
        plan.problem_statement,
        "",
        "## Ambiguities and assumptions",
    ]
    if plan.ambiguities:
        out += ["| Term | Impact | Question | Working assumption |", "|---|---|---|---|"]
        out += [f"| {a.term} | {a.impact} | {a.question} | {a.assumption} |" for a in plan.ambiguities]
    else:
        out.append("None detected.")
    out += ["", "## Task breakdown (execution order; tasks in the same wave can run in parallel)"]
    wave = 0
    for t in plan.tasks:
        if t.wave != wave:
            wave = t.wave
            out += ["", f"### Wave {wave}" ]
        deps = ", ".join(t.depends_on) or "none"
        out += [
            "",
            f"**{t.id} - {t.title}** `[{t.category}]` depends on: {deps}",
            f"- Deliverables: {'; '.join(t.deliverables)}",
            f"- AI prompt: _{t.ai_assist.prompt}_",
            f"- AI does: {t.ai_assist.ai_role}",
            f"- Engineer owns: {t.ai_assist.engineer_owns}",
            f"- Validation: {'; '.join(t.validation)}",
        ]
    out += ["", "## Risks and mitigations", "| Kind | Risk | Mitigation |", "|---|---|---|"]
    out += [f"| {r.kind} | {r.risk} | {r.mitigation} |" for r in plan.risks]
    out += ["", "## Trade-offs", "| Decision | Chosen | Alternative | Rationale |", "|---|---|---|---|"]
    out += [f"| {t.decision} | {t.chosen} | {t.alternative} | {t.rationale} |" for t in plan.trade_offs]
    out += ["", "## Limitations"] + [f"- {l}" for l in plan.limitations]
    return "\n".join(out) + "\n"
