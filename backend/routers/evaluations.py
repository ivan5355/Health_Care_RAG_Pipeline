from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import User, get_current_user, require_admin
from models.evaluation import EvaluationRun, EvaluationRunDetail
from services.evaluator import get_evaluation_run, get_evaluation_runs, run_comparison, run_evaluation

router = APIRouter(prefix="/api", tags=["evaluations"])


class CompareRequest(BaseModel):
    version_a: str
    version_b: str


@router.get("/evaluations", response_model=list[EvaluationRun])
def list_evaluations(user: User = Depends(get_current_user)):
    return get_evaluation_runs()


@router.get("/evaluations/{run_id}", response_model=EvaluationRunDetail)
def get_evaluation(run_id: str, user: User = Depends(get_current_user)):
    run = get_evaluation_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return run


@router.post("/evaluations/run", response_model=EvaluationRunDetail)
def trigger_evaluation(
    name: str = "RAG Evaluation", prompt_version: str | None = None, user: User = Depends(require_admin)
):
    return run_evaluation(name, prompt_version=prompt_version)


@router.post("/evaluations/compare")
def compare_prompt_versions(req: CompareRequest, user: User = Depends(require_admin)):
    return run_comparison(req.version_a, req.version_b)
