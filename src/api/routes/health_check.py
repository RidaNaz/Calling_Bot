from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/")
async def health_check() -> bool:
    return True