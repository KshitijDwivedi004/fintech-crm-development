import os
import re
from datetime import datetime
from typing import Any, List, Union, Optional
from app.schemas.user import (
    UserId,
    TaxSlab,
    Category,
    TaxPayerType,
    NameOrder,
    CombinedDataResponse,
)
from app.api.api_v1.deps import get_current_active_user
from app.schemas.user import (
    UserFull,
    UserCreateManual,
    UserUpdateRequest,
    UserBulkUpload,
    BulkUploadResponse,
)

from app.repository import credit_report_repository
from app.services import credit_report_service
from fastapi import status, HTTPException
from app.repository.ca_repository import ca_repository
from app.repository.auditor_repository import auditor_repository
from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Query, UploadFile
from starlette.responses import StreamingResponse
from app.service.external_service import external_repository
from app.api.api_v1 import deps
from app.models.user import documents, documents_type, users
from app.repository.base_repository import base_repository
from app.repository.documents_repository import document_repository
from app.repository.user_repository import user_repository
from app.schemas.document import (
    DocumentBase,
    DocumentCreate,
    DocumentId,
    DocumentList,
    DocumentName,
    DocumentStatus,
    DocumentType,
    DocumentUpdate,
)
from pydantic import EmailStr
from app.services.lead_service import lead_service

from app.schemas.user import (
    Category,
    NameOrder,
    TaxPayerType,
    TaxSlab,
    UserBase,
    UnifiedLeadBase,
    UserCreate,
    UserCreateKafka,
    UserId,
    UserInDBBase,
)
from app.utils.azur_blob import container_client
from fastapi import UploadFile, File, Depends, HTTPException, status, Path
from pydantic import ValidationError
import csv
from io import StringIO
from datetime import datetime
from typing import List
import logging
import pandas as pd
from io import BytesIO


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter()


@router.get("/get-users", response_model=dict[str, Union[int, List[UserId]]])
async def get_lists_users(
    query: str = None,
    tax_slab: TaxSlab = None,
    category: Category = None,
    type: TaxPayerType = None,
    name_order: NameOrder = None,
    skip: int = 0,
    limit: int = 100,
    current_user: users = Depends(deps.get_current_active_admin_ca_auditor),
) -> Any:
    """
    Retrieve users.
    only admin, CA and auditor can access this endpoint
    """
    search_query = {}

    if query:
        if re.match(r"^\d+$", query):
            search_query["phone_number"] = query
        else:
            search_query["full_name"] = query
    if tax_slab:
        search_query["tax_slab"] = tax_slab
    if category:
        search_query["category"] = category
    if type:
        search_query["tax_payer_type"] = type
    documents_type_count = await document_repository.get_documents_type_count()
    list_users = await user_repository.get_list_users(
        name_order, search_query, skip=skip, limit=limit
    )
    count = await user_repository.users_count(search_query, name_order)
    temp_users = []
    for user in list_users:
        user_id = user["id"]
        documnets_counts = await document_repository.get_user_documents_count(user_id)
        temp_users.append(UserId(**user, documents_count=documnets_counts))
    return {
        "total_users": count,
        "total_documents_type": documents_type_count,
        "users": temp_users,
    }


@router.put("/upload-users")
async def upload_user_basic_as_user(
    payload: UserCreate,
    current_user: users = Depends(deps.get_current_active_user),
):
    """
    Update user baic details
    User can update his/her basic details
    """

    await user_repository.update_basic_details(payload, current_user.id)
    return {"detail": "User Updated successfully"}


@router.get("/get-by-phone/{request}", response_model=UserInDBBase)
async def get_user_detail_using_phone(
    request: str,
    current_user: users = Depends(deps.get_current_active_admin_ca_auditor),
):
    """
    Retrieve user details and documents using phone number
    only admin, CA and auditor can access this endpoint"""
    user = await user_repository.get_by_phone(request)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the database",
        )
    documents = await document_repository.get_user_documents(user.id)
    documents_list = []
    for document in documents:
        document_type_id = document["document_type_id"]
        document_type_result = await document_repository.get_documents_type(document_type_id)
        documents_list.append(
            DocumentList(**document, document_name=document_type_result.document_name)
        )
    return UserInDBBase(
        **user,
        documents=documents_list,
    )


@router.get("/combined", response_model=CombinedDataResponse)
async def get_combined_lead_data(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(
        None, description="Search by name, loan type, source, employment type"
    ),
    date_range: Optional[str] = Query(
        None,
        description="Predefined date range (all_time, last_7_days, last_30_days, last_90_days, last_180_days, last_365_days)",
    ),
    date_from: Optional[datetime] = Query(None, description="Custom date range start"),
    date_to: Optional[datetime] = Query(None, description="Custom date range end"),
    loan_amount: Optional[str] = Query(
        None,
        description="Loan amount range (up_to_25_lakhs, 25_lakhs_to_2_crores, 2_crores_to_10_crores, above_10_crores)",
    ),
    employment_type: Optional[str] = Query(
        None, description="Employment type (Salaried, Business)"
    ),
    cibil_score: Optional[str] = Query(
        None, description="CIBIL score range (300_500, 501_700, 701_850)"
    ),
    sources: Optional[List[str]] = Query(
        None,
        description="Sources (Facebook, Website, Instagram, chatbot, beehiiv, strapi_loan, strapi_cibil)",
    ),
    current_user: Any = Depends(deps.get_current_active_admin_ca_auditor),
):
    """
    Get combined lead data with advanced filtering and pagination.
    """
    combined_data = await lead_service.get_combined_leads(
        page=page,
        page_size=page_size,
        search=search,
        date_range=date_range,
        date_from=date_from,
        date_to=date_to,
        loan_amount=loan_amount,
        employment_type=employment_type,
        cibil_score=cibil_score,
        sources=sources,
    )

    return combined_data


@router.post("/manual-create", response_model=UserFull)
async def create_user_manually(
    payload: UserCreateManual = Body(..., embed=True),
    current_user: users = Depends(deps.get_current_active_admin_ca_auditor),
):
    """
    Manually create a new user with required fields
    Only admin, CA and auditor can access this endpoint
    """
    # try:
    new_user = await user_repository.create_manual(payload)
    return new_user
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating user"
    #     )


@router.put("/update-user", response_model=UserFull)
async def update_user(
    payload: UserUpdateRequest = Body(...),
    current_user: users = Depends(deps.get_current_active_admin_ca_auditor),
):
    """
    Update user details by ID.
    Supports partial updates - only specified fields will be updated.
    Only admin, CA and auditor can access this endpoint.
    """
    try:
        # Make sure at minimum the user ID is provided
        if not payload.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User ID is required"
            )

        updated_user = await user_repository.update_user(payload)
        return updated_user
    except HTTPException as http_exc:
        # Pass through HTTP exceptions as they are
        raise http_exc
    except Exception as e:
        # Log the error for debugging
        print(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}",
        )


field_mapping = {
    "Full Name": "full_name",
    "Contact Number": "phone_number",
    "Email ID": "email",
    "Location": "location",
    "PAN Number": "pan_number",
    "CIBIL": "cibil_score",
    "Lead Source": "source",
    "Employment Type": "employment_type",
    "Annual Income": "annual_income",
    "Loan Type": "loan_purpose",
    "Loan Amount Required": "loan_amount_required",
}


@router.post("/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_users(
    file: UploadFile = File(...),
    current_user: users = Depends(deps.get_current_active_admin_ca_auditor),
):
    try:
        contents = await file.read()

        if file.filename.endswith(".xlsx"):
            df = pd.read_excel(BytesIO(contents), dtype=str).fillna("")
        elif file.filename.endswith(".csv"):
            df = pd.read_csv(BytesIO(contents), dtype=str).fillna("")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file format. Only .csv and .xlsx are allowed.",
            )

        rows = df.to_dict("records")
        created_users = []

        # Normalize field_mapping keys to lowercase
        normalized_field_mapping = {k.lower(): v for k, v in field_mapping.items()}

        for idx, row in enumerate(rows, start=1):
            try:
                # Normalize row keys to lowercase
                normalized_row = {k.lower(): v for k, v in row.items()}

                # Map headers to model fields, ensuring values are strings and stripped
                mapped_row = {}
                for k, v in normalized_row.items():
                    if k in normalized_field_mapping:
                        cleaned_value = str(v).strip() if v is not None else ""
                        mapped_row[normalized_field_mapping[k]] = cleaned_value
                logger.debug(f"Processed Row {idx}: Mapped Row: {mapped_row}")

                # Check if at least one of email or phone_number is present
                if not mapped_row.get("email") and not mapped_row.get("phone_number"):
                    logger.error(
                        f"Processed Row {idx}: Validation Error: Either email or phone_number must be present"
                    )
                    continue  # Skip this row

                # Validate row using Pydantic schema
                user_bulk = UserBulkUpload.parse_obj(mapped_row)
                logger.debug(f"Processed Row {idx}: Validated User Bulk: {user_bulk}")

                # Convert annual income to monthly
                monthly_income = user_bulk.annual_income / 12 if user_bulk.annual_income else None
                user_manual = UserCreateManual(
                    full_name=user_bulk.full_name,
                    phone_number=user_bulk.phone_number,
                    email=user_bulk.email,
                    pan_number=user_bulk.pan_number,
                    cibil_score=user_bulk.cibil_score,
                    source=user_bulk.source,
                    employment_type=user_bulk.employment_type,
                    loan_purpose=user_bulk.loan_purpose,
                    loan_amount=user_bulk.loan_amount_required,
                    location=user_bulk.location,
                    monthly_income=monthly_income,
                    country_code=user_bulk.phone_number[:2] if user_bulk.phone_number else None,
                )
                logger.debug(f"Processed Row {idx}: Created User Manual: {user_manual}")

                # Create user
                created_user = await user_repository.create_manual(user_manual)
                created_users.append(user_manual.full_name)
                logger.debug(
                    f"Processed Row {idx}: User Created Successfully: {user_manual.full_name}"
                )

            except ValidationError as e:
                logger.error(f"Processed Row {idx}: Validation Error: {e}")
            except HTTPException as http_exc:
                logger.error(f"Processed Row {idx}: HTTP Exception: {http_exc.detail}")
            except Exception as e:
                logger.error(f"Processed Row {idx}: Error Processing Row: {e}")

        logger.info(f"Total Users Created: {len(created_users)}")
        return BulkUploadResponse(detail=f"{len(created_users)} users created successfully")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in Bulk Upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the uploaded file.",
        )


@router.get("/get-using-id", response_model=UserInDBBase)
async def get_user_detail_using_id(
    user_id: Optional[str] = None,
    current_user: users = Depends(deps.get_current_active_admin_ca_auditor),
):
    """
    Retrieve user details and documents using user id
    Only admin, CA and auditor can access this endpoint
    """
    # Handle null or empty user_id
    if not user_id or user_id == "null":
        raise HTTPException(
            status_code=404,
            detail="Invalid user ID provided",
        )

    user = await base_repository.get(users, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this ID does not exist in the database",
        )
    documents = await document_repository.get_user_documents(user.id)
    documents_list = []
    for document in documents:
        document_type_id = document["document_type_id"]
        document_type_result = await document_repository.get_documents_type(document_type_id)
        documents_list.append(
            DocumentList(**document, document_names=document_type_result.document_name)
        )
    return UserInDBBase(
        **user,
        documents=documents_list,
    )


@router.get("/me/details", response_model=UserInDBBase)
async def get_user_detail_as_user(
    current_user: users = Depends(deps.get_current_active_user),
):
    """
    Retrieve user details and documents
    User can access this endpoint"""
    user = await base_repository.get(users, id=current_user.id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the database",
        )
    documents = await document_repository.get_user_documents(user.id)
    return UserInDBBase(
        **user,
        documents=documents,
    )


@router.get("/recent_users/{days}")
async def get_recent_users(
    days: int,
    current_user: users = Depends(deps.get_current_active_admin_ca_auditor),
):
    """
    Retrieve users that were created within the last n days.
    only admin, CA and auditor can access this endpoint"""
    return await user_repository.get_recent_users(days)


@router.get("/recent_documents/{days}")
async def get_recent_documents(
    days: int,
    current_user: users = Depends(deps.get_current_active_admin_ca_auditor),
):
    """
    Retrieve documents that were created within the last n days.
    only admin, CA and auditor can access this endpoint"""
    return await document_repository.get_recent_documents(days)


## Todo make api for editing user details as Admin


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: users = Depends(deps.get_current_active_superuser),
):
    """
    Delete user.
    Only superuser can delete user"""
    row = await base_repository.get(users, id=user_id)
    if not row:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the database",
        )
    await user_repository.set_is_active(user_id, False)
    return {"detail": "User deleted successfully"}


@router.post("/upload", response_model=DocumentId)
async def upload_file_as_user(
    document_type_id: int = Form(),
    document_type: DocumentType = Form(),
    document_size: int = Form(),
    file: UploadFile = File(...),
    current_user: users = Depends(deps.get_current_active_user),
):
    """
    Uploading documents as User, logged in as user
    """

    document = await document_repository.get_document_type_by_id(document_type_id)
    if not document:
        raise HTTPException(
            status_code=404,
            detail="The document with this id does not exist in the database",
        )
    document_key = document["document_key"]
    path = f"{current_user.id}/{document_key}"
    payload = DocumentCreate(
        document_type=document_type,
        document_size=document_size,
        status="pending",
        user_id=current_user.id,
        document_type_id=document_type_id,
        document_path=path,
    )
    id = await document_repository.create(payload)
    path += f"_{id}"
    await document_repository.update_document_path(path, id)
    try:
        blob_client = container_client.get_blob_client(path)
        blob_client.upload_blob(await file.read())
        return DocumentId(**payload.dict(), id=id)
    except Exception:
        await document_repository.update_document_status(False, id)
        raise HTTPException(status_code=404, detail="Sever isuue while uploading file.")


@router.put("/update/document")
async def update_document_as_user(
    document_id: int = Form(...),
    document_name: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: users = Depends(deps.get_current_active_user),
):
    """
    Update a document's name and/or file content.
    Users can update their own documents by providing the document ID and
    optionally a new name or file content.
    """
    try:
        # Verify document exists and belongs to the current user
        document = await document_repository.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="The document with this ID does not exist")

        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="You don't have permission to update this document"
            )

        # Update document name if provided
        if document_name:
            await document_repository.update_document_name(document_id, document_name)

        # Update file content if provided
        if file:
            blob_client = container_client.get_blob_client(document.document_path)
            blob_client.upload_blob(await file.read(), overwrite=True)

            # Update document metadata
            document_size = file.size
            document_type = file.content_type
            await document_repository.update_document_metadata(
                document_id, document_type, document_size
            )

        return {"detail": "Document updated successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Server issue while updating document: {str(e)}"
        )


@router.get("/download/{document_type_id}")
async def download_file_as_user(
    document_type_id: int,
    current_user: users = Depends(deps.get_current_active_user),
):
    """
    Downloading  documents as User, logged in as user
    """
    try:
        row = await document_repository.get_documents_using_id(current_user.id, document_type_id)
        if not row:
            raise HTTPException(
                status_code=404,
                detail="The document with this id does not exist in the database",
            )

        blob_client = container_client.get_blob_client(row.document_path)
        file_contents = blob_client.download_blob()
        return StreamingResponse(
            iter([file_contents.readall()]), media_type="application/octet-stream"
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")


@router.get("/with-cibil/{user_id}")
async def get_user_with_cibil_data(
    user_id: str,
    current_user: users = Depends(deps.get_current_active_admin_ca_auditor),
):
    """
    Retrieve user details and associated CIBIL report documents
    Only admin, CA and auditor can access this endpoint
    """
    # Get user data
    user = await base_repository.get(users, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this ID does not exist in the database",
        )

    # Get user documents
    documents_list = await document_repository.get_user_documents(user.id)

    # Get CIBIL PDFs if the user has a phone number
    cibil_documents = []
    if user.phone_number:
        try:
            # Import the cibil_pdf_service to access its functions
            from app.services.cibil_pdf_service import cibil_pdf_service

            # Get CIBIL documents for this phone number
            cibil_response = await credit_report_service.get_cibil_pdf_by_phone(user.phone_number)

            if cibil_response.get("status") == "success":
                cibil_documents = cibil_response.get("data", {}).get("documents", [])
        except Exception as e:
            # Log error but continue with the rest of the data
            logger.error(f"Error fetching CIBIL documents: {str(e)}")

    # Combine regular user data with CIBIL documents
    return {**user, "documents": documents_list, "cibil_documents": cibil_documents}


@router.get("/with-cibil-data/{user_id}")
async def get_user_with_cibil_data(
    user_id: str,
    current_user: users = Depends(deps.get_current_active_admin_ca_auditor),
):
    """
    Retrieve user details and associated CIBIL data including reports and PDF documents
    Only admin, CA and auditor can access this endpoint
    """
    # Get user data
    user = await base_repository.get(users, id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this ID does not exist in the database",
        )

    # Get user documents
    documents_list = await document_repository.get_user_documents(user.id)

    # Get CIBIL data if the user has a phone number
    cibil_documents = []
    raw_report_data = None

    if user.phone_number:
        try:
            # Import the credit report service to access CIBIL data
            from app.services.credit_report_service import credit_report_service
            from app.repository.credit_report_repository import credit_report_repository

            # Get CIBIL report from repository if exists
            recent_report = await credit_report_repository.get_recent_report(
                pan_number=user.pan_number or "",
                phone_number=user.phone_number,
                days=365,  # Look for reports within the last year
            )

            if recent_report:
                raw_report_data = recent_report.get("raw_data")

            # Get CIBIL PDF documents for this phone number
            cibil_response = await credit_report_service.get_cibil_pdf_by_phone(user.phone_number)

            if cibil_response.get("status") == "success":
                cibil_documents = cibil_response.get("data", {}).get("documents", [])

        except Exception as e:
            # Log error but continue with the rest of the data
            logger.error(f"Error fetching CIBIL data: {str(e)}")

    # Combine all data
    response_data = {
        **dict(user),
        "documents": documents_list,
        "cibil_documents": cibil_documents,
        "cibil_raw_data": raw_report_data,
    }

    return response_data


@router.get("/document_type/list")
async def get_document_list():
    return await document_repository.get_document_type_list()
