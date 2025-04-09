from typing import Any, List

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr
from starlette.responses import StreamingResponse

from app.api.api_v1 import deps
from app.core.config import settings
from app.core.security import password_regex, validate_phone_number
from app.models.auditor import auditor
from app.models.ca import ca, ca_profile
from app.repository.auditor_repository import auditor_repository
from app.repository.base_repository import base_repository
from app.repository.ca_repository import ca_repository
from app.repository.documents_repository import document_repository
from app.schemas.auditor import (
    AuditorId,
    AuditorInDBBase,
    AuditorTaskBase,
    AuditorTaskCreate,
    AuditorTaskDateTime,
    AuditorUpdate,
)
from app.schemas.CA import CABase, CACreate, CAId, CAInDBBase, CAUpdate, ProfilePictureCreate
from app.schemas.common import Successful
from app.schemas.user import ResetPassword
from app.utils.azur_blob import blob_service_client
from app.utils.cryptoUtil import get_password_hash, verify_password

router = APIRouter()


@router.post("/", response_model=CABase)
async def create_ca(
    payload: CACreate,
    current_user: ca = Depends(deps.get_current_active_superuser),
):
    if await ca_repository.get_by_email(email=payload.email):
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the database.",
        )
    if await ca_repository.get_by_phone(phone=payload.phone_number):
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the database.",
        )
    if await auditor_repository.get_by_email(email=payload.email):
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the database.",
        )
    if await auditor_repository.get_by_phone(phone=payload.phone_number):
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the database.",
        )
    validate_phone_number(payload.phone_number)
    password_regex(payload.password)
    payload.password = await get_password_hash(payload.password)
    return await ca_repository.create(payload)


@router.get("/me", response_model=CAInDBBase)
async def read_user_me(
    current_user: ca = Depends(deps.get_current_active_ca),
) -> Any:
    """
    Get current user.
    """
    documents = await ca_repository.get_ca_profilePicture(current_user.id)
    result = CAInDBBase(
        **current_user,
        profilePicture=documents,
    )
    return result


@router.put("/password", response_model=Successful)
async def update_ca_password(
    response: ResetPassword,
    current_user: ca = Depends(deps.get_current_active_ca),
) -> Any:
    user_in = CAUpdate(**current_user)
    if response.current_password is None or response.new_password != response.confirm_password:
        raise HTTPException(status_code=404, detail="New password does not match!")
    if not await verify_password(response.current_password, current_user.password):
        raise HTTPException(status_code=404, detail="Current password doesnot match!")
    password_regex(response.new_password)
    user_in.password = await get_password_hash(response.new_password)
    await ca_repository.update(id=current_user.id, obj_in=user_in)
    return {"detail": "User updated successfully"}


@router.put("/", response_model=Successful)
async def update_ca(
    full_name: str = Body(None),
    email: EmailStr = Body(None),
    phone_number: str = Body(None),
    current_user: ca = Depends(deps.get_current_active_ca),
) -> Any:
    """
    Update a user.
    """
    user_in = CAUpdate(**current_user)
    if email is not None:
        if await ca_repository.get_by_email(email=email):
            raise HTTPException(
                status_code=400,
                detail="The user with this username already exists in the database.",
            )
        user_in.email = email
    if phone_number is not None:
        if await ca_repository.get_by_phone(phone=phone_number):
            raise HTTPException(
                status_code=400,
                detail="The user with this username already exists in the database.",
            )
        validate_phone_number(phone_number)
        user_in.phone_number = phone_number
    if full_name is not None:
        user_in.full_name = full_name

    await ca_repository.update(id=current_user.id, obj_in=user_in)

    return {"detail": "User updated successfully"}


@router.get("/", response_model=List[AuditorId])
async def get_lists_auditor(
    skip: int = 0,
    limit: int = 100,
    current_user: ca = Depends(deps.get_current_active_ca),
) -> Any:
    """
    Retrieve Auditor.
    """
    return await auditor_repository.get_list_auditor(current_user.id, skip=skip, limit=limit)


@router.put("/Update-Auditor/{auditor_id}", response_model=Successful)
async def update_auditor(
    auditor_id: str,
    response: AuditorUpdate,
    current_user: auditor = Depends(deps.get_current_active_ca),
) -> Any:
    """
    Update a user.
    """
    user = await base_repository.get(auditor, id=auditor_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The auditor with this username does not exist in the database",
        )
    if user.created_by != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="You can update the auditor as it is not created by you",
        )
    user_in = AuditorUpdate(**user)
    if response.email is not None:
        if await auditor_repository.get_by_email(email=response.email):
            raise HTTPException(
                status_code=400,
                detail="The user with this username already exists in the database.",
            )
        user_in.email = response.email
    if response.phone_number is not None:
        if await auditor_repository.get_by_phone(phone=response.phone_number):
            raise HTTPException(
                status_code=400,
                detail="The user with this username already exists in the database.",
            )
        validate_phone_number(response.phone_number)
        user_in.phone_number = response.phone_number
    if response.is_active is not None:
        user_in.is_active = response.is_active
    if response.full_name is not None:
        user_in.full_name = response.full_name
    if response.experience is not None:
        user_in.experience = response.experience
    if response.expertise is not None:
        user_in.expertise = response.expertise
    if response.qualification is not None:
        user_in.qualification = response.qualification
    if response.task_read is not None:
        user_in.task_read = response.task_read
    if response.task_write is not None:
        user_in.task_write = response.task_write
    if response.task_delete is not None:
        user_in.task_delete = response.task_delete
    if response.task_create is not None:
        user_in.task_create = response.task_create
    if response.task_import is not None:
        user_in.task_import = response.task_import
    if response.task_export is not None:
        user_in.task_export = response.task_export
    if response.chat_create is not None:
        user_in.chat_create = response.chat_create
    if response.chat_delete is not None:
        user_in.chat_delete = response.chat_delete
    if response.chat_read is not None:
        user_in.chat_read = response.chat_read
    if response.chat_delete is not None:
        user_in.chat_delete = response.chat_delete
    if response.chat_import is not None:
        user_in.chat_import = response.chat_import
    if response.chat_export is not None:
        user_in.chat_export = response.chat_export

    await auditor_repository.update(id=auditor_id, obj_in=user_in)

    return {"detail": "User updated successfully"}


@router.delete("/{auditor_id}", response_model=Successful)
async def delete_auditor(
    auditor_id: str,
    current_user: ca = Depends(deps.get_current_active_ca),
):
    row = await base_repository.get(auditor, id=auditor_id)
    if not row:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the database",
        )
    await auditor_repository.set_is_active(auditor_id, False)
    return {"detail": "Auditor deleted successfully"}


@router.delete("/{ca_id}", response_model=Successful)
async def delete_ca_as_admin(
    ca_id: str,
    current_user: ca = Depends(deps.get_current_active_superuser),
):
    row = await base_repository.get(ca, id=ca_id)
    if not row:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the database",
        )
    await ca_repository.ca_is_active(ca_id, False)
    return {"detail": "CA deleted successfully"}

@router.post("/profilePicture")
async def upload_profile_picture(
    filetype: str = Form(...),
    filesize: int = Form(...),
    file: UploadFile = File(...),
    current_user: ca = Depends(deps.get_current_active_ca),
):
    try:
        # Read file content
        file_content = await file.read()
        
        # Generate a unique filename
        filename = f"profilePicture.{filetype.split('/')[-1]}"
        
        # Upload to Azure Storage
        from app.utils.azure_storage import azure_image_storage
        upload_result = await azure_image_storage.upload_image(
            file_content,
            current_user.id, 
            settings.PROFILEPICTURECONTAINER_NAME,
            filename,
            filetype
        )
        
        # Prepare profile data with image URL
        profile_data = {
            "filename": filename,
            "filetype": filetype,
            "filesize": filesize,
            "container": settings.PROFILEPICTURECONTAINER_NAME,
            "filepath": upload_result["filepath"],
            "ca_id": current_user.id,
            "image_url": upload_result["image_url"],
            "id": str(uuid.uuid4())
        }
        
        # Update or create profile picture record in database
        profile = await ca_repository.get_ca_profilePicture(current_user.id)
        
        if profile:
            # If profile exists, update it
            await ca_repository.update_profile_picture(current_user.id, profile_data)
        else:
            # If no profile, create a new one
            await ca_repository.create_profile_picture_with_url(profile_data)
        
        return {
            "detail": "Profile picture uploaded successfully",
            "image_url": upload_result["image_url"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server issue while uploading file: {str(e)}")


@router.get("/profilePicture")
async def get_profile_picture(
    current_user: ca = Depends(deps.get_current_active_ca),
):
    try:
        # Get profile picture info from database
        profile_pic = await ca_repository.get_ca_profilePicture(current_user.id)
        
        if not profile_pic:
            raise HTTPException(
                status_code=404,
                detail="Profile picture does not exist"
            )
        
        # Check if image_url exists
        if hasattr(profile_pic, "image_url") and profile_pic.image_url:
            # Return the direct URL and metadata
            return {
                "image_url": profile_pic.image_url,
                "filetype": profile_pic.filetype,
                "filesize": profile_pic.filesize
            }
        else:
            # For backwards compatibility with existing records
            return {
                "filepath": profile_pic.filepath,
                "container": profile_pic.container,
                "filetype": profile_pic.filetype,
                "filesize": profile_pic.filesize
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving profile picture: {str(e)}")


@router.put("/profilePicture")
async def update_profile_picture(
    file: UploadFile = File(...),
    current_user: ca = Depends(deps.get_current_active_ca),
):
    try:
        # Read file content
        file_content = await file.read()
        filetype = file.content_type or "image/jpeg"
        filesize = len(file_content)
        
        # Generate a unique filename
        filename = f"profilePicture.{filetype.split('/')[-1]}"
        
        # Upload to Azure Storage
        from app.utils.azure_storage import azure_image_storage
        upload_result = await azure_image_storage.upload_image(
            file_content,
            current_user.id, 
            settings.PROFILEPICTURECONTAINER_NAME,
            filename,
            filetype
        )
        
        # Prepare profile data with image URL
        profile_data = {
            "filename": filename,
            "filetype": filetype,
            "filesize": filesize,
            "container": settings.PROFILEPICTURECONTAINER_NAME,
            "filepath": upload_result["filepath"],
            "image_url": upload_result["image_url"]
        }
        
        # Update profile picture in database
        await ca_repository.update_profile_picture(current_user.id, profile_data)
        
        return {
            "detail": "Profile picture updated successfully",
            "image_url": upload_result["image_url"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server issue while updating profile picture: {str(e)}")


@router.delete("/profilePicture")
async def delete_profile_picture(
    current_user: ca = Depends(deps.get_current_active_ca),
):
    try:
        # Get profile picture info
        profile_pic = await ca_repository.get_ca_profilePicture(current_user.id)
        
        if not profile_pic:
            raise HTTPException(
                status_code=404,
                detail="No profile picture found"
            )
        
        # Delete from Azure Storage
        from app.utils.azure_storage import azure_image_storage
        await azure_image_storage.delete_image(profile_pic.container, profile_pic.filepath)
        
        # Remove from database
        await ca_repository.remove_profile(current_user.id)
        
        return {"detail": "Profile picture deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server issue while deleting profile picture: {str(e)}")
@router.get("/download/profilePicture")
async def download_file(filepath: str):
    try:
        container_client = blob_service_client.get_container_client(
            settings.PROFILEPICTURECONTAINER_NAME
        )
        blob_client = container_client.get_blob_client(filepath)
        file_contents = blob_client.download_blob()
        return StreamingResponse(
            iter([file_contents.readall()]), media_type="application/octet-stream"
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")


@router.get("/{request}", response_model=AuditorInDBBase)
async def get_auditor_detail_using_phone_or_email(
    request: str,
    current_user: ca = Depends(deps.get_current_active_ca),
):
    user = await auditor_repository.get_by_email_or_phone(request)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the database",
        )
    documents = await auditor_repository.get_auditor_profilePicture(user.id)
    result = AuditorInDBBase(
        **user,
        profilePicture=documents,
    )
    return result


@router.get("/id/{auditor_id}", response_model=AuditorInDBBase)
async def get_user_detail_using_id(
    auditor_id: str,
    current_user: ca = Depends(deps.get_current_active_ca),
):
    user = await base_repository.get(auditor, id=auditor_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this userid does not exist in the database",
        )
    documents = await auditor_repository.get_auditor_profilePicture(auditor_id)
    result = AuditorInDBBase(
        **user,
        profilePicture=documents,
    )
    return result


@router.get("/auditor_task/", response_model=List[AuditorTaskDateTime])
async def get_auditor_task(
    auditor_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: ca = Depends(deps.get_current_active_ca),
):
    return await auditor_repository.get_list_auditor_task(auditor_id, skip, limit)
