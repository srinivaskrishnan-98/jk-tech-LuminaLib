from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.books import router as books_router
from app.api.recommendations import router as recommendations_router
from app.api.reviews import router as reviews_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(books_router, prefix="/books", tags=["Books"])
api_router.include_router(reviews_router, prefix="/books", tags=["Reviews"])
api_router.include_router(recommendations_router, tags=["Recommendations"])
