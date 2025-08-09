from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/ping")
def ping():
    return {"status": "OK", "message": "Metro Match API is running"}
