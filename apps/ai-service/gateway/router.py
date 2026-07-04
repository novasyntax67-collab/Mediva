from fastapi import APIRouter

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/triage")
async def process_triage():
    return {"status": "success", "message": "Triage complete"}
