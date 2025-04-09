import io
import os
import zipfile
from typing import Any, List, Optional
from jose import jwt
import random
import uuid
import string
from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr
from starlette.responses import StreamingResponse
from app.repository import password_history_repository
from app.utils.azure_storage import azure_image_storage

from app.api.api_v1 import deps
from app.core.config import settings
from app.core.security import password_regex, validate_phone_number
from app.models.auditor import auditor, auditor_profile
from app.models.ca import ca
from app.models.user import documents, users
from app.repository.auditor_repository import auditor_repository
from app.repository.base_repository import base_repository
from app.repository.ca_repository import ca_repository
from app.repository.documents_repository import document_repository
from app.repository.user_repository import user_repository
import uuid
from app.repository.password_history_repository import PasswordHistoryRepository
from app.db.session import database, engine, metadata
from app.schemas.auditor import (
    AuditorBase,
    AuditorCreate,
    AuditorCreateId,
    AuditorId,
    AuditorInDBBase,
    AuditorTaskBase,
    AuditorTaskCreate,
    AuditorTaskDateTime,
    AuditorUpdate,
    ProfilePictureCreate,
)
from app.schemas.common import Successful
from app.schemas.document import (
    DocumentBase,
    DocumentCreate,
    DocumentList,
    DocumentStatus,
    DocumentType,
)
from app.schemas.user import (
    Category,
    NameOrder,
    ResetAuditorPassword,
    ResetPassword,
    TaxPayerType,
    ForgetPassword,
    TaxSlab,
    UserUpdateDeatils,
)
from app.utils.azur_blob import blob_service_client, container_client
from app.utils.cryptoUtil import get_password_hash, verify_password
from app.repository.auditor_repository import auditor_repository

router = APIRouter()


# @router.post("/", response_model=AuditorBase)
# async def create_auditor(
#     payload: AuditorCreate,
#     current_user: auditor = Depends(deps.get_current_active_ca),
# ):
#     if await auditor_repository.get_by_email(email=payload.email):
#         raise HTTPException(
#             status_code=400,
#             detail="The user with this username already exists in the database.",
#         )
#     if await auditor_repository.get_by_phone(phone=payload.phone_number):
#         raise HTTPException(
#             status_code=400,
#             detail="The user with this username already exists in the database.",
#         )
#     if await ca_repository.get_by_email(email=payload.email):
#         raise HTTPException(
#             status_code=400,
#             detail="The user with this username already exists in the CA database.",
#         )
#     if await ca_repository.get_by_phone(phone=payload.phone_number):
#         raise HTTPException(
#             status_code=400,
#             detail="The user with this username already exists in the CA database.",
#         )
#     validate_phone_number(payload.phone_number)
#     password_regex(payload.password)
#     payload.password = await get_password_hash(payload.password)
#     payload = AuditorCreateId(
#         **payload.dict(),
#         created_by=current_user.id,
#     )
#     return await auditor_repository.create(payload)


@router.post("/", response_model=AuditorBase)
async def create_auditor(
    payload: AuditorCreate,
    current_user: auditor = Depends(deps.get_current_active_ca),
):
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
    if await ca_repository.get_by_email(email=payload.email):
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the CA database.",
        )
    if await ca_repository.get_by_phone(phone=payload.phone_number):
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the CA database.",
        )
    validate_phone_number(payload.phone_number)
    password_regex(payload.password)
    payload.password = await get_password_hash(payload.password)

    payload_dict = payload.dict()
    if "created_by" in payload_dict:
        payload_dict.pop("created_by")

    payload = AuditorCreateId(
        **payload_dict,
        created_by=current_user.id,
    )
    return await auditor_repository.create(payload)


@router.get("/me")
async def read_user_me(
    current_user: auditor = Depends(deps.get_current_active_auditor),
) -> Any:
    """
    Get current user.
    """
    documents = await auditor_repository.get_auditor_profilePicture(current_user.id)
    result = AuditorInDBBase(
        **current_user,
        profilePicture=documents,
    )
    return result


# @router.put("/password", response_model=Successful)
# async def update_auditor_password(
#     response: ResetAuditorPassword,
#     current_user: auditor = Depends(deps.get_current_active_auditor),
# ) -> Any:
#     user_in = AuditorUpdate(**current_user)
#     if not await verify_password(response.current_password, current_user.password):
#         raise HTTPException(status_code=404, detail="Current password does not match!")
#     if response.current_password is None or response.new_password != response.confirm_password:
#         raise HTTPException(status_code=404, detail="New password does not match!")
#     # password_regex(response.new_password)
#     user_in.password = await get_password_hash(response.new_password)
#     await auditor_repository.update(id=current_user.id, obj_in=user_in)
#     return {"detail": "User's Password updated successfully"}

@router.put("/password", response_model=Successful)
async def update_auditor_password(
    response: ResetAuditorPassword,
    current_user: auditor = Depends(deps.get_current_active_auditor),
) -> Any:
    """
    Update auditor password with password history check
    """
    # Validate the current password
    if not await verify_password(response.current_password, current_user.password):
        raise HTTPException(status_code=404, detail="The password you entered is incorrect.")
    
    # Validate the new password matches confirmation
    if response.current_password is None or response.new_password != response.confirm_password:
        raise HTTPException(status_code=404, detail="Passwords do not match. Please make sure both passwords are identical.")
    
    # Optional: Add password validation
    # password_regex(response.new_password)
    
    # Check if new password is the same as current password
    if response.new_password == response.current_password:
        raise HTTPException(status_code=400, detail="For security reasons, your new password must be different from last 3 passwords you've used in the past.")
    
    # Get password history and check if the new password matches any recent ones
    password_history = await PasswordHistoryRepository.get_password_history(current_user.id, limit=2)
    
    # Check against password history
    for old_password in password_history:
        if await verify_password(response.new_password, old_password['password_hash']):
            raise HTTPException(
                status_code=400,
                detail="For security reasons, your new password must be different from last 3 passwords you've used in the past."
            )
    
    # Save current password to history before updating
    await PasswordHistoryRepository.add_password_to_history(
        current_user.id, 
        current_user.password
    )
    
    # Update the password
    user_in = AuditorUpdate(**current_user)
    user_in.password = await get_password_hash(response.new_password)
    await auditor_repository.update(id=current_user.id, obj_in=user_in)
    # Trim password history
    await PasswordHistoryRepository.trim_password_history(current_user.id, max_entries=5)
    return {"detail": "User's Password updated successfully"}

@router.put("/forgot_password", response_model=Successful)
async def update_auditor_password(
    response: ForgetPassword,
) -> Any:
    user_in = await auditor_repository.get_by_email_or_phone(response.current_email)
    # user_in.password = await get_password_hash(response.new_password)
    # await auditor_repository.update(id=current_user.id, obj_in=user_in)

    return {"detail": user_in}


# @router.put("/", response_model=Successful)
# async def update_auditor(
#     full_name: str = Body(None),
#     email: EmailStr = Body(None),
#     phone_number: str = Body(None),
#     current_user: auditor = Depends(deps.get_current_active_auditor),
# ) -> Any:
#     """
#     Update a user.
#     """
#     user_in = AuditorUpdate(**current_user)
#     if email is not None:
#         if await auditor_repository.get_by_email(email=email):
#             raise HTTPException(
#                 status_code=400,
#                 detail="The user with this username already exists in the database.",
#             )
#         user_in.email = email
#     if phone_number is not None:
#         if await auditor_repository.get_by_phone(phone=phone_number):
#             raise HTTPException(
#                 status_code=400,
#                 detail="The user with this username already exists in the database.",
#             )
#         validate_phone_number(phone_number)
#         user_in.phone_number = phone_number
#     if full_name is not None:
#         user_in.full_name = full_name

#     await auditor_repository.update(id=current_user.id, obj_in=user_in)

#     return {"detail": "User updated successfully"}


@router.post("/profilePicture")
async def upload_profile_picture(
    filetype: str = Form(...),
    filesize: int = Form(...),
    file: UploadFile = File(...),
    current_user: auditor = Depends(deps.get_current_active_auditor),
):
    try:
        # Read file content
        file_content = await file.read()

        # Generate a unique filename
        filename = f"profilePicture.{filetype.split('/')[-1]}"

        # Upload to Azure Storage
        from app.utils.azure_storage import azure_image_storage

        upload_result = await azure_image_storage.upload_image(
            file_content, current_user.id, settings.PROFILEPICTURECONTAINER_NAME, filename, filetype
        )

        # Prepare profile data with image URL
        profile_data = {
            "filename": filename,
            "filetype": filetype,
            "filesize": filesize,
            "container": settings.PROFILEPICTURECONTAINER_NAME,
            "filepath": upload_result["filepath"],
            "auditor_id": current_user.id,
            "image_url": upload_result["image_url"],
            "id": str(uuid.uuid4()),
        }

        # Update or create profile picture record in database
        profile = await auditor_repository.get_auditor_profilePicture(current_user.id)

        if profile:
            # If profile exists, update it
            await auditor_repository.update_profile_picture(current_user.id, profile_data)
        else:
            # If no profile, create a new one
            await auditor_repository.create_profile_picture_with_url(profile_data)

        return {
            "detail": "Profile picture uploaded successfully",
            "image_url": upload_result["image_url"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server issue while uploading file: {str(e)}")


@router.get("/profilePicture")
async def get_profile_picture(
    current_user: auditor = Depends(deps.get_current_active_auditor),
):
    try:
        # Get profile picture info from database
        profile_pic = await auditor_repository.get_auditor_profilePicture(current_user.id)

        if not profile_pic:
            raise HTTPException(status_code=404, detail="Profile picture does not exist")

        # Check if image_url exists
        if hasattr(profile_pic, "image_url") and profile_pic.image_url:
            # Return the direct URL and metadata
            return {
                "image_url": profile_pic.image_url,
                "filetype": profile_pic.filetype,
                "filesize": profile_pic.filesize,
            }
        else:
            # For backwards compatibility with existing records
            return {
                "filepath": profile_pic.filepath,
                "container": profile_pic.container,
                "filetype": profile_pic.filetype,
                "filesize": profile_pic.filesize,
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving profile picture: {str(e)}")


@router.put("/profilePicture")
async def update_profile_picture(
    file: UploadFile = File(...),
    current_user: auditor = Depends(deps.get_current_active_auditor),
):
    """
    Update profile picture using local file storage as a temporary solution
    """
    try:
        # Read file content
        file_content = await file.read()

        # Get file info
        filetype = file.content_type or "image/jpeg"
        filesize = len(file_content)

        # Generate a filename based on user ID and file type
        extension = filetype.split("/")[-1]
        filename = f"{current_user.id}.{extension}"
        file_path = f"static/profiles/{filename}"

        upload_result = await azure_image_storage.upload_image(
            file_content, current_user.id, settings.PROFILEPICTURECONTAINER_NAME, filename, filetype
        )

        # Ensure the directory exists

        # Create a URL that will work with your static file serving
        image_url = upload_result["image_url"]

        # Check if user already has a profile picture
        existing_profile = await auditor_repository.get_auditor_profilePicture(current_user.id)

        if existing_profile:
            # If we added the new method to update with image URL
            # Uncomment this if you added the method:
            # await auditor_repository.update_profile_with_image_url(current_user.id, image_url)

            # Otherwise use the standard update_profile method
            await auditor_repository.update_profile(current_user.id)

            # And manually update the image_url if possible
            if hasattr(auditor_profile.c, "image_url"):
                update_query = (
                    auditor_profile.update()
                    .where(auditor_profile.c.auditor_id == current_user.id)
                    .values(image_url=image_url)
                )
                await database.execute(update_query)
        else:
            # Create new profile picture with the standard method
            profile_data = ProfilePictureCreate(
                filename=filename, filetype=filetype, filesize=filesize, auditor_id=current_user.id
            )
            await auditor_repository.create_profile_picture(profile_data)

            # Then update with image URL if possible
            if hasattr(auditor_profile.c, "image_url"):
                update_query = (
                    auditor_profile.update()
                    .where(auditor_profile.c.auditor_id == current_user.id)
                    .values(image_url=image_url)
                )
                await database.execute(update_query)

        # Return success response with the image URL
        return {"detail": "Profile picture updated successfully", "image_url": image_url}

    except Exception as e:
        # Log the error
        print(f"Error updating profile picture: {str(e)}")
        import traceback

        print(traceback.format_exc())

        # Return error response
        raise HTTPException(
            status_code=500, detail=f"Server issue while updating profile picture: {str(e)}"
        )


@router.delete("/profilePicture")
async def delete_profile_picture(
    current_user: auditor = Depends(deps.get_current_active_auditor),
):
    try:
        # Get profile picture info
        profile_pic = await auditor_repository.get_auditor_profilePicture(current_user.id)

        if not profile_pic:
            raise HTTPException(status_code=404, detail="No profile picture found")

        # Delete from Azure Storage

        await azure_image_storage.delete_image(profile_pic.container, profile_pic.filepath)

        # Remove from database
        await auditor_repository.remove_profile(current_user.id)

        return {"detail": "Profile picture deleted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Server issue while deleting profile picture: {str(e)}"
        )


@router.post("/task/", response_model=Successful)
async def create_auditor_task(
    payload: AuditorTaskBase,
    auditor_id: str,
    current_user: ca = Depends(deps.get_current_active_ca),
):
    user = await base_repository.get(auditor, id=auditor_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The Auditor with this id does not exist in the database",
        )
    if user.created_by != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="You can't create task for this auditor as it is not created by you",
        )
    mapped_paylod = jsonable_encoder(payload)
    result = AuditorTaskCreate(**mapped_paylod, created_by=current_user.id, created_for=auditor_id)
    await auditor_repository.create_task(result)
    return {"detail": "Task Added successfully"}


@router.put("/task/", response_model=Successful)
async def update_auditor_task(
    task_id: str,
    payload: AuditorTaskBase,
    current_user: ca = Depends(deps.get_current_active_ca),
):
    await auditor_repository.update_task(id=task_id, obj_in=payload)
    return {"detail": "Task Updated successfully"}


@router.delete("/task/", response_model=Successful)
async def delete_auditor_task(
    task_id: str,
    current_user: ca = Depends(deps.get_current_active_ca),
):
    await auditor_repository.task_is_active(id=task_id)
    return {"detail": "Task Deleted successfully"}


@router.get("/task/", response_model=List[AuditorTaskDateTime])
async def get_auditor_task(
    skip: int = 0,
    limit: int = 100,
    current_user: auditor = Depends(deps.get_current_active_auditor),
):
    return await auditor_repository.get_list_auditor_task(current_user.id, skip, limit)


@router.get("/user_document/{user_id}")
async def get_user_documents(
    user_id: str, current_user: auditor = Depends(deps.get_current_active_auditor)
):
    """
    Get list of documents of User, logged in as Auditor"""
    documents = await document_repository.get_user_documents(user_id)
    documents_list = []
    for document in documents:
        document_type_id = document["document_type_id"]
        document_type_result = await document_repository.get_documents_type(document_type_id)
        documents_list.append(
            DocumentList(**document, document_file_name=document_type_result.document_name)
        )
    return documents_list


@router.get("/download/user_document/{document_id}")
async def download_user_documents(
    document_id: int,
    current_user: auditor = Depends(deps.get_current_active_auditor),
):
    """
    Downloading documents of User, logged in as Auditor
    It will return a file stream
    """
    try:
        # Get document record from database
        row = await base_repository.get_as_active(documents, id=document_id)
        if not row:
            raise HTTPException(
                status_code=404,
                detail="The document with this id does not exist in the database",
            )

        try:
            # Download the document using azure_image_storage
            file_contents = await azure_image_storage.download_document(row.document_path)

            # Extract filename from the path for the Content-Disposition header
            filename = row.document_path.split("/")[-1]

            # Return as streaming response
            return StreamingResponse(
                iter([file_contents]),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        except Exception as storage_error:
            # Log the error
            print(f"Azure storage error: {str(storage_error)}")
            import traceback

            print(traceback.format_exc())

            # Return appropriate error response
            raise HTTPException(status_code=404, detail="Document file not found in storage")

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        print(f"Error downloading document: {str(e)}")
        import traceback

        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Server issue while downloading file: {str(e)}"
        )


@router.post("/upload/user_document/{user_id}")
async def upload_user_document(
    user_id: str,
    document_name: str = Form(...),
    document_type: DocumentType = Form(...),
    document_type_id: int = Form(...),
    document_size: int = Form(...),
    file: UploadFile = File(...),
    current_user: auditor = Depends(deps.get_current_active_auditor),
):
    """
    Upload a document for a user, logged in as Auditor.

    Args:
        user_id: ID of the user for whom the document is being uploaded
        document_type: Type of document (e.g., image/jpeg, application/pdf)
        document_type_id: ID of the document type (corresponds to entries in document_types table)
        document_size: Size of the document in bytes
        file: The actual file to upload

    Returns:
        JSON response indicating success or error
    """
    try:
        # Verify the user exists
        user = await base_repository.get(users, id=user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="The user with this user_id does not exist in the database",
            )

        # Verify the document type exists
        doc_type = await document_repository.get_document_type_by_id(document_type_id)
        if not doc_type:
            raise HTTPException(
                status_code=404,
                detail=f"The document type with ID {document_type_id} does not exist",
            )

        # Generate a unique filename for the document
        filename = f"{uuid.uuid4()}"
        document_path = f"{user_id}/{filename}"
        file_content = await file.read()

        # Upload file to blob storage
        upload_result = await azure_image_storage.upload_document(
            file_content,
            current_user.id,
            settings.PROFILEPICTURECONTAINER_NAME,
            filename,
            document_type,
        )

        # Create document record in database
        document_data = DocumentCreate(
            document_name=document_name,
            document_type=document_type.value,  # Convert enum to string value
            document_size=document_size,
            status="pending",  # Default status for newly uploaded documents
            user_id=user_id,
            document_type_id=document_type_id,
            document_path=upload_result["document_url"],
        )

        document_id = await document_repository.create(document_data)

        return {"detail": "Document uploaded successfully", "document_id": document_id}

    except Exception as e:
        # Log the exception for debugging
        print(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail="Server issue while uploading file")


@router.put("/update/user_document/{document_id}")
async def update_document_status(
    document_id: int,
    status: DocumentStatus,
    current_user: auditor = Depends(deps.get_current_active_auditor),
):
    """
    Updating  documents as Admin, logged in as Admin
    """

    row = await base_repository.get_as_active(documents, id=document_id)
    if not row:
        raise HTTPException(
            status_code=404,
            detail="The document with this id does not exist in the database",
        )
    await document_repository.update(document_id, status)
    return {"detail": "Status updated successfully"}


@router.delete("/document/user_document/{document_id}")
async def delete_document(
    document_id: int,
    current_user: auditor = Depends(deps.get_current_active_auditor),
):
    """
    Deleting documents as Admin, logged in as Admin
    """
    try:
        # Get the document record from database
        row = await base_repository.get_as_active(documents, id=document_id)
        if not row:
            raise HTTPException(
                status_code=404,
                detail="The document with this id does not exist in the database",
            )

        # Delete the document using azure_image_storage utility
        delete_success = await azure_image_storage.delete_document(row.document_path)

        if delete_success:
            # Mark document as inactive in the database
            await document_repository.update_document_status(False, document_id)
            return {"detail": "Document deleted successfully"}
        else:
            # If document couldn't be deleted from storage
            raise HTTPException(status_code=500, detail="Could not delete document from storage")

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        print(f"Error deleting document: {str(e)}")
        import traceback

        print(traceback.format_exc())

        # Return error response
        raise HTTPException(status_code=500, detail="Server issue while deleting file")


@router.put("/update/user_document")
async def update_user_document(
    document_id: int = Form(...),
    document_name: Optional[str] = Form(None),
    document_type: Optional[DocumentType] = Form(None),
    document_size: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: auditor = Depends(deps.get_current_active_auditor),
):
    """
    Update a user document as an Auditor.

    Allows auditors to update a document's name, type, or file content.
    At least one of document_name or file must be provided.
    """
    try:
        # Verify document exists
        document = await base_repository.get_as_active(documents, id=document_id)
        if not document:
            raise HTTPException(
                status_code=404, detail="The document with this ID does not exist in the database"
            )

        # Update document name if provided
        if document_name:
            await document_repository.update_document_name(document_id, document_name)

        # Update file content if provided
        if file:
            blob_client = container_client.get_blob_client(document.document_path)
            blob_client.upload_blob(await file.read(), overwrite=True)

            # Update document metadata
            doc_type = document_type.value if document_type else document.document_type
            doc_size = document_size or file.size
            await document_repository.update_document_metadata(document_id, doc_type, doc_size)

        return {"detail": "Document updated successfully", "document_id": document_id}

    except Exception as e:
        print(f"Error updating document: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Server issue while updating document: {str(e)}"
        )


@router.get("/download/all_user_document/{user_id}")
async def download_all_user_documents(
    user_id: str,
    current_user: auditor = Depends(deps.get_current_active_auditor),
):
    """
    Downloading  documents of User, logged in as Auditor
    It will download all the documents of the user in a zip file"""
    try:
        # Get all blobs in the user's folder
        user_folder = f"{user_id}/"
        blobs = container_client.list_blobs(name_starts_with=user_folder)

        # Stream each file to the client
        return StreamingResponse(
            iter_files(blobs, container_client, user_id),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={user_id}_files.zip"},
        )

    except Exception:
        raise HTTPException(status_code=404, detail="Sever isuue while downloading files.")


async def iter_files(blobs, container_client, user_id):
    zip_data = io.BytesIO()
    with zipfile.ZipFile(zip_data, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for blob in blobs:
            blob_client = container_client.get_blob_client(blob)
            file_data = blob_client.download_blob().readall()
            file_name = os.path.basename(blob.name)
            file_name = user_id + "/" + file_name
            # Fetching fie extension
            # Doing this because the file extension is not present in the blob name
            # and we need to store the file with the same extension
            file_extension = await document_repository.file_extension(file_name)
            split_parts = file_extension.split("/")
            zip_file.writestr(f"{file_name}.{split_parts[-1]}", file_data)

    zip_data.seek(0)
    while True:
        data = zip_data.read(4096)
        if not data:
            break
        yield data


@router.put("/update/user")
async def update_user(
    object: UserUpdateDeatils,
    user_id: str,
    current_user: auditor = Depends(deps.get_current_active_auditor),
):
    objin = await base_repository.get(users, id=user_id)
    if not objin:
        raise HTTPException(
            status_code=404,
            detail="The user with this userid does not exist in the database",
        )
    payload = UserUpdateDeatils(**objin)
    if object.tax_payer_type is not None:
        payload.tax_payer_type = object.tax_payer_type
    if object.tax_slab is not None:
        payload.tax_slab = object.tax_slab
    if object.category is not None:
        payload.category = object.category

    await user_repository.update_user_details(payload, user_id)
    return {"detail": "User updated successfully"}
