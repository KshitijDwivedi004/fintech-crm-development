from datetime import timedelta
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core import security
from app.core.config import settings
from app.core.otp import send_otp, verify_otp
from app.repository.auditor_repository import auditor_repository
from app.repository.ca_repository import ca_repository
from app.repository.documents_repository import document_repository
from app.repository.user_repository import user_repository
from app.schemas.common import ProfilePic
from app.schemas.otp import CreateOTP, VerifyOTP
from app.schemas.token import Token,TokenRefresh

router = APIRouter()


@router.post("/login/access-token", response_model=Token)
async def login_access_token(form_data: OAuth2PasswordRequestForm = Depends(), remember_me: bool = Form(False)) -> Any:
    """
    API endpoint for login as CA, Admin and Auditor
    """
    user = await ca_repository.authenticate(request=form_data.username, password=form_data.password)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    if user:
        if not await ca_repository.is_active(user):
            raise HTTPException(status_code=400, detail="Inactive user")
        
        profile_pic = await ca_repository.get_ca_profilePicture(user.id)
        
        if profile_pic:
            if hasattr(profile_pic, "image_url") and profile_pic.image_url:
                profile_pic_data = ProfilePic(**profile_pic)
            else:
                profile_pic_data = ProfilePic(
                    id=profile_pic.id,
                    filename=profile_pic.filename,
                    filetype=profile_pic.filetype,
                    filesize=profile_pic.filesize,
                    filepath=profile_pic.filepath,
                    container=profile_pic.container
                )
        else:
            profile_pic_data = None
        
        return {
            "refresh_token": await security.create_refresh_token(user.id, remember_me) if remember_me else None,
            "access_token": await security.create_access_token(
                user.id, expires_delta=access_token_expires
            ),
            "token_type": "bearer",
            "user_info": {
                "id": user.id,
                "full_name": user.full_name,
                "role": user.role,
                "phone_number": user.phone_number,
                "profile_pic": profile_pic_data,
            },
        }
    
    user = await auditor_repository.authenticate(
        request=form_data.username, password=form_data.password
    )
    
    if user:
        if not await auditor_repository.is_active(user):
            raise HTTPException(status_code=400, detail="Inactive user")
        
        profile_pic = await auditor_repository.get_auditor_profilePicture(user.id)
        
        if profile_pic:
            # Use direct image_url if available, otherwise create profile_pic without it
            if hasattr(profile_pic, "image_url") and profile_pic.image_url:
                profile_pic_data = ProfilePic(**profile_pic)
            else:
                profile_pic_data = ProfilePic(
                    id=profile_pic.id,
                    filename=profile_pic.filename,
                    filetype=profile_pic.filetype,
                    filesize=profile_pic.filesize,
                    filepath=profile_pic.filepath,
                    container=profile_pic.container
                )
        else:
            profile_pic_data = None
        
        return {
            "refresh_token": await security.create_refresh_token(user.id, remember_me) if remember_me else None,
            "access_token": await security.create_access_token(
                user.id, expires_delta=access_token_expires
            ),
            "token_type": "bearer",
            "user_info": {
                "id": user.id,
                "full_name": user.full_name,
                "role": user.role,
                "phone_number": user.phone_number,
                "profile_pic": profile_pic_data,
            },
        }
    
    raise HTTPException(status_code=401, detail="This email address is not registered with Saral. Please check and try again.")

@router.post("/refresh", response_model=TokenRefresh)
async def refresh_access_token(refresh_token: str = Form(...)) -> Any:
    """
    API to refresh Access Token using the Refresh Token.
    """
    user_id = await security.decode_token(refresh_token, settings.REFRESH_SECRET_KEY)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return {
        "access_token": await security.create_access_token(user_id, expires_delta=access_token_expires),
        "token_type": "bearer",
    }
    
@router.post("/send_OTP")
async def send_OTP(payload: CreateOTP, background_tasks: BackgroundTasks):
    user = await user_repository.get_by_phone(payload.phone_number)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect Phonenumber",
        )

    if not await user_repository.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")

    background_tasks.add_task(send_otp, payload)
    return {"detail": "OTP sent successfully"}


@router.post("/user/login/access-token")
async def user_login_access_token(payload: VerifyOTP):
    """
    Login API endpoint for user
    """
    user = await user_repository.get_by_phone(payload.phone_number)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect Phonenumber",
        )

    if not await user_repository.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    # verfifing OTP
    await verify_otp(payload)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    return {
        "access_token": await security.create_access_token(
            user.phone_number, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "user_info": {
            "id": user.id,
            "phone_number": user.phone_number,
            "full_name": user.full_name,
            "email": user.email,
        },
    }