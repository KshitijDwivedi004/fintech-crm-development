from fastapi import APIRouter, HTTPException, Path, Query, status
from typing import Any, List, Optional
from starlette.responses import StreamingResponse

from app.schemas.credit_report import (
    OTPGenerateRequest,
    OTPGenerateResponse,
    CreditReportRequest,
    CreditReportResponse,
    APIErrorResponse,
    CreditReportListResponse,
)
from app.services.credit_report_service import credit_report_service
from app.services.cibil_pdf_service import cibil_pdf_service
from app.core.logger import logger

router = APIRouter()


@router.post(
    "/generate-otp",
    response_model=OTPGenerateResponse,
    responses={400: {"model": APIErrorResponse}, 500: {"model": APIErrorResponse}},
    summary="Generate OTP for credit report",
)
async def generate_otp(request: OTPGenerateRequest) -> Any:
    """
    Generate OTP for credit report verification.

    - **phone_number**: Phone number to receive OTP
    - **orderid**: Optional order ID
    """
    try:
        response = await credit_report_service.generate_otp(
            phone_number=request.phone_number, orderid=request.orderid
        )

        if response.get("status") != "success":
            logger.error(f"OTP generation failed: {response.get('mess')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to generate OTP: {response.get('mess')}",
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_otp: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post(
    "/credit-report",
    response_model=CreditReportResponse,
    responses={400: {"model": APIErrorResponse}, 500: {"model": APIErrorResponse}},
    summary="Get credit report from Equifax",
)
async def get_credit_report(request: CreditReportRequest) -> Any:
    """
    Get credit report from Equifax.

    - **fname**: First name
    - **lname**: Last name
    - **dob**: Date of birth in DD-MM-YYYY format
    - **phone_number**: Phone number
    - **pan_num**: PAN number
    - **otp**: OTP received
    - **orderid**: Optional order ID
    - **user_id**: Optional user ID for association
    """
    try:
        response = await credit_report_service.get_credit_report(
            fname=request.fname,
            lname=request.lname,
            dob=request.dob,
            phone_number=request.phone_number,
            pan_num=request.pan_num,
            otp=request.otp,
            orderid=request.orderid,
            check_db_first=True,  # Check database first before calling API
            user_id=request.user_id,
            generate_pdf=True,  # Generate and store PDF
        )

        if response.get("status") != "success":
            logger.error(f"Credit report fetch failed: {response.get('mess')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch credit report: {response.get('mess')}",
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_credit_report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get(
    "/credit-reports",
    response_model=CreditReportListResponse,
    responses={400: {"model": APIErrorResponse}, 500: {"model": APIErrorResponse}},
    summary="Public endpoint to search credit reports",
)
async def search_credit_reports(
    search: Optional[str] = Query(None, description="Search term for name, PAN, or phone number"),
    limit: int = Query(100, description="Limit the number of results"),
    skip: int = Query(0, description="Skip the first N results"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
) -> Any:
    """
    Public endpoint to search credit reports.
    No authentication required.

    - **search**: Optional search term for name, PAN, or phone number
    - **limit**: Limit the number of results (default: 100)
    - **skip**: Skip the first N results (default: 0)
    - **user_id**: Optional user ID to filter reports
    """
    try:
        if search:
            response = await credit_report_service.search_reports(search, limit, skip, user_id)
        else:
            response = await credit_report_service.get_all_reports(limit, skip, user_id)

        if response.get("status") != "success":
            logger.error(f"Credit report search failed: {response.get('mess')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to search credit reports: {response.get('mess')}",
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search_credit_reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.delete(
    "/credit-report/{report_id}",
    responses={
        400: {"model": APIErrorResponse},
        404: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
    summary="Delete a credit report",
)
async def delete_credit_report(
    report_id: int = Path(..., description="ID of the credit report to delete")
) -> Any:
    """
    Delete a credit report by ID.
    No authentication required.

    - **report_id**: ID of the credit report to delete
    """
    try:
        response = await credit_report_service.delete_report(report_id)

        if response.get("status") != "success":
            if "not found" in response.get("mess", "").lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report not found: {response.get('mess')}",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to delete report: {response.get('mess')}",
                )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_credit_report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


# New PDF-related endpoints


@router.delete(
    "/delete-raw-data-by-phone/{phone_number}",
    responses={
        400: {"model": APIErrorResponse},
        404: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
    summary="Delete CIBIL raw data by phone number",
)
async def delete_cibil_raw_data_by_phone(
    phone_number: str = Path(..., description="User's phone number")
) -> Any:
    """
    Delete CIBIL raw data for a user by phone number.
    This will soft delete the record in the credit_reports table.

    - **phone_number**: The phone number linked to the CIBIL report to delete
    """
    try:
        from app.repository.credit_report_repository import credit_report_repository

        # Check if report exists
        report = await credit_report_repository.get_by_phone(phone_number)
        if not report:
            return {
                "status": "error",
                "code": "ERR",
                "mess": f"No CIBIL report found for phone number {phone_number}",
                "data": None,
            }

        # Soft delete the report(s) for this phone number
        success = await credit_report_repository.delete_by_phone(phone_number)

        if success:
            return {
                "status": "success",
                "code": "TXN",
                "mess": f"CIBIL report for phone number {phone_number} successfully deleted",
                "data": None,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete CIBIL report for phone number {phone_number}",
            )

    except Exception as e:
        logger.error(f"Error deleting CIBIL raw data by phone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get(
    "/pdf-by-phone/{phone_number}",
    responses={
        400: {"model": APIErrorResponse},
        404: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
    summary="Get CIBIL PDF documents by phone number",
)
async def get_cibil_pdf_by_phone(
    phone_number: str = Path(..., description="User's phone number")
) -> Any:
    """
    Get CIBIL PDF documents for a user by phone number.

    - **phone_number**: The phone number to search for
    """
    try:
        response = await credit_report_service.get_cibil_pdf_by_phone(phone_number)

        if response.get("status") != "success":
            if "not found" in response.get("mess", "").lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=response.get("mess"),
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=response.get("mess"),
                )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_cibil_pdf_by_phone: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.delete(
    "/delete-raw-data/{phone_number}",
    responses={
        400: {"model": APIErrorResponse},
        404: {"model": APIErrorResponse},
        500: {"model": APIErrorResponse},
    },
    summary="Delete raw CIBIL data by phone number",
)
async def delete_raw_cibil_data(
    phone_number: str = Path(..., description="User's phone number")
) -> Any:
    """
    Delete raw CIBIL data for a user by phone number.

    - **phone_number**: Phone number associated with the CIBIL data
    """
    try:
        # Import directly to avoid circular imports
        from app.repository.credit_report_repository import credit_report_repository

        # Perform the deletion
        result = await credit_report_repository.soft_delete_by_phone(phone_number)

        if result:
            return {"detail": "CIBIL data deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No CIBIL data found for this phone number",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_raw_cibil_data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get(
    "/view-pdf/{document_id}",
    response_class=StreamingResponse,
    responses={404: {"model": APIErrorResponse}, 500: {"model": APIErrorResponse}},
    summary="View CIBIL report PDF",
)
async def view_cibil_pdf(document_id: int = Path(..., description="Document ID")) -> Any:
    """
    View a CIBIL report PDF.

    - **document_id**: ID of the document to view
    """
    try:
        return await cibil_pdf_service.get_cibil_pdf(document_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in view_cibil_pdf: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get(
    "/download-pdf/{document_id}",
    response_class=StreamingResponse,
    responses={404: {"model": APIErrorResponse}, 500: {"model": APIErrorResponse}},
    summary="Download CIBIL report PDF",
)
async def download_cibil_pdf(document_id: int = Path(..., description="Document ID")) -> Any:
    """
    Download a CIBIL report PDF.

    - **document_id**: ID of the document to download
    """
    try:
        return await cibil_pdf_service.download_cibil_pdf(document_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in download_cibil_pdf: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.delete(
    "/delete-pdf/{document_id}",
    responses={404: {"model": APIErrorResponse}, 500: {"model": APIErrorResponse}},
    summary="Delete CIBIL report PDF",
)
async def delete_cibil_pdf(document_id: int = Path(..., description="Document ID")) -> Any:
    """
    Delete a CIBIL report PDF.

    - **document_id**: ID of the document to delete
    """
    try:
        return await cibil_pdf_service.delete_cibil_pdf(document_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_cibil_pdf: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
