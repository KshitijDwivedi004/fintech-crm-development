import jwt
from typing import Any, Optional
from fastapi import Depends, HTTPException, WebSocketException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from app.core import security
from app.core.config import settings
from app.models.auditor import auditor
from app.models.ca import ca
from app.repository.auditor_repository import auditor_repository
from app.repository.base_repository import base_repository
from app.repository.ca_repository import ca_repository
from app.repository.user_repository import user_repository

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")
reusable_user_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/user/login/access-token"
)

async def get_current_user(token: str = Depends(reusable_oauth2)) -> Any:
    """
    Get CA, Admin and Auditor details from token
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = payload.get("sub")
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    # First try to get CA user
    user = await base_repository.get(ca, id=token_data)
    if user is not None:
        return user

    # Then try to get auditor
    user = await base_repository.get(auditor, id=token_data)
    if user is not None:
        return user

    # Try to get admin (if you have an admin model)
    # user = await base_repository.get(admin, id=token_data)
    # if user is not None:
    #     return user
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

async def get_user(token: str = Depends(reusable_user_oauth2)) -> Any:
    """
    Get user details from token
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = payload.get("sub")
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
        
    user = await user_repository.get_by_phone(token_data)
    if user is not None:
        return user
        
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

async def get_current_active_user(current_user: Any = Depends(get_user)) -> Any:
    """
    Return user details if user is active
    """
    if not current_user or current_user.role != "User":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )

    if not await user_repository.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user

async def get_current_active_admin_ca_auditor(current_user: Any = Depends(get_current_user)) -> Any:
    """
    Get the active current admin, CA, and auditor details from token
    Returns the current user if they have appropriate role and are active
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    if not hasattr(current_user, 'role') or current_user.role not in ["Admin", "CA", "Auditor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )

    is_active = False
    if current_user.role == "Admin":
        is_active = await ca_repository.is_active(current_user)
    elif current_user.role == "CA":
        is_active = await ca_repository.is_active(current_user)
    else:  # Auditor
        is_active = await auditor_repository.is_active(current_user)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return current_user

async def get_current_active_ca(current_user: Any = Depends(get_current_user)) -> Any:
    """
    Get active CA user
    """
    if not current_user or current_user.role != "CA":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )

    if not await ca_repository.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user

async def get_current_active_superuser(current_user: Any = Depends(get_current_user)) -> Any:
    """
    Get active admin user
    """
    if not current_user or current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )

    if not await ca_repository.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user doesn't have enough privileges"
        )
    
    return current_user

async def get_current_active_auditor(current_user: Any = Depends(get_current_user)) -> Any:
    """
    Get active auditor user
    """
    if not current_user or current_user.role != "Auditor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )

    if not await auditor_repository.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user

async def get_current_active_auditor_ca(current_user: Any = Depends(get_current_user)) -> Any:
    """
    Get active auditor or CA user
    """
    if not current_user or current_user.role not in ["Auditor", "CA"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )

    is_active = False
    if current_user.role == "Auditor":
        is_active = await auditor_repository.is_active(current_user)
    else:  # CA
        is_active = await ca_repository.is_active(current_user)

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user

async def websocket_auth(token: str = Depends(reusable_oauth2)) -> None:
    """
    Authenticate WebSocket connections
    """
    try:
        jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
    except Exception:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)