from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .engine import analyze
from .render import to_markdown

app = FastAPI(title="Sudha Gelvi Requirement Planner", version="1.0.0", contact={"name": "Sudha Gelvi"})


class AnalyzeRequest(BaseModel):
    requirement: str = Field(..., min_length=3, max_length=5000)


@app.post("/api/v1/analyze")
def analyze_requirement(body: AnalyzeRequest, format: str = "json"):
    try:
        plan = analyze(body.requirement)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if format == "md":
        return {"markdown": to_markdown(plan)}
    return plan.to_dict()
