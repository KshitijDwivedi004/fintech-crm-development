from typing import Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

import jwt
from pydantic import ValidationError

from app.core import security
from app.core.config import settings
from app.models.call import telecaller
from app.repository.call_repository import telecaller_repository
from app.api.api_v1.deps import get_current_user

# Reuse the same OAuth2 scheme from the main deps
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")


async def get_current_telecaller(current_user: Any = Depends(get_current_user)) -> Any:
    """
    Get the current telecaller user
    """
    if not current_user or current_user.role != "Telecaller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
        )

    user = await telecaller_repository.get(current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telecaller not found")

    return user


async def get_current_active_telecaller(current_user: Any = Depends(get_current_telecaller)) -> Any:
    """
    Get the current active telecaller user
    """
    if not await telecaller_repository.is_active(current_user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return current_user
