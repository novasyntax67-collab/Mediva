from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import sys
import os
from typing import Optional, Dict, Any

# Ensure backend-core is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "packages", "backend-core")))

from auth.supabase import SupabaseAuthenticator
from database.models import ProfileRole, RolePermission, Permission
from app.core.config import settings
from app.core.database import async_session_maker
from app.core.unit_of_work import APIUnitOfWork

# Initialize authenticator
authenticator = SupabaseAuthenticator(
    supabase_url=settings.SUPABASE_URL,
    supabase_anon_key=settings.SUPABASE_ANON_KEY,
    jwt_secret=settings.SUPABASE_JWT_SECRET
)

security = HTTPBearer(auto_error=False)

async def get_db():
    """
    Yields a database session instance.
    """
    async with async_session_maker() as session:
        yield session

async def get_uow(session: AsyncSession = Depends(get_db)):
    """
    Yields a unit of work coordinator instance.
    """
    yield APIUnitOfWork(session)

async def get_current_user_claims(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Validates token from request authorization header.
    Extracts claims from local jwt decode or remote supabase auth get_user.
    """
    if not credentials:
        if settings.ENABLE_DEV_AUTH:
            return {
                "sub": "a0000000-0000-0000-0000-000000000001",
                "email": "jane.doe@medivahealth.com",
                "role": "authenticated"
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    claims = authenticator.verify_token(token)
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return claims

async def get_current_user(
    claims: Dict[str, Any] = Depends(get_current_user_claims)
) -> uuid.UUID:
    """
    Resolves the profile ID of the authenticated user.
    """
    return uuid.UUID(claims["sub"])

def require_permission(required_permission: str):
    """
    Dependency factory to enforce role-based access control (RBAC) permissions.
    """
    async def dependency(
        claims: Dict[str, Any] = Depends(get_current_user_claims),
        uow: APIUnitOfWork = Depends(get_uow)
    ) -> None:
        user_id = uuid.UUID(claims["sub"])
        
        async with uow:
            query = (
                select(1)
                .select_from(ProfileRole)
                .join(RolePermission, ProfileRole.role_id == RolePermission.role_id)
                .join(Permission, RolePermission.permission_id == Permission.id)
                .filter(
                    ProfileRole.profile_id == user_id,
                    Permission.name == required_permission,
                    ProfileRole.deleted_at == None,
                    RolePermission.deleted_at == None,
                    Permission.deleted_at == None
                )
            )
            result = await uow.session.execute(query)
            if not result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Operation not permitted. Insufficient privilege level."
                )
    return dependency
