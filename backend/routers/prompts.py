from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import User, require_admin
from services import prompt_manager

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


class SetActiveRequest(BaseModel):
    version: str


class ABTestRequest(BaseModel):
    control: str
    candidate: str
    traffic_pct: int = 10


@router.get("/versions")
def list_versions(user: User = Depends(require_admin)):
    versions = prompt_manager.get_available_versions()
    registry = prompt_manager.get_registry()
    return {
        "versions": versions,
        "active_version": registry["active_version"],
        "ab_test": registry["ab_test"],
    }


@router.get("/versions/{version}")
def get_version_detail(version: str, user: User = Depends(require_admin)):
    try:
        prompt = prompt_manager.load_prompt(version)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Version '{version}' not found")
    return {
        "version": prompt["version"],
        "name": prompt.get("name", ""),
        "config": prompt.get("config", {}),
        "system_prompt_length": len(prompt.get("system_prompt", "")),
        "few_shot_count": len(prompt.get("few_shot", [])),
    }


@router.post("/activate")
def activate_version(req: SetActiveRequest, user: User = Depends(require_admin)):
    try:
        prompt_manager.set_active_version(req.version)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"active_version": req.version, "ab_test": None}


@router.post("/ab-test/start")
def start_ab_test(req: ABTestRequest, user: User = Depends(require_admin)):
    try:
        prompt_manager.start_ab_test(req.control, req.candidate, req.traffic_pct)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return prompt_manager.get_registry()


@router.post("/ab-test/stop")
def stop_ab_test(user: User = Depends(require_admin)):
    prompt_manager.stop_ab_test()
    return prompt_manager.get_registry()
