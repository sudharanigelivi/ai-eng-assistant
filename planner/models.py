from dataclasses import asdict, dataclass, field


@dataclass
class Ambiguity:
    term: str
    question: str
    assumption: str
    impact: str  # high | medium | low


@dataclass
class AIAssist:
    prompt: str
    ai_role: str
    engineer_owns: str


@dataclass
class Task:
    id: str
    title: str
    category: str  # clarify | design | code | test | docs | review
    depends_on: list[str]
    deliverables: list[str]
    ai_assist: AIAssist
    validation: list[str]
    wave: int = 0  # tasks in the same wave can run in parallel


@dataclass
class Risk:
    kind: str  # functional | design | ai
    risk: str
    mitigation: str


@dataclass
class TradeOff:
    decision: str
    chosen: str
    alternative: str
    rationale: str


@dataclass
class Plan:
    requirement: str
    requirement_type: str  # greenfield | brownfield | ambiguous
    domain: str
    ambiguity_level: str  # low | medium | high
    problem_statement: str
    ambiguities: list[Ambiguity] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    trade_offs: list[TradeOff] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
