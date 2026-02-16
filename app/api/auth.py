"""Authentication API routes."""
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.controllers.auth_controller import AuthController
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_settings, oauth2_scheme
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    ProfileUpdateRequest,
    SignupRequest,
    TokenResponse,
    UserProfileResponse,
)
from app.schemas.common import MessageResponse

router = APIRouter()


@router.post("/signup", response_model=UserProfileResponse, status_code=201)
async def signup(
    data: SignupRequest,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserProfileResponse:
    """Register a new user account."""
    controller = AuthController(session, settings)
    return await controller.signup(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Authenticate and receive a JWT access token."""
    controller = AuthController(session, settings)
    data = LoginRequest(email=form_data.username, password=form_data.password)
    return await controller.login(data)


@router.post("/signout", response_model=MessageResponse)
async def signout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    """Revoke the current JWT token."""
    controller = AuthController(session, settings)
    return await controller.signout(token, current_user.id)


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserProfileResponse:
    """Get the current user's profile and preferences."""
    controller = AuthController(session, settings)
    return await controller.get_profile(current_user)


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserProfileResponse:
    """Update the current user's profile and preferences."""
    controller = AuthController(session, settings)
    return await controller.update_profile(current_user, data)
