import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.config import settings
from app.core.logger import logger
from app.repository.credit_report_repository import credit_report_repository
from app.services.cibil_pdf_service import cibil_pdf_service
from app.services.pdfGenerationService import generateCibilReportPDF
from io import BytesIO


class CreditReportService:
    """
    Service to handle credit report API interactions and database operations
    """

    def __init__(self):
        # API credentials - these should come from environment variables in settings
        # Add these to your .env file and update the Settings class in config.py
        self.apiid = settings.CREDIT_REPORT_API_ID
        self.token = settings.CREDIT_REPORT_API_TOKEN

        # API endpoints
        self.otp_api_url = "http://apimanage.websoftexpay.com/api/creditreport_generateOTP.aspx"
        self.credit_report_api_url = (
            "http://apimanage.websoftexpay.com/api/credit_report_euifax.aspx"
        )

    async def generate_otp(self, phone_number: str, orderid: str = "1") -> Dict[str, Any]:
        """
        Generate OTP for credit report verification

        Args:
            phone_number: User's phone number
            orderid: Order ID (default: "1")

        Returns:
            API response dictionary
        """

        try:
            payload = {
                "apiid": self.apiid,
                "token": self.token,
                "methodName": "CreditReportEquifaxOTPGenerate",
                "orderid": orderid,
                "phone_number": phone_number,
            }

            logger.info(f"Generating OTP for phone number: {phone_number}")

            async with httpx.AsyncClient() as client:
                response = await client.post(self.otp_api_url, json=payload)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during OTP generation: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error generating OTP: {str(e)}")
            raise

    async def get_credit_report(
        self,
        fname: str,
        lname: str,
        dob: str,
        phone_number: str,
        pan_num: str,
        otp: str,
        orderid: str = "1",
        check_db_first: bool = True,
        user_id: Optional[str] = None,
        generate_pdf: bool = True,  # Added parameter to control PDF generation
    ) -> Dict[str, Any]:
        """
        Get credit report from Equifax or from database if recent report exists

        Args:
            fname: First name
            lname: Last name
            dob: Date of birth in DD-MM-YYYY format
            phone_number: Phone number
            pan_num: PAN number
            otp: OTP received
            orderid: Order ID (default: "1")
            check_db_first: Whether to check database before calling API (default: True)
            user_id: Optional user ID to associate with the report
            generate_pdf: Whether to generate and store PDF (default: True)

        Returns:
            Credit report data
        """
        try:
            # 1. Check if a recent report exists in the database (if check_db_first is True)
            if check_db_first:
                logger.info(f"Checking database for recent report: PAN: {pan_num}")
                recent_report = await credit_report_repository.get_recent_report(
                    pan_num, phone_number
                )

                if recent_report:
                    logger.info(f"Found recent report in database for PAN: {pan_num}")
                    return {
                        "status": "success",
                        "code": "TXN",
                        "mess": "success",
                        "data": recent_report["raw_data"],
                        "from_database": True,
                    }

            # 2. If no recent report or check_db_first is False, call the API
            logger.info(
                f"Fetching credit report from API for user: {fname} {lname}, PAN: {pan_num}"
            )

            payload = {
                "apiid": self.apiid,
                "token": self.token,
                "methodName": "creditreportEquifax",
                "orderid": orderid,
                "fname": fname,
                "lname": lname,
                "dob": dob,
                "phone_number": phone_number,
                "pan_num": pan_num,
                "otp": otp,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.credit_report_api_url, json=payload)
                response.raise_for_status()
                api_response = response.json()

                # If API call was successful, store the response in the database
                if api_response.get("status") == "success":
                    # Insert or update in the database
                    saved_report = await self._save_report_to_db(
                        api_response, fname, lname, dob, phone_number, pan_num, user_id
                    )

                    # Generate and store the PDF if requested
                    if generate_pdf:
                        pdf_document = await self._generate_and_store_pdf(
                            api_response, phone_number, pan_num, user_id
                        )

                        if pdf_document:
                            # Add PDF info to the response
                            api_response["pdf_document"] = {
                                "id": pdf_document.get("id"),
                                "document_path": pdf_document.get("document_path"),
                            }

                return api_response

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during credit report fetch: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error fetching credit report: {str(e)}")
            raise

    async def _generate_and_store_pdf(
        self,
        api_response: Dict[str, Any],
        phone_number: str,
        pan_num: str,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a PDF from the credit report data and store it

        Args:
            api_response: The credit report API response
            phone_number: User's phone number
            pan_num: User's PAN number
            user_id: Optional user ID

        Returns:
            Dictionary with PDF document information
        """
        try:
            # Extract data needed for PDF generation
            data = api_response.get("data", {})

            # Parse data for PDF generation
            from app.services.credit_report_service import (
                parsePersonalInfo,
                parseCreditScore,
                parseCreditSummary,
                parseAccountDetails,
                parseEnquiries,
            )

            # Extract and parse data
            personal_info = parsePersonalInfo(data)
            credit_score = parseCreditScore(data)
            credit_summary = parseCreditSummary(data)
            account_details = parseAccountDetails(data)
            enquiries = parseEnquiries(data)

            # Generate PDF
            pdf_doc = generateCibilReportPDF(
                personal_info, credit_score, credit_summary, account_details, enquiries
            )

            # Convert PDF to bytes
            pdf_buffer = BytesIO()
            pdf_doc.output(pdf_buffer)
            pdf_bytes = pdf_buffer.getvalue()

            # Store PDF
            pdf_document = await cibil_pdf_service.store_cibil_pdf(
                pdf_data=pdf_bytes, phone_number=phone_number, pan_number=pan_num, user_id=user_id
            )

            return pdf_document

        except Exception as e:
            logger.error(f"Error generating and storing PDF: {str(e)}")
            return None

    async def _save_report_to_db(
        self,
        api_response: Dict[str, Any],
        fname: str,
        lname: str,
        dob: str,
        phone_number: str,
        pan_num: str,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Extract relevant data from API response and save to database
        """
        try:
            # Extract data from the API response
            data = api_response.get("data", {})
            equifax_report = data.get("Equifax_Report", {})

            # Get the credit score
            credit_score = None
            credit_score_version = None

            ccr_response = equifax_report.get("CCRResponse", {})
            cir_report_data_list = ccr_response.get("CIRReportDataLst", [])

            if cir_report_data_list:
                cir_report_data = cir_report_data_list[0].get("CIRReportData", {})
                score_details = cir_report_data.get("ScoreDetails", [])

                if score_details:
                    credit_score = score_details[0].get("Value")
                    credit_score_version = score_details[0].get("Version")

            # Get account summaries
            retail_accounts_summary = None
            total_accounts = 0
            active_accounts = 0
            closed_accounts = 0
            delinquent_accounts = 0

            if cir_report_data_list:
                cir_report_data = cir_report_data_list[0].get("CIRReportData", {})
                retail_accounts_summary = cir_report_data.get("RetailAccountsSummary", {})

                if retail_accounts_summary:
                    total_accounts = int(retail_accounts_summary.get("NoOfAccounts", 0))
                    active_accounts = int(retail_accounts_summary.get("NoOfActiveAccounts", 0))
                    closed_accounts = total_accounts - active_accounts
                    delinquent_accounts = int(retail_accounts_summary.get("NoOfPastDueAccounts", 0))

            # Get report order number
            report_id = None
            inquiry_response_header = equifax_report.get("InquiryResponseHeader", {})
            if inquiry_response_header:
                report_id = inquiry_response_header.get("ReportOrderNO")

            # Prepare data for database
            report_data = {
                "pan_number": pan_num,
                "phone_number": phone_number,
                "first_name": fname,
                "last_name": lname,
                "dob": dob,
                "report_id": report_id,
                "credit_score": int(credit_score) if credit_score else None,
                "credit_score_version": credit_score_version,
                "raw_data": data,
                "total_accounts": total_accounts,
                "active_accounts": active_accounts,
                "closed_accounts": closed_accounts,
                "delinquent_accounts": delinquent_accounts,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_valid": True,
                "user_id": user_id,  # Associate with user if provided
                "lead_source": "Website",  # Default lead source
            }

            # Check if a report already exists for this PAN and phone number
            existing_report = await credit_report_repository.get_by_pan_and_phone(
                pan_num, phone_number
            )

            if existing_report:
                # Update existing report
                await credit_report_repository.update(pan_num, phone_number, report_data)
                logger.info(f"Updated credit report in database for PAN: {pan_num}")
            else:
                # Create new report
                await credit_report_repository.create(report_data)
                logger.info(f"Created new credit report in database for PAN: {pan_num}")

        except Exception as e:
            logger.error(f"Error saving report to database: {str(e)}")
            # Continue execution even if saving to DB fails
            pass

    async def search_reports(
        self, search_term: str, limit: int = 100, skip: int = 0, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for credit reports
        """
        try:
            reports = await credit_report_repository.search_reports(
                search_term, limit, skip, user_id
            )
            total_count = await credit_report_repository.count_reports(user_id)

            return {
                "status": "success",
                "code": "TXN",
                "mess": "success",
                "data": {"reports": reports, "total": total_count, "limit": limit, "skip": skip},
            }
        except Exception as e:
            logger.error(f"Error searching reports: {str(e)}")
            return {
                "status": "error",
                "code": "ERR",
                "mess": f"Error searching reports: {str(e)}",
                "data": None,
            }

    async def get_all_reports(
        self, limit: int = 100, skip: int = 0, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all credit reports with pagination
        """
        try:
            reports = await credit_report_repository.get_all_reports(limit, skip, user_id)
            total_count = await credit_report_repository.count_reports(user_id)

            return {
                "status": "success",
                "code": "TXN",
                "mess": "success",
                "data": {"reports": reports, "total": total_count, "limit": limit, "skip": skip},
            }
        except Exception as e:
            logger.error(f"Error getting all reports: {str(e)}")
            return {
                "status": "error",
                "code": "ERR",
                "mess": f"Error getting all reports: {str(e)}",
                "data": None,
            }

    async def delete_report(self, report_id: int) -> Dict[str, Any]:
        """
        Delete a credit report by ID
        """
        try:
            # Check if report exists
            report = await credit_report_repository.get_by_id(report_id)
            if not report:
                return {
                    "status": "error",
                    "code": "ERR",
                    "mess": f"Report with ID {report_id} not found",
                    "data": None,
                }

            # Soft delete the report
            success = await credit_report_repository.delete(report_id)

            if success:
                return {
                    "status": "success",
                    "code": "TXN",
                    "mess": f"Report with ID {report_id} successfully deleted",
                    "data": None,
                }
            else:
                return {
                    "status": "error",
                    "code": "ERR",
                    "mess": f"Failed to delete report with ID {report_id}",
                    "data": None,
                }
        except Exception as e:
            logger.error(f"Error deleting report: {str(e)}")
            return {
                "status": "error",
                "code": "ERR",
                "mess": f"Error deleting report: {str(e)}",
                "data": None,
            }

    async def get_cibil_pdf_by_phone(self, phone_number: str) -> Dict[str, Any]:
        """
        Get CIBIL PDF documents for a user by phone number

        Args:
            phone_number: The phone number to search for

        Returns:
            Dict with document information
        """
        try:
            # Import repositories directly
            from app.repository.documents_repository import document_repository
            from app.repository.user_repository import user_repository

            # Find user by phone
            user = await user_repository.get_by_phone(phone_number)
            if not user:
                return {
                    "status": "error",
                    "code": "ERR",
                    "mess": "User not found with this phone number",
                    "data": None,
                }

            # Find documents for this user that are PDFs and have "CIBIL" in the name
            documents = await document_repository.get_user_documents(user.id)
            if not documents:
                return {
                    "status": "success",
                    "code": "TXN",
                    "mess": "No CIBIL documents found",
                    "data": {"documents": [], "total": 0},
                }

            cibil_pdfs = []
            for doc in documents:
                if doc is not None:
                    # Check if doc is an object with a dict() method
                    if hasattr(doc, "dict") and callable(doc.dict):
                        doc_data = doc.dict()
                        print(doc_data)
                        doc_type = doc_data.get("document_type", "")
                        doc_name = doc_data.get("document_name", "")
                    # If it's already a dictionary
                    elif isinstance(doc, dict):
                        print(doc)
                        doc_type = doc.get("document_type", "")
                        doc_name = doc.get("document_name", "")
                    else:
                        # Skip this document if it's neither an object with dict() nor a dictionary
                        continue

                    if (
                        doc_type == "application/pdf"
                        and isinstance(doc_name, str)
                        and "cibil" in doc_name.lower()
                    ):
                        cibil_pdfs.append(doc if isinstance(doc, dict) else doc_data)

            return {
                "status": "success",
                "code": "TXN",
                "mess": "success",
                "data": {"documents": cibil_pdfs, "total": len(cibil_pdfs)},
            }

        except Exception as e:
            logger.error(f"Error getting CIBIL PDFs by phone: {str(e)}")
            return {
                "status": "error",
                "code": "ERR",
                "mess": f"Error getting CIBIL PDFs: {str(e)}",
                "data": None,
            }

    async def _save_report_to_db(
        self,
        api_response: Dict[str, Any],
        fname: str,
        lname: str,
        dob: str,
        phone_number: str,
        pan_num: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract relevant data from API response and save to database.
        Also ensures a user exists in the users table.
        """
        try:
            # Extract data from the API response
            data = api_response.get("data", {})
            equifax_report = data.get("Equifax_Report", {})

            # Get the credit score
            credit_score = None
            credit_score_version = None

            ccr_response = equifax_report.get("CCRResponse", {})
            cir_report_data_list = ccr_response.get("CIRReportDataLst", [])

            if cir_report_data_list:
                cir_report_data = cir_report_data_list[0].get("CIRReportData", {})
                score_details = cir_report_data.get("ScoreDetails", [])

                if score_details:
                    credit_score = score_details[0].get("Value")
                    credit_score_version = score_details[0].get("Version")

            # Get account summaries
            retail_accounts_summary = None
            total_accounts = 0
            active_accounts = 0
            closed_accounts = 0
            delinquent_accounts = 0

            if cir_report_data_list:
                cir_report_data = cir_report_data_list[0].get("CIRReportData", {})
                retail_accounts_summary = cir_report_data.get("RetailAccountsSummary", {})

                if retail_accounts_summary:
                    total_accounts = int(retail_accounts_summary.get("NoOfAccounts", 0))
                    active_accounts = int(retail_accounts_summary.get("NoOfActiveAccounts", 0))
                    closed_accounts = total_accounts - active_accounts
                    delinquent_accounts = int(retail_accounts_summary.get("NoOfPastDueAccounts", 0))

            # Get report order number
            report_id = None
            inquiry_response_header = equifax_report.get("InquiryResponseHeader", {})
            if inquiry_response_header:
                report_id = inquiry_response_header.get("ReportOrderNO")

            # Prepare data for database
            report_data = {
                "pan_number": pan_num,
                "phone_number": phone_number,
                "first_name": fname,
                "last_name": lname,
                "dob": dob,
                "report_id": report_id,
                "credit_score": int(credit_score) if credit_score else None,
                "credit_score_version": credit_score_version,
                "raw_data": data,
                "total_accounts": total_accounts,
                "active_accounts": active_accounts,
                "closed_accounts": closed_accounts,
                "delinquent_accounts": delinquent_accounts,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_valid": True,
                "user_id": user_id,  # Associate with user if provided
                "lead_source": "Website",  # Default lead source
            }

            # Check if a report already exists for this PAN and phone number
            existing_report = await credit_report_repository.get_by_pan_and_phone(
                pan_num, phone_number
            )

            if existing_report:
                # Update existing report
                await credit_report_repository.update(pan_num, phone_number, report_data)
                logger.info(f"Updated credit report in database for PAN: {pan_num}")
            else:
                # Create new report
                created_report = await credit_report_repository.create(report_data)
                logger.info(f"Created new credit report in database for PAN: {pan_num}")

            # SYNC WITH USERS TABLE - This is the critical addition
            # Import necessary repository
            from app.repository.user_repository import user_repository
            import uuid

            # Check if a user already exists with this phone number
            existing_user = await user_repository.get_by_phone(phone_number)

            if not existing_user:
                # Create a new user in the users table
                from app.schemas.user import UserCreateManual

                # Prepare user data
                user_data = UserCreateManual(
                    full_name=f"{fname} {lname}",
                    phone_number=phone_number,
                    country_code="91",  # Default country code
                    email=None,  # CIBIL reports might not have email
                    pan_number=pan_num,
                    cibil_score=int(credit_score) if credit_score else None,
                    source="strapi_cibil",
                    status="Lead",
                    is_active=True,
                    role="User",
                    loan_amount=None,
                    employment_type=None,
                    monthly_income=None,
                    loan_purpose=None,
                    loan_tenure=None,
                    location=None,
                )

                # Create the user
                new_user = await user_repository.create_manual(user_data)

                # Update report with user_id if it was created
                if new_user and not user_id:
                    await credit_report_repository.update_user_id(
                        pan_num, phone_number, new_user.id
                    )
                    logger.info(
                        f"Created new user and linked with credit report for phone: {phone_number}"
                    )

            elif not user_id:
                # If user exists but report doesn't have user_id, update it
                await credit_report_repository.update_user_id(
                    pan_num, phone_number, existing_user.id
                )

                # Also update the user's CIBIL score if needed
                if credit_score and (
                    not existing_user.cibil_score or existing_user.cibil_score != int(credit_score)
                ):
                    from app.schemas.user import UserUpdateRequest

                    update_data = UserUpdateRequest(
                        id=existing_user.id,
                        cibil_score=int(credit_score) if credit_score else None,
                    )

                    await user_repository.update_user(update_data)
                    logger.info(f"Updated user CIBIL score for phone: {phone_number}")

            # Return the report data for further processing
            return report_data

        except Exception as e:
            logger.error(f"Error saving report to database: {str(e)}")
            # Continue execution even if saving to DB fails
            return {}


# Create a singleton instance
credit_report_service = CreditReportService()
