from fastapi import APIRouter

router = APIRouter()


@router.get("/health", name="dev:health", tags=["Dev"])
def health():
    return {"result": "ok"}
