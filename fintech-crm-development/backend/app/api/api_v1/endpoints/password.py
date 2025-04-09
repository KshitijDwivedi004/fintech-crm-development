from fastapi import APIRouter, Body, HTTPException, Depends
from typing import Any
from databases import Database
from fastapi.responses import JSONResponse
from sqlalchemy import select
from app.api.api_v1 import deps
from app.repository import password_history_repository
from app.repository.token_repository import marked_token_as_used, validate_token
from app.utils.cryptoUtil import verify_password,get_password_hash
from typing import List
from app.models.tokens import tokens

from app.db.session import get_database, database  # Import both
from app.core import security
from app.core.config import settings

from app.repository.user_repository import UserRepository
from app.repository.auditor_repository import auditor_repository
from app.schemas.auditor import AuditorCreate
router = APIRouter()
from app.repository.password_history_repository import PasswordHistoryRepository


# Create a single instance of UserRepository
user_repository = UserRepository(database)

@router.post("/password-recovery", response_model=dict[str, str])
async def recover_password(email: str = Body(..., embed=True)) -> Any:
    from app.service.email_reset_password import (  
        generate_account_reset_token,
        send_reset_password_email
    )
    """
    Password Recovery endpoint - verifies the email and sends password reset token
    """
    user = await auditor_repository.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"message": "The user with this email does not exist in the system"},
        )
        
    try:
        password_reset_token = await generate_account_reset_token(email=email)
        send_reset_password_email(
            email,
            user['full_name'],
            password_reset_token
        )
        
        return {"detail": "Password recovery email sent successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Internal server error"})


@router.post("/reset-password/{token}", response_model=dict[str, str])
async def reset_password(
    token:str,
    new_password: str = Body(...,embed=True)
) -> Any:
    """
    Reset password endpoint
    """    
    
    valid_token = await validate_token(token)
    from app.service.email_reset_password import (  
        verify_account_reset_token
    )
    
    email = verify_account_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail={"message": "Invalid token"})
    
    user = await auditor_repository.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"message": "The user with this email does not exist in the system"},
        )
    # Check if the new password is in the recent history
    if await verify_password(new_password, user['password']):
        raise HTTPException(
            status_code=400,
            detail={"message": "For security reasons, your new password must be different from last 3 passwords you've used in the past."}
        ) 
        
    # Check password history
    password_ok = await PasswordHistoryRepository.check_password_history(
        user['id'], 
        new_password,
        limit=2  # Check last 2 passwords (plus current = 3 total)
    )
    
    if not password_ok:
        raise HTTPException(
            status_code=400,
            detail={"message": "For security reasons, your new password must be different from last 3 passwords you've used in the past."}
        )
    hashed_password = await get_password_hash(new_password)
    
    # Add the current password to history before updating
    await PasswordHistoryRepository.add_password_to_history(
        user['id'], 
        user['password']
    )
    await auditor_repository.update_password(user['id'], hashed_password)
    # Trim password history
    await PasswordHistoryRepository.trim_password_history(user['id'], max_entries=5)
    
    await marked_token_as_used(token)
    return {"detail": "Password updated successfully"}

@router.get("/validate-token/{token}")
async def validate_reset_token(token: str):
    """
    Validate reset token
    """
    try:
        await validate_token(token)
        return JSONResponse(status_code=200, content={"message": "Token is valid"})
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

@router.post("/setup-account/{token}", response_model=dict[str, str])
async def setup_account(
    token: str,
    password: str = Body(...,embed=True),
) -> Any:
    """
    Setup account with password using setup token
    """
    
    valid_token = await validate_token(token)
    
    from app.service.email_account_setup import (  
        send_account_setup_email,
        generate_account_setup_token,
        verify_account_setup_token
    )
    email = verify_account_setup_token(token)
    
    if not email:
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid token"}
        )
    
    user = await auditor_repository.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={"message": "User not found"}
        )
    
    hashed_password = await get_password_hash(password)
    await auditor_repository.activate_account(user['id'],hashed_password)
    await marked_token_as_used(token)
    return {"message": "Account setup completed successfully"}

@router.post("/create-auditor", response_model=dict[str, str])
async def create_auditor(
    auditor_in: AuditorCreate  # Accept all input fields
) -> Any:
    from app.service.email_account_setup import (   
        send_account_setup_email,
        generate_account_setup_token,   
    )
    # Check if the user already exists
    user = await auditor_repository.get_by_email(auditor_in.email)
    if user:
        if not user["is_active"]:
            token = await generate_account_setup_token(auditor_in.email)
            send_account_setup_email(
                email_to=auditor_in.email,
                full_name=auditor_in.full_name,
                token=token
            )
            return {"message": "User already exists but is inactive. Setup email sent again."}
        
        # User exists and is active
        raise HTTPException(
            status_code=400,
            detail={"message": "The user with this email already exists and is active."},
        )
    
    """
    currently I will set created_by option in auditor pydantic schema to none as we haven't implemented the
    admin functionality yet, after implementing the admin functionality we can secure this 
    endpoint and set created_by option to the current user.  
    """
    
    new_user = await auditor_repository.create(auditor_in)

    # Generate setup token and send email
    token = await generate_account_setup_token(auditor_in.email)
    send_account_setup_email(
        email_to=auditor_in.email,
        full_name=auditor_in.full_name,
        token=token
    )


    return {"message": "User created successfully. Setup email sent."}