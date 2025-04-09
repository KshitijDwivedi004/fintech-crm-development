import datetime
import uuid
from typing import Optional, Dict, Any

from app.core.config import settings
from app.db.session import database
from app.models.user import documents
from app.repository.user_repository import user_repository
from app.repository.documents_repository import document_repository
from app.utils.azur_blob import container_client
from app.schemas.document import DocumentCreate, DocumentType
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
import io


class CibilPdfService:
    """Service for handling CIBIL report PDF operations"""

    async def store_cibil_pdf(
        self,
        pdf_data: bytes,
        phone_number: str,
        pan_number: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Store a CIBIL report PDF and associate it with a user

        Args:
            pdf_data: The binary PDF data
            phone_number: The user's phone number
            pan_number: Optional PAN number
            user_id: Optional user ID - if not provided, will look up by phone number

        Returns:
            Dict with document information
        """
        try:
            # If user_id is not provided, try to find user by phone number
            if not user_id:
                user = await user_repository.get_by_phone(phone_number)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found with this phone number",
                    )
                user_id = user.id

            # Get document type ID for CIBIL reports (assuming it exists)
            document_types = await document_repository.get_document_type_list()
            cibil_doc_type = next(
                (
                    doc_type
                    for doc_type in document_types
                    if "cibil" in doc_type["document_name"].lower()
                ),
                None,
            )

            if not cibil_doc_type:
                # Use a default document type if CIBIL type doesn't exist
                cibil_doc_type = {"id": 1, "document_name": "CIBIL Report"}

            # Generate a unique path for the document
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = f"CIBIL_Report_{phone_number}_{timestamp}.pdf"
            path = f"{user_id}/cibil/{file_name}"

            # Create document in database
            document_data = DocumentCreate(
                document_type=DocumentType.pdf.value,
                document_size=len(pdf_data),
                status="completed",
                user_id=user_id,
                document_type_id=cibil_doc_type["id"],
                document_path=path,
                document_name=f"CIBIL Report - {timestamp}",
            )

            document_id = await document_repository.create(document_data)

            # Update the path to include the document ID for uniqueness
            path = f"{user_id}/cibil/{document_id}_{file_name}"
            await document_repository.update_document_path(path, document_id)

            # Upload PDF to blob storage
            blob_client = container_client.get_blob_client(path)
            blob_client.upload_blob(pdf_data, overwrite=True)

            return {
                "id": document_id,
                "document_path": path,
                "document_type": DocumentType.pdf.value,
                "document_name": f"CIBIL Report - {timestamp}",
                "document_size": len(pdf_data),
                "user_id": user_id,
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error storing CIBIL PDF: {str(e)}",
            )

    async def get_cibil_pdf(self, document_id: int) -> StreamingResponse:
        """
        Get a CIBIL report PDF for viewing or downloading

        Args:
            document_id: The ID of the document

        Returns:
            StreamingResponse containing the PDF data
        """
        try:
            # Get document information
            document = await document_repository.get_document_by_id(document_id)
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )

            # Get the file from blob storage
            blob_client = container_client.get_blob_client(document.document_path)
            file_content = blob_client.download_blob().readall()

            # Return as a streaming response
            return StreamingResponse(
                io.BytesIO(file_content),
                media_type="application/pdf",
                headers={"Content-Disposition": f"inline; filename=CIBIL_Report.pdf"},
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving CIBIL PDF: {str(e)}",
            )

    async def download_cibil_pdf(self, document_id: int) -> StreamingResponse:
        """
        Download a CIBIL report PDF

        Args:
            document_id: The ID of the document

        Returns:
            StreamingResponse with attachment disposition for download
        """
        try:
            # Get document information
            document = await document_repository.get_document_by_id(document_id)
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )

            # Get the file from blob storage
            blob_client = container_client.get_blob_client(document.document_path)
            file_content = blob_client.download_blob().readall()

            # Return as a streaming response with attachment disposition
            return StreamingResponse(
                io.BytesIO(file_content),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=CIBIL_Report.pdf"},
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error downloading CIBIL PDF: {str(e)}",
            )

    async def delete_cibil_pdf(self, document_id: int) -> Dict[str, str]:
        """
        Delete a CIBIL report PDF

        Args:
            document_id: The ID of the document

        Returns:
            Dict with status message
        """
        try:
            # Get document information
            document = await document_repository.get_document_by_id(document_id)
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )

            # Delete from blob storage
            try:
                blob_client = container_client.get_blob_client(document.document_path)
                blob_client.delete_blob()
            except Exception as e:
                # Log error but continue (soft delete from DB)
                print(f"Error deleting blob: {str(e)}")

            # Update document status in database (soft delete)
            await document_repository.update_document_status(False, document_id)

            return {"detail": "CIBIL report deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting CIBIL PDF: {str(e)}",
            )


# Create singleton instance
cibil_pdf_service = CibilPdfService()
