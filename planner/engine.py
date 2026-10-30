import re

from . import templates as T
from .models import AIAssist, Ambiguity, Plan, Risk, Task, TradeOff

IMPACT_WEIGHT = {"high": 2, "medium": 1, "low": 0.5}
SOLUTION_SCOPE_TERMS = {"analytics", "apis", "persistence"}  # only meaningful for new builds


def _word_hits(text: str, words) -> int:
    return sum(1 for w in words if w in text)


def _find_terms(text: str) -> list[str]:
    return [t for t in T.VAGUE_TERMS if re.search(rf"\b{re.escape(t)}\b", text)]


def classify(requirement: str) -> tuple[str, str, list[str]]:
    """Return (requirement_type, ambiguity_level, matched vague terms)."""
    text = requirement.lower()
    gf = _word_hits(text, T.GREENFIELD_WORDS)
    bf = _word_hits(text, T.BROWNFIELD_WORDS)
    terms = _find_terms(text)
    if bf > gf:
        terms = [t for t in terms if t not in SOLUTION_SCOPE_TERMS]

    score = sum(IMPACT_WEIGHT[T.VAGUE_TERMS[t][2]] for t in terms)
    if len(text.split()) < 10:
        score += 3
    if gf and not re.search(T.NUMBER_RE, text) and "scalable" not in terms:
        score += 1  # a new build with no quantified expectations at all
    level = "high" if score >= 6 else "medium" if score >= 2 else "low"

    if (gf == 0 and bf == 0) or level == "high":
        rtype = "ambiguous"
    else:
        rtype = "brownfield" if bf > gf else "greenfield"
    return rtype, level, terms


def _domain(requirement: str) -> str:
    text = requirement.lower()
    return "url_shortener" if any(w in text for w in T.URL_SHORTENER_WORDS) else "generic"


def _ambiguities(requirement: str, rtype: str, terms: list[str]) -> list[Ambiguity]:
    items = [
        Ambiguity(term=t, question=T.VAGUE_TERMS[t][0], assumption=T.VAGUE_TERMS[t][1],
                  impact=T.VAGUE_TERMS[t][2])
        for t in terms
    ]
    text = requirement.lower()
    if rtype == "brownfield" and not re.search(r"\b(expected|should|when|steps|returns?)\b", text):
        items.append(Ambiguity(
            "reproduction details",
            "What is the expected vs actual behaviour and how is it reproduced?",
            "The first task produces a failing test that defines expected behaviour.",
            "high",
        ))
    if rtype == "ambiguous":
        items.append(Ambiguity(
            "scope",
            "What outcome, for which users, would make this successful?",
            "No implementation begins until success criteria are agreed.",
            "high",
        ))
    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(items, key=lambda a: order[a.impact])


def _problem_statement(requirement: str, rtype: str, domain: str) -> str:
    req = requirement.strip().rstrip(".")
    if domain == "url_shortener" and rtype == "greenfield":
        return (
            "Deliver a stateless HTTP service that maps long URLs to short codes, redirects "
            "with low latency, persists links durably, and reports per-link click analytics, "
            "with explicit numeric scale targets and abuse protection."
        )
    if rtype == "greenfield":
        return f"Design and deliver a new capability: \"{req}\", with an explicit contract, tests and documentation."
    if rtype == "brownfield":
        return (
            f"Change existing behaviour safely: \"{req}\". Preserve public behaviour except "
            "where intentionally changed, proven by tests written before the change."
        )
    return (
        f"The request \"{req}\" is underspecified. Convert it into measurable acceptance "
        "criteria before committing to a design."
    )


def _build_tasks(requirement: str, rtype: str, domain: str) -> list[dict]:
    if rtype == "brownfield":
        return T.BROWNFIELD
    if rtype == "ambiguous":
        generic = [t for t in T.GREENFIELD_GENERIC if t["key"] != "clarify"]
        # Everything downstream of the spike depends on it.
        rewired = [dict(t, deps=["spike" if d == "clarify" else d for d in t["deps"]])
                   for t in generic]
        return T.AMBIGUOUS_PREFIX + rewired
    return T.URL_SHORTENER_GREENFIELD if domain == "url_shortener" else T.GREENFIELD_GENERIC


def _assign_waves(tasks: list[Task]) -> list[Task]:
    """Topologically order tasks; wave = longest dependency chain length."""
    by_id = {t.id: t for t in tasks}
    for t in tasks:
        for d in t.depends_on:
            if d not in by_id:
                raise ValueError(f"{t.id} depends on unknown task {d}")
    waves: dict[str, int] = {}

    def depth(tid: str, stack: tuple[str, ...] = ()) -> int:
        if tid in stack:
            raise ValueError(f"dependency cycle: {' -> '.join(stack + (tid,))}")
        if tid not in waves:
            deps = by_id[tid].depends_on
            waves[tid] = 1 + max((depth(d, stack + (tid,)) for d in deps), default=0)
        return waves[tid]

    for t in tasks:
        t.wave = depth(t.id)
    return sorted(tasks, key=lambda t: (t.wave, tasks.index(t)))


def analyze(requirement: str) -> Plan:
    requirement = " ".join(requirement.split())
    if len(requirement) < 3:
        raise ValueError("requirement must not be empty")
    rtype, level, terms = classify(requirement)
    domain = _domain(requirement)

    task_defs = _build_tasks(requirement, rtype, domain)
    tasks = [
        Task(
            id=f"T{i}",
            title=d["title"],
            category=d["category"],
            depends_on=[],
            deliverables=list(d["deliverables"]),
            ai_assist=AIAssist(d["prompt"].format(req=requirement), d["ai_role"], d["owns"]),
            validation=list(d["validation"]),
        )
        for i, d in enumerate(task_defs, start=1)
    ]
    key_to_id = {d["key"]: t.id for d, t in zip(task_defs, tasks)}
    for d, t in zip(task_defs, tasks):
        t.depends_on = [key_to_id[k] for k in d["deps"]]

    ambiguities = _ambiguities(requirement, rtype, terms)
    risks = (
        (T.URL_SHORTENER_RISKS if domain == "url_shortener" and rtype == "greenfield" else [])
        + {"greenfield": T.GENERIC_RISKS, "brownfield": T.BROWNFIELD_RISKS,
           "ambiguous": T.AMBIGUOUS_RISKS}[rtype]
        + T.AI_RISKS
    )
    trade_offs = (
        T.TRADE_OFFS_URL if domain == "url_shortener" and rtype == "greenfield" else []
    ) + T.TRADE_OFFS_GENERIC
    assumptions = [f"{a.term}: {a.assumption}" for a in ambiguities]

    return Plan(
        requirement=requirement,
        requirement_type=rtype,
        domain=domain,
        ambiguity_level=level,
        problem_statement=_problem_statement(requirement, rtype, domain),
        ambiguities=ambiguities,
        assumptions=assumptions,
        tasks=_assign_waves(tasks),
        risks=[Risk(*r) for r in risks],
        trade_offs=[TradeOff(*t) for t in trade_offs],
        limitations=list(T.LIMITATIONS_BASE),
    )
