import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any, Union
import json
from venv import logger
from sqlalchemy import bindparam, insert, or_, and_, text, update
from app.db.session import database
from app.models.user import users
from app.models.consolidate_users import consolidate_users
from app.repository.user_repository import user_repository
from app.repository.documents_repository import document_repository
from app.service.external_service import external_repository
from app.schemas.user import UnifiedLeadBase, CombinedDataResponse
from sqlalchemy import select, join, func, and_
import time
from app.models.message import messages
from typing import Dict, List, Optional, Tuple, Any, Union
import asyncio


class LeadService:
    def __init__(self):
        self.user_repository = user_repository
        self.external_repository = external_repository
        self.document_repository = document_repository

    async def get_combined_leads(
        self,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        date_range: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        loan_amount: Optional[str] = None,
        employment_type: Optional[str] = None,
        cibil_score: Optional[str] = None,
        sources: Optional[List[str]] = None,
    ) -> CombinedDataResponse:
        """
        Get combined lead data from internal and external sources with filtering and pagination.
        """
        # Calculate date range based on selection
        start_date, end_date = self._calculate_date_range(date_range, date_from, date_to)

        # Get loan amount range boundaries
        min_amount, max_amount = self._parse_loan_amount_range(loan_amount)

        # Get all data from different sources
        all_data = await self._fetch_and_filter_all_sources(
            search=search,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amount,
            max_amount=max_amount,
            employment_type=employment_type,
            min_score=None,
            max_score=None,
            sources=None,
            cibil_score=cibil_score,
            loan_amount=loan_amount,
        )

        # Filter external the data based on the provided filters
        filtered_data = self._filter_leads(
            all_data,
            search=search,
            start_date=None,
            end_date=None,
            min_amount=min_amount,
            max_amount=max_amount,
            employment_type=employment_type,
            cibil_score=cibil_score,
            sources=sources,
            loan_amount=loan_amount,
        )
        # Calculate total records count
        total_records = len(filtered_data)
        # await self.store_users(filtered_data)

        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_records)
        paginated_data = filtered_data[start_idx:end_idx] if start_idx < total_records else []
        return CombinedDataResponse(
            total_records=total_records,
            leads=paginated_data,
            page_size=page_size,
            current_page=page,
            total_pages=(total_records // page_size) + (1 if total_records % page_size else 0),
        )

    async def store_users(self, filtered_data: List[UnifiedLeadBase]):
        """
        Store data from filtered_data into the users table, avoiding duplicates.
        """
        for lead in filtered_data:
            # Check if a user with the same phone_number already exists
            existing_user = await database.fetch_one(
                select(consolidate_users).where(
                    or_(
                        consolidate_users.c.id == lead.user_id,
                        consolidate_users.c.phone_number == lead.phone_number,
                    )
                )
            )

            if not existing_user:
                # Prepare the data for insertion
                user_data = {
                    "id": lead.user_id,
                    "full_name": lead.full_name,
                    "phone_number": lead.phone_number,
                    "country_code": lead.country_code,
                    "email": lead.email,
                    "pan_number": lead.pan_number,
                    "loan_amount": lead.loan_amount,
                    "employment_type": lead.employment_type,
                    "company_name": lead.company_name,
                    "monthly_income": lead.monthly_income,
                    "loan_purpose": lead.loan_purpose,
                    "loan_tenure": lead.loan_tenure,
                    "raw_data": lead.raw_data,
                    "cibil_score": lead.cibil_score,
                    "source": lead.lead_source,
                    "created_on": lead.created_at,
                    "updated_on": lead.created_at,
                }

                # Insert the new user into the consolidate_users table
                insert_query = insert(consolidate_users).values(**user_data)
                await database.execute(insert_query)

    async def fetch(self) -> list:
        """
        Fetch all records from the consolidate_users table.

        Returns:
            list: A list of rows, where each row is a mapping of column names to values.
        """
        query = select(users)
        results = await database.fetch_all(query)
        return results

    def convert_datetime_to_string(self, data):
        """
        Recursively convert datetime objects in a dictionary or list to ISO format strings.
        """
        if isinstance(data, dict):
            return {k: self.convert_datetime_to_string(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.convert_datetime_to_string(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data

    def _filter_leads(
        self,
        leads: List[UnifiedLeadBase],
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        employment_type: Optional[str] = None,
        cibil_score: Optional[str] = None,
        sources: Optional[List[str]] = None,
        loan_amount: Optional[str] = None,
    ) -> List[UnifiedLeadBase]:
        """
        Filter leads based on the provided criteria.
        """
        filtered = leads

        # Apply search filter
        if search:
            search_term = search.lower()
            special_sources = {"beehiiv", "strapi_loan", "strapi_cibil"}
            employment_keywords = {"salaried", "business"}

            filtered = [
                lead
                for lead in filtered
                if (
                    (lead.full_name and search_term in lead.full_name.lower())
                    or (lead.email and search_term in lead.email.lower())
                    or (lead.phone_number and search_term in lead.phone_number.lower())
                    or (lead.loan_type and search_term in lead.loan_type.lower())
                    or (lead.lead_source and search_term in lead.lead_source.lower())
                    or (
                        "website" in search_term and lead.lead_source in special_sources
                    )  # Include all special sources when searching for "website"
                    or (
                        any(
                            keyword in search_term for keyword in employment_keywords
                        )  # Search contains "salaried" or "business"
                        and lead.employment_type
                        and any(
                            keyword in lead.employment_type.lower()
                            for keyword in employment_keywords
                        )  # Lead contains either "salaried" or "business"
                    )
                    or (
                        hasattr(lead, "raw_data")  # Ensure `raw_data` exists
                        and lead.raw_data is not None
                        and (
                            (
                                lead.raw_data.get("loan_type")
                                and search_term in lead.raw_data["loan_type"].lower()
                            )
                            or (
                                lead.raw_data.get("email")
                                and search_term in lead.raw_data["email"].lower()
                            )
                            or (
                                lead.raw_data.get("phone_number")
                                and search_term in lead.raw_data["phone_number"].lower()
                            )
                        )
                    )
                )
            ]

        # Apply date range filter based on Last communicated date
        if start_date:
            filtered = [
                lead
                for lead in filtered
                if (lead.last_communicated is not None and lead.last_communicated >= start_date)
            ]

        if end_date:
            filtered = [
                lead
                for lead in filtered
                if (lead.last_communicated is not None and lead.last_communicated <= end_date)
            ]

        # Apply loan amount filter
        if loan_amount:
            loan_ranges = self._parse_loan_amount_ranges(loan_amount)

            if loan_ranges:
                filtered = [
                    lead
                    for lead in filtered
                    if any(
                        lead.loan_amount is not None
                        and (min_amount is None or lead.loan_amount >= min_amount)
                        and (max_amount is None or lead.loan_amount <= max_amount)
                        for min_amount, max_amount in loan_ranges
                    )
                ]

        # Apply employment type filter
        if employment_type:
            employment_values = {emp.strip().lower() for emp in employment_type.split(",")}
            filtered = [
                lead
                for lead in filtered
                if (lead.employment_type and lead.employment_type.lower() in employment_values)
            ]

        # Apply CIBIL score filter
        if cibil_score:
            cibil_ranges = self._parse_cibil_score_range(cibil_score)
            if cibil_ranges:
                filtered = [
                    lead
                    for lead in filtered
                    if (
                        lead.cibil_score is not None
                        and any(
                            min_range <= lead.cibil_score <= max_range
                            for min_range, max_range in cibil_ranges
                        )
                    )
                ]

        # Apply sources filter
        if sources:
            sources_lower = {s.lower() for s in sources}

            # If "website" is one of the sources, include special sources
            if "website" in sources_lower:
                sources_lower |= {"beehiiv", "strapi_loan", "strapi_cibil"}

            filtered = [
                lead
                for lead in filtered
                if (
                    lead.lead_source and lead.lead_source.lower() in sources_lower
                )  # No null sources allowed
            ]
        # Ensure `datetime.min` is timezone-aware
        min_datetime = datetime.min.replace(tzinfo=timezone.utc)

        # # Sort filtered leads by `created_at`, placing `None` values at the end
        # filtered.sort(key=lambda lead: lead.created_at if lead.created_at is not None else min_datetime, reverse=True)

        return filtered

    def _calculate_date_range(
        self, date_range: Optional[str], date_from: Optional[datetime], date_to: Optional[datetime]
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Calculate start and end dates based on date range selection"""
        from datetime import timezone  # Import timezone

        # Use timezone-aware datetime
        now = datetime.now(timezone.utc)

        if date_range == "all_time":
            return None, None
        elif date_range == "last_7_days":
            return now - timedelta(days=7), now
        elif date_range == "last_30_days":
            return now - timedelta(days=30), now
        elif date_range == "last_90_days":
            return now - timedelta(days=90), now
        elif date_range == "last_180_days":
            return now - timedelta(days=180), now
        elif date_range == "last_365_days":
            return now - timedelta(days=365), now
        elif date_from and date_to:  # Custom date range
            # Ensure both dates are timezone-aware
            if date_from.tzinfo is None:
                date_from = date_from.replace(tzinfo=timezone.utc)
            if date_to.tzinfo is None:
                date_to = date_to.replace(tzinfo=timezone.utc)
            return date_from, date_to

        return None, None  # Default to all time

    def _parse_loan_amount_range(
        self, loan_amount: Optional[str]
    ) -> Tuple[Optional[float], Optional[float]]:
        """Parse loan amount range from string representation"""
        if not loan_amount:
            return None, None

        ranges = {
            "up_to_25_lakhs": (1, 2500000),
            "25_lakhs_to_2_crores": (2500000, 20000000),
            "2_crores_to_10_crores": (20000000, 100000000),
            "above_10_crores": (100000000, None),
        }

        return ranges.get(loan_amount, (None, None))

    def _parse_loan_amount_ranges(
        self, loan_amount: Optional[Union[str, List[str]]]
    ) -> List[Tuple[Optional[float], Optional[float]]]:
        """Parse loan amount range from string or list of strings"""
        if not loan_amount:
            return []

        ranges = {
            "up_to_25_lakhs": (1, 2500000),
            "25_lakhs_to_2_crores": (2500000, 20000000),
            "2_crores_to_10_crores": (20000000, 100000000),
            "above_10_crores": (100000000, None),
        }

        # Ensure loan_amount is a list
        if isinstance(loan_amount, str):
            loan_amount = [item.strip() for item in loan_amount.split(",")]

        # Extract valid loan ranges
        return [ranges[range_str] for range_str in loan_amount if range_str in ranges]

    def _parse_cibil_score_range(
        self, cibil_score: Optional[str]
    ) -> List[Tuple[Optional[int], Optional[int]]]:
        """Parse CIBIL score range from string representation - supports multiple ranges"""
        if not cibil_score:
            return []

        ranges = {"300_500": (300, 500), "501_700": (501, 700), "701_850": (701, 850)}

        range_list = [r.strip() for r in cibil_score.split(",")]
        result = []

        for range_str in range_list:
            min_max = ranges.get(range_str)
            if min_max:
                result.append(min_max)

        return result if result else []

    async def _fetch_and_filter_all_sources(
        self,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        employment_type: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        sources: Optional[List[str]] = None,
        cibil_score: Optional[str] = None,
        loan_amount: Optional[str] = None,
    ) -> List[UnifiedLeadBase]:
        """Fetch data from all sources and apply filters"""

        # Get all data from external sources
        external_data = await self.external_repository.get_all_external_data()

        # Process and filter external data
        loan_applications = self._filter_loan_applications(
            external_data["loan_applications"],
            search=search,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amount,
            max_amount=max_amount,
            sources=sources,
            cibil_score=cibil_score,
            loan_amount=loan_amount,
        )

        cibil_users = self._filter_cibil_users(
            external_data["cibil_users"],
            search=search,
            start_date=start_date,
            end_date=end_date,
            min_score=min_score,
            max_score=max_score,
            sources=sources,
            cibil_score=cibil_score,
        )

        subscribers = self._filter_subscribers(
            external_data["subscribers"],
            search=search,
            start_date=start_date,
            end_date=end_date,
            sources=sources,
        )

        # # NEW: Get direct CIBIL users from repository
        # Filter direct CIBIL users
        filtered_direct_cibil = await self._fetch_and_filter_direct_cibil_users(
            search=search,
            start_date=start_date,
            end_date=end_date,
            min_score=min_score,
            max_score=max_score,
            sources=sources,
            cibil_score=cibil_score,
        )

        # Convert all data to unified lead format and combine
        combined_data = []

        combined_data.extend(self._convert_loan_applications(loan_applications))
        combined_data.extend(self._convert_cibil_users(cibil_users))
        combined_data.extend(self._convert_subscribers(subscribers))
        combined_data.extend(self._convert_direct_cibil_users(filtered_direct_cibil))

        await self._store_consolidated_users_efficiently(combined_data)
        # Get internal users data with base filters
        internal_users = await self._get_filtered_internal_users(
            search=search,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amount,
            max_amount=max_amount,
            employment_type=employment_type,
            min_score=min_score,
            max_score=max_score,
            sources=sources,
            cibil_score=cibil_score,
            loan_amount=loan_amount,
        )
        combined_data = internal_users
        # Consolidate leads to avoid duplicates
        # consolidated_leads = self.consolidate_leads(combined_data)

        return combined_data

    async def _fetch_and_filter_direct_cibil_users(
        self,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        sources: Optional[List[str]] = None,
        cibil_score: Optional[str] = None,
    ):
        """Fetch and filter direct CIBIL users in a single step"""
        direct_cibil_users = await self._fetch_cibil_users_for_combined_data()

        return self._filter_direct_cibil_users(
            direct_cibil_users,
            search=search,
            start_date=start_date,
            end_date=end_date,
            min_score=min_score,
            max_score=max_score,
            sources=sources,
            cibil_score=cibil_score,
        )

    async def _store_consolidated_users_efficiently(self, users_data: List[UnifiedLeadBase]):
        """Store consolidated users with optimized database operations

        Handles both users with phone numbers and those with only email identifiers.
        """
        if not users_data:
            return

        # Filter out leads with missing IDs and separate users with/without phone numbers
        users_with_phone = []
        users_without_phone = []

        for user in users_data:
            if user.id is not None or user.user_id is not None:
                if user.phone_number:
                    users_with_phone.append(user)
                elif user.email:  # Store users with email but no phone number
                    users_without_phone.append(user)

        # Process users with phone numbers
        if users_with_phone:
            await self._process_users_with_phone(users_with_phone)

        # Process users without phone numbers but with email
        if users_without_phone:
            await self._process_users_without_phone(users_without_phone)

    class DateTimeEncoder(json.JSONEncoder):
        """Custom encoder for handling datetime objects in JSON"""

        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    async def _process_users_with_phone(self, users_with_phone: List[UnifiedLeadBase]):
        if not users_with_phone:
            return

        try:
            # Prepare data as before
            values_list = [
                # Same data preparation code as you have...
            ]

            if values_list:
                async with database.transaction():
                    # Create temporary table first
                    await database.execute(
                        """
                        CREATE TEMPORARY TABLE IF NOT EXISTS temp_users (
                            LIKE users INCLUDING ALL
                        ) ON COMMIT DROP
                    """
                    )

                    # Clear any existing data
                    await database.execute("TRUNCATE TABLE temp_users")

                    # Use batch size for insert into temp table
                    BATCH_SIZE = 1000
                    batches = [
                        values_list[i : i + BATCH_SIZE]
                        for i in range(0, len(values_list), BATCH_SIZE)
                    ]

                    # Insert all data into temp table
                    for batch in batches:
                        await database.execute_many(
                            """INSERT INTO temp_users VALUES (
                                :id, :phone_number, :full_name, :country_code, :email,
                                :pan_number, :loan_amount, :employment_type, :company_name,
                                :monthly_income, :loan_purpose, :loan_tenure, :raw_data,
                                :cibil_score, :source, :created_on, :updated_on
                            )""",
                            batch,
                        )

                    # Single upsert from temp table to main table
                    await database.execute(
                        """
                        INSERT INTO users
                        SELECT * FROM temp_users
                        ON CONFLICT (phone_number) DO UPDATE SET
                            full_name = CASE WHEN users.full_name IS NULL THEN EXCLUDED.full_name ELSE users.full_name END,
                            country_code = CASE WHEN users.country_code IS NULL THEN EXCLUDED.country_code ELSE users.country_code END,
                            email = CASE WHEN users.email IS NULL THEN EXCLUDED.email ELSE users.email END,
                            pan_number = CASE WHEN users.pan_number IS NULL THEN EXCLUDED.pan_number ELSE users.pan_number END,
                            loan_amount = CASE WHEN users.loan_amount IS NULL THEN EXCLUDED.loan_amount ELSE users.loan_amount END,
                            employment_type = CASE WHEN users.employment_type IS NULL THEN EXCLUDED.employment_type ELSE users.employment_type END,
                            company_name = CASE WHEN users.company_name IS NULL THEN EXCLUDED.company_name ELSE users.company_name END,
                            monthly_income = CASE WHEN users.monthly_income IS NULL THEN EXCLUDED.monthly_income ELSE users.monthly_income END,
                            loan_purpose = CASE WHEN users.loan_purpose IS NULL THEN EXCLUDED.loan_purpose ELSE users.loan_purpose END,
                            loan_tenure = CASE WHEN users.loan_tenure IS NULL THEN EXCLUDED.loan_tenure ELSE users.loan_tenure END,
                            raw_data = CASE WHEN users.raw_data IS NULL THEN EXCLUDED.raw_data ELSE users.raw_data END,
                            cibil_score = CASE WHEN users.cibil_score IS NULL THEN EXCLUDED.cibil_score ELSE users.cibil_score END,
                            source = CASE WHEN users.source IS NULL THEN EXCLUDED.source ELSE users.source END,
                            created_on = CASE WHEN users.created_on IS NULL THEN EXCLUDED.created_on ELSE users.created_on END,
                            updated_on = EXCLUDED.updated_on
                        """
                    )
        except Exception as e:
            logging.error(f"Optimized batch processing failed: {str(e)}")

    async def _process_users_without_phone(self, users_without_phone: List[UnifiedLeadBase]):
        """Process users that don't have phone numbers but have emails.
        Only inserts new users; skips users with duplicate emails.
        """
        # Extract all emails from the input users
        emails = [user.email for user in users_without_phone if user.email]

        if not emails:
            return  # No users to process

        try:
            # Get existing emails from the database
            existing_query = select(users.c.email).where(users.c.email.in_(emails))
            existing_result = await database.fetch_all(existing_query)
            existing_email_set = {row["email"] for row in existing_result}

            # Prepare data for insertion (only for users with non-duplicate emails)
            values_list = []
            for user in users_without_phone:
                if not user.email or user.email in existing_email_set:
                    continue  # Skip users with no email or duplicate emails

                # Process raw data to handle beehiiv format
                raw_data = user.raw_data
                if isinstance(raw_data, dict) and "createdAt" in raw_data:
                    # Convert createdAt to created_at to match database schema
                    raw_data["created_at"] = raw_data.pop("createdAt")

                # Ensure raw_data is a JSON string
                if isinstance(raw_data, dict):
                    raw_data = json.dumps(raw_data)
                elif raw_data:
                    raw_data = self.convert_datetime_to_string(raw_data)

                # Prepare user data for insertion
                values_list.append(
                    {
                        "id": user.id or user.user_id,
                        "phone_number": None,  # No phone number
                        "full_name": user.full_name or None,
                        "country_code": user.country_code or None,
                        "email": user.email,
                        "pan_number": user.pan_number or None,
                        "loan_amount": user.loan_amount or None,
                        "employment_type": user.employment_type or None,
                        "company_name": user.company_name or None,
                        "monthly_income": user.monthly_income or None,
                        "loan_purpose": user.loan_purpose or None,
                        "loan_tenure": user.loan_tenure or None,
                        "raw_data": raw_data,
                        "cibil_score": user.cibil_score or None,
                        "source": user.lead_source
                        or "beehiiv",  # Default to beehiiv if from that source
                        "created_on": user.created_at,
                        "updated_on": user.created_at,
                    }
                )

            # Execute batch insert for new users
            if values_list:
                BATCH_SIZE = 1000  # Adjust batch size as needed
                for i in range(0, len(values_list), BATCH_SIZE):
                    batch = values_list[i : i + BATCH_SIZE]
                    insert_query = """
                    INSERT INTO users (
                        id, phone_number, full_name, country_code, email, 
                        pan_number, loan_amount, employment_type, company_name, 
                        monthly_income, loan_purpose, loan_tenure, raw_data, 
                        cibil_score, source, created_on, updated_on
                    ) 
                    VALUES (
                        :id, :phone_number, :full_name, :country_code, :email, 
                        :pan_number, :loan_amount, :employment_type, :company_name, 
                        :monthly_income, :loan_purpose, :loan_tenure, :raw_data, 
                        :cibil_score, :source, :created_on, :updated_on
                    );
                    """
                    await database.execute_many(insert_query, batch)

        except Exception as e:
            # Log the exception
            logging.error(f"Error processing users without phone numbers: {str(e)}")
            raise  # Re-raise the exception if needed

    def _convert_direct_cibil_users(self, direct_cibil_users: List[Dict]) -> List[UnifiedLeadBase]:
        """Convert direct CIBIL users to unified lead format"""
        return [
            UnifiedLeadBase(
                id=user.get("id"),
                user_id=user.get("user_id"),
                full_name=user.get("full_name"),
                phone_number=user.get("phone_number"),
                pan_number=user.get("pan_number"),
                cibil_score=user.get("cibil_score"),
                lead_source="strapi_cibil",
                created_at=self._parse_date(user.get("created_at")),
                last_communicated=self._parse_date(
                    user.get("last_communicated") or user.get("created_at")
                ),
                raw_data=user,
                documents_count=user.get("documents_count", 1),
            )
            for user in direct_cibil_users
        ]

    def consolidate_leads(self, leads: List[UnifiedLeadBase]) -> List[UnifiedLeadBase]:
        """
        Consolidate leads with specific handling for strapi_cibil users:
        - If a matching user (by phone+PAN) exists with strapi_loan source, update their CIBIL score
        - Don't create new entries for strapi_cibil users that match existing strapi_loan users
        - Return the consolidated leads sorted by created_at field
        """
        # Create a new list for final results
        result_leads = []

        # Keep track of processed leads by phone+PAN
        processed_keys = set()

        # First pass: add all strapi_loan leads to the result and track their keys
        for lead in leads:
            if lead.lead_source == "strapi_loan" and lead.phone_number:
                # Use phone_number as the key (since PAN might be missing)
                key = lead.phone_number
                result_leads.append(lead)
                processed_keys.add(key)

        # Second pass: update CIBIL scores for existing loan leads and add non-matching leads
        for lead in leads:
            if lead.phone_number:
                # Use phone_number as the key (since PAN might be missing)
                key = lead.phone_number

                # If this is a strapi_cibil lead and we've already added a strapi_loan lead with same key
                if lead.lead_source == "strapi_cibil" and key in processed_keys:
                    # Update CIBIL score for ALL matching strapi_loan leads
                    for existing_lead in result_leads:
                        if (
                            existing_lead.phone_number == lead.phone_number
                            and existing_lead.lead_source == "strapi_loan"
                        ):
                            existing_lead.cibil_score = lead.cibil_score

                # If this is a lead we haven't processed yet (not a matching strapi_cibil)
                elif key not in processed_keys:
                    result_leads.append(lead)
                    processed_keys.add(key)
            else:
                # If lead doesn't have a phone number, add it as a new lead
                if lead not in result_leads:  # Avoid duplicates
                    result_leads.append(lead)

        # Sort the consolidated leads by created_at field
        result_leads.sort(
            key=lambda x: (
                x.created_at if x.created_at else datetime.min.replace(tzinfo=timezone.utc)
            ),
            reverse=True,
        )

        return result_leads

    async def _get_filtered_internal_users(
        self,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        employment_type: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        sources: Optional[List[str]] = None,
        cibil_score: Optional[str] = None,
        loan_amount: Optional[str] = None,
    ):
        """Get and filter internal users"""
        query = users.select().where(users.c.is_active == True)

        # Apply text search filter
        # Apply text search filter
        if search:
            search_term = f"%{search}%"

            # First create the base query with standard search conditions
            query = query.where(
                or_(
                    users.c.full_name.ilike(search_term),
                    users.c.email.ilike(search_term),
                    users.c.phone_number.ilike(search_term),
                    users.c.loan_purpose.ilike(search_term),
                    users.c.employment_type.ilike(search_term),
                    users.c.source.ilike(search_term),
                    text("raw_data->>'loan_type' ILIKE :search_term"),
                    text("raw_data->>'email' ILIKE :search_term"),
                    text("raw_data->>'phone_number' ILIKE :search_term"),
                )
            ).params(search_term=search_term)

            # If 'website' is in the search term, add another condition separately
            if "website" in search.lower():
                query = query.where(users.c.source.in_(["strapi_loan", "strapi_cibil", "beehiiv"]))

        if start_date:
            query = query.where(users.c.created_on >= start_date)
        if end_date:
            query = query.where(users.c.created_on <= end_date)

        # if start_date or end_date:
        #     query = self.filter_users_by_most_recent_communication(start_date=start_date, end_date=end_date)

        # Apply loan amount filter
        if loan_amount:
            loan_ranges = self._parse_loan_amount_ranges(loan_amount)

            if loan_ranges:
                loan_conditions = []
                for min_amt, max_amt in loan_ranges:
                    if min_amt is not None and max_amt is not None:
                        loan_conditions.append(
                            and_(users.c.loan_amount >= min_amt, users.c.loan_amount <= max_amt)
                        )
                    elif min_amt is not None:
                        loan_conditions.append(users.c.loan_amount >= min_amt)

                query = query.where(or_(*loan_conditions))

        # Apply employment type filter
        if employment_type:
            employment_values = [emp.strip() for emp in employment_type.split(",")]
            if len(employment_values) > 1:
                query = query.where(users.c.employment_type.in_(employment_values))
            else:
                query = query.where(users.c.employment_type == employment_values[0])

        cibil_ranges = self._parse_cibil_score_range(cibil_score)
        if cibil_ranges and len(cibil_ranges) > 0:

            cibil_conditions = []
            for min_range, max_range in cibil_ranges:
                # Include null/missing scores in the 300-500 range
                # if min_range == 300 and max_range == 500:
                #     cibil_conditions.append(
                #         or_(
                #             and_(
                #                 users.c.cibil_score >= min_range, users.c.cibil_score <= max_range
                #             ),
                #             users.c.cibil_score.is_(None),
                #         )
                #     )
                # else:
                cibil_conditions.append(
                    and_(users.c.cibil_score >= min_range, users.c.cibil_score <= max_range)
                )
            if cibil_conditions:
                query = query.where(or_(*cibil_conditions))
        else:
            if min_score is not None:
                query = query.where(users.c.cibil_score >= min_score)
            if max_score is not None:
                query = query.where(users.c.cibil_score <= max_score)

        # Apply sources filter - Modified to support multiple sources
        if sources and len(sources) > 0:
            source_conditions = []
            for source in sources:
                source_conditions.append(users.c.source == source)
            query = query.where(or_(*source_conditions))
        # Apply ORDER BY updated_date in descending order (most recent first)
        query = query.order_by(users.c.updated_on.desc())

        # Execute query
        result = await database.fetch_all(query)

        # Fetch document counts for each user
        user_leads = []
        for user in result:
            # doc_count = await self.document_repository.get_user_documents_count(user.id)
            if user is not None:
                lead = self._convert_internal_user_to_lead(user)
                # lead.documents_count = doc_count
                user_leads.append(lead)

        return user_leads

    def filter_users_by_most_recent_communication(self, start_date=None, end_date=None):
        # Build a subquery to get the most recent timestamp for each phone number within the date range
        msg_query = select(
            [messages.c.phone_number, func.max(messages.c.timestamp).label("last_communicated")]
        ).group_by(messages.c.phone_number)

        if start_date:
            start_timestamp = str(int(time.mktime(start_date.timetuple())))
            msg_query = msg_query.where(messages.c.timestamp >= start_timestamp)

        if end_date:
            end_timestamp = str(int(time.mktime(end_date.timetuple())))
            msg_query = msg_query.where(messages.c.timestamp <= end_timestamp)

        msg_query = msg_query.alias("msg_query")

        # Select users matching these phone numbers and join with the latest communication data
        query = select([users, msg_query.c.last_communicated]).join(
            msg_query, users.c.phone_number == msg_query.c.phone_number
        )

        return query

    def _filter_loan_applications(
        self,
        loan_applications: List[Dict],
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        sources: Optional[List[str]] = None,
        cibil_score: Optional[str] = None,
        loan_amount: Optional[str] = None,
    ) -> List[Dict]:
        """Filter loan applications"""
        from datetime import timezone

        filtered = loan_applications

        if search:
            search_term = search.lower()
            special_sources = {"beehiiv", "strapi_loan", "strapi_cibil"}

            filtered = [
                app
                for app in filtered
                if (
                    (app.get("name") and search_term in app.get("name", "").lower())
                    or (app.get("email") and search_term in app.get("email", "").lower())
                    or (
                        app.get("phone_number")
                        and search_term in app.get("phone_number", "").lower()
                    )
                    or (app.get("loan_type") and search_term in app.get("loan_type", "").lower())
                    or (
                        app.get("source") and search_term in app.get("source", "").lower()
                    )  # Normal source search
                    or (
                        "website" in search_term and app.get("source") in special_sources
                    )  # Fetch from all special sources when searching for "website"
                )
            ]

        # Apply date range filter
        if start_date:
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)

            filtered = [
                app
                for app in filtered
                if (
                    app.get("createdAt")
                    and self._parse_date(app.get("createdAt")) is not None
                    and self._parse_date(app.get("createdAt")) >= start_date
                )
            ]

        if end_date:
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)

            filtered = [
                app
                for app in filtered
                if (
                    app.get("createdAt")
                    and self._parse_date(app.get("createdAt")) is not None
                    and self._parse_date(app.get("createdAt")) <= end_date
                )
            ]

        # Apply loan amount filter
        # if min_amount is not None:
        #     filtered = [
        #         app
        #         for app in filtered
        #         if (app.get("amount") and self._safe_float(app.get("amount", 0)) >= min_amount)
        #     ]

        # if max_amount is not None:
        #     filtered = [
        #         app
        #         for app in filtered
        #         if (app.get("amount") and self._safe_float(app.get("amount", 0)) <= max_amount)
        #     ]
        if loan_amount:
            loan_ranges = self._parse_loan_amount_ranges(loan_amount)

            filtered = [
                app
                for app in filtered
                if app.get("amount")
                and any(
                    (min_amt is None or self._safe_float(app.get("amount")) >= min_amt)
                    and (max_amt is None or self._safe_float(app.get("amount")) <= max_amt)
                    for min_amt, max_amt in loan_ranges
                )
            ]

        cibil_ranges = self._parse_cibil_score_range(cibil_score)
        if cibil_ranges and len(cibil_ranges) > 0:
            range_filtered = []
            for min_range, max_range in cibil_ranges:
                for app in filtered:
                    app_score = self._safe_int(app.get("cibil_score", 0))
                    if app_score and min_range <= app_score <= max_range:
                        range_filtered.append(app)
            filtered = range_filtered

        # Apply sources filter
        if sources and len(sources) > 0:
            if "strapi_loan" not in [s.lower() for s in sources]:
                filtered = []
        return filtered

    def _filter_cibil_users(
        self,
        cibil_users: List[Dict],
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        sources: Optional[List[str]] = None,
        cibil_score: Optional[str] = None,
    ) -> List[Dict]:
        """Filter CIBIL users"""
        from datetime import timezone

        filtered = cibil_users
        cibil_ranges = self._parse_cibil_score_range(cibil_score)

        if cibil_ranges and len(cibil_ranges) > 0:
            range_filtered = []
            for min_range, max_range in cibil_ranges:
                for user in filtered:
                    user_score = self._safe_int(user.get("cibil_score", 0))
                    if user_score and min_range <= user_score <= max_range:
                        range_filtered.append(user)
            filtered = range_filtered
        else:
            if min_score is not None:
                filtered = [
                    user
                    for user in filtered
                    if (
                        user.get("cibil_score")
                        and self._safe_int(user.get("cibil_score", 0)) >= min_score
                    )
                ]

            if max_score is not None:
                filtered = [
                    user
                    for user in filtered
                    if (
                        user.get("cibil_score")
                        and self._safe_int(user.get("cibil_score", 0)) <= max_score
                    )
                ]

        if search:
            search_term = search.lower()
            special_sources = {"beehiiv", "strapi_loan", "strapi_cibil"}

            filtered = [
                user
                for user in filtered
                if (
                    (user.get("name") and search_term in user.get("name", "").lower())
                    or (
                        user.get("phone_number")
                        and search_term in user.get("phone_number", "").lower()
                    )
                    or (
                        user.get("pan_number") and search_term in user.get("pan_number", "").lower()
                    )
                    or (
                        user.get("source") and search_term in user.get("source", "").lower()
                    )  # Normal source search
                    or (
                        "website" in search_term and user.get("source") in special_sources
                    )  # Fetch all special sources on 'website' search
                )
            ]

        if start_date:
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)

            filtered = [
                user
                for user in filtered
                if (
                    user.get("createdAt")
                    and self._parse_date(user.get("createdAt")) is not None
                    and self._parse_date(user.get("createdAt")) >= start_date
                )
            ]

        if end_date:
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)

            filtered = [
                user
                for user in filtered
                if (
                    user.get("createdAt")
                    and self._parse_date(user.get("createdAt")) is not None
                    and self._parse_date(user.get("createdAt")) <= end_date
                )
            ]

        if min_score is not None:
            filtered = [
                user
                for user in filtered
                if (
                    user.get("cibil_score")
                    and self._safe_int(user.get("cibil_score", 0)) >= min_score
                )
            ]

        if max_score is not None:
            filtered = [
                user
                for user in filtered
                if (
                    user.get("cibil_score")
                    and self._safe_int(user.get("cibil_score", 0)) <= max_score
                )
            ]

        # Updated to support multiple sources
        if sources and len(sources) > 0:
            # Only keep "strapi_cibil" records if "strapi_cibil" is in the sources list
            if "strapi_cibil" not in [s.lower() for s in sources]:
                filtered = []
        return filtered

    def _filter_subscribers(
        self,
        subscribers: List[Dict],
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sources: Optional[List[str]] = None,  # Changed from source to sources
    ) -> List[Dict]:
        """Filter subscribers"""
        from datetime import timezone

        filtered = subscribers

        if search:
            search_term = search.lower()
            special_sources = {"beehiiv", "strapi_loan", "strapi_cibil"}

            filtered = [
                sub
                for sub in filtered
                if (
                    (sub.get("email") and search_term in sub.get("email", "").lower())
                    or (
                        sub.get("source") and search_term in sub.get("source", "").lower()
                    )  # Normal source search
                    or (
                        "website" in search_term and sub.get("source") in special_sources
                    )  # Fetch all special sources on 'website' search
                )
            ]

        if start_date:
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)

            filtered = [
                sub
                for sub in filtered
                if (
                    sub.get("createdAt")
                    and self._parse_date(sub.get("createdAt")) is not None
                    and self._parse_date(sub.get("createdAt")) >= start_date
                )
            ]

        if end_date:
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)

            filtered = [
                sub
                for sub in filtered
                if (
                    sub.get("createdAt")
                    and self._parse_date(sub.get("createdAt")) is not None
                    and self._parse_date(sub.get("createdAt")) <= end_date
                )
            ]

        # Updated to support multiple sources
        if sources and len(sources) > 0:
            # Only keep "beehiiv" records if "beehiiv" is in the sources list
            if "beehiiv" not in [s.lower() for s in sources]:
                filtered = []
        return filtered

    def _convert_internal_user_to_lead(self, user) -> Union[UnifiedLeadBase, List[UnifiedLeadBase]]:
        """Convert internal user (or list of users) to unified lead format."""
        if isinstance(user, list):
            return [self._convert_internal_user_to_lead(u) for u in user]

        # Handle single user object
        if user.raw_data:
            # Check if raw_data is already a dictionary
            if isinstance(user.raw_data, dict):
                pass  # raw_data is already a dictionary, no need to deserialize
            elif isinstance(user.raw_data, str):
                # Deserialize JSON string to dictionary
                user.raw_data = json.loads(user.raw_data)
            else:
                # Handle unexpected types (e.g., log a warning or raise an error)
                logging.warning(f"Unexpected type for raw_data: {type(user.raw_data)}")
                user.raw_data = None  # Set to None or handle as needed

        # Handle the last_communicated field
        last_communicated = None
        if user.last_communicated:
            try:
                if isinstance(user.last_communicated, str):
                    last_communicated = self._parse_date(user.last_communicated)
                else:
                    last_communicated = user.last_communicated
            except (ValueError, TypeError):
                last_communicated = None

        return UnifiedLeadBase(
            id=user.id,
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone_number=user.phone_number,
            country_code=user.country_code,
            pan_number=user.pan_number,
            loan_amount=user.loan_amount,
            employment_type=user.employment_type,
            cibil_score=user.cibil_score,
            lead_source=user.source,
            last_communicated=last_communicated,
            created_at=user.created_on,
            company_name=user.company_name,
            monthly_income=user.monthly_income,
            loan_purpose=user.loan_purpose,
            loan_tenure=user.loan_tenure,
            raw_data=user.raw_data,
            subscription_status=user.subscription_status,
            tax_payer_type=user.tax_payer_type,
            tax_slab=user.tax_slab,
            category=user.category,
        )

    def _convert_loan_applications(self, loan_applications: List[Dict]) -> List[UnifiedLeadBase]:
        """Convert loan applications to unified lead format"""
        return [
            UnifiedLeadBase(
                id=str(uuid.uuid4()),  # Generate unique ID
                user_id=app.get("id"),
                document_name=app.get("documentId"),
                full_name=app.get("name"),
                email=app.get("email"),
                phone_number=app.get("phone_number"),
                loan_amount=self._safe_float(app.get("amount", 0)),
                loan_type=app.get("loan_type"),
                lead_source="strapi_loan",
                created_at=self._parse_date(app.get("createdAt")),
                raw_data=app,
                documents_count=0,  # Default value
            )
            for app in loan_applications
        ]

    def _convert_cibil_users(self, cibil_users: List[Dict]) -> List[UnifiedLeadBase]:
        """Convert CIBIL users to unified lead format"""
        return [
            UnifiedLeadBase(
                id=str(uuid.uuid4()),  # Generate unique ID
                user_id=user.get("id"),
                document_name=user.get("documentId"),
                full_name=user.get("name"),
                phone_number=user.get("phone_number"),
                pan_number=user.get("pan_number"),
                cibil_score=self._safe_int(user.get("cibil_score", 0)),
                lead_source="strapi_cibil",
                created_at=self._parse_date(user.get("createdAt")),
                raw_data=user,
                documents_count=0,  # Default value
            )
            for user in cibil_users
        ]

    def _convert_subscribers(self, subscribers: List[Dict]) -> List[UnifiedLeadBase]:
        """Convert subscribers to unified lead format"""
        return [
            UnifiedLeadBase(
                id=str(uuid.uuid4()),  # Generate unique ID
                email=sub.get("email"),
                lead_source="beehiiv",
                created_at=self._parse_date(sub.get("createdAt")),
                subscription_status=sub.get("status"),
                raw_data=sub,
                documents_count=0,  # Default value
            )
            for sub in subscribers
        ]

    def _filter_direct_cibil_users(
        self,
        direct_cibil_users: List[Dict],
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        sources: Optional[List[str]] = None,
        cibil_score: Optional[str] = None,
    ) -> List[Dict]:
        """Filter direct CIBIL users from repository"""
        filtered = direct_cibil_users

        # Apply search filter
        if search:
            search_term = search.lower()
            filtered = [
                user
                for user in filtered
                if (
                    (user.get("full_name") and search_term in user.get("full_name", "").lower())
                    or (
                        user.get("phone_number")
                        and search_term in user.get("phone_number", "").lower()
                    )
                    or (
                        user.get("pan_number") and search_term in user.get("pan_number", "").lower()
                    )
                    or (
                        user.get("lead_source")
                        and search_term in user.get("lead_source", "").lower()
                    )
                )
            ]

        # Apply date filters
        if start_date:
            filtered = [
                user
                for user in filtered
                if (
                    user.get("created_at")
                    and self._parse_date(user.get("created_at"))
                    and self._parse_date(user.get("created_at")) >= start_date
                )
            ]

        if end_date:
            filtered = [
                user
                for user in filtered
                if (
                    user.get("created_at")
                    and self._parse_date(user.get("created_at"))
                    and self._parse_date(user.get("created_at")) <= end_date
                )
            ]

        # Apply CIBIL score filters
        cibil_ranges = self._parse_cibil_score_range(cibil_score)
        if cibil_ranges:
            range_filtered = []
            for min_range, max_range in cibil_ranges:
                for user in filtered:
                    user_score = self._safe_int(user.get("cibil_score", 0))
                    if user_score and min_range <= user_score <= max_range:
                        range_filtered.append(user)
            filtered = range_filtered

        # Apply source filter
        if sources and "strapi_cibil" not in [s.lower() for s in sources]:
            filtered = []

        return filtered

    def _parse_date(self, date_value: Optional[Union[str, datetime]]) -> Optional[datetime]:
        """
        Safely parse a date string or datetime object to a timezone-aware datetime object.
        Supports:
        - Datetime objects (returns them with timezone if needed)
        - ISO format with or without timezone (e.g., "2023-10-01T12:00:00Z" or "2023-10-01T12:00:00+05:30")
        - Custom format: "YYYY-MM-DD HH:MM:SS.sss ±HHMM"
        """
        if not date_value:
            return None

        # If it's already a datetime object, just ensure it's timezone-aware
        if isinstance(date_value, datetime):
            if date_value.tzinfo is None:
                return date_value.replace(tzinfo=timezone.utc)
            return date_value

        # Only proceed with string parsing if we have a string
        if not isinstance(date_value, str):
            return None

        try:
            # Try parsing as ISO format (with or without timezone)
            if date_value.endswith("Z"):
                # Handle ISO format with "Z" (UTC)
                return datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            else:
                # Handle standard ISO format
                dt = datetime.fromisoformat(date_value)
                # Ensure the datetime is timezone-aware
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
        except ValueError:
            # If ISO parsing fails, try parsing with custom format
            try:
                # Handle custom format: "YYYY-MM-DD HH:MM:SS.sss ±HHMM"
                dt = datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S.%f %z")
                return dt
            except ValueError:
                # If both parsing attempts fail, return None
                return None

    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        if value is None:
            return None

        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    async def _fetch_cibil_users_for_combined_data(self) -> List[Dict]:
        """
        Fetch CIBIL report users directly from the credit_report_repository
        to include in the combined leads data.

        This ensures CIBIL users are included in the leads table.
        """
        try:
            # Import the credit report repository
            from app.repository.credit_report_repository import credit_report_repository

            # Get all credit reports (limit to 100 for performance)
            reports = await credit_report_repository.get_all_reports(limit=100, skip=0)

            # Transform reports to the unified lead format
            cibil_leads = []
            for report in reports:
                # Convert to dictionary if it's not already
                if not isinstance(report, dict):
                    report = dict(report)

                # Create a lead object
                lead = {
                    "id": report.get("id"),
                    "user_id": report.get("user_id"),
                    "full_name": f"{report.get('first_name', '')} {report.get('last_name', '')}".strip(),
                    "email": None,  # CIBIL reports may not have email
                    "phone_number": report.get("phone_number"),
                    "pan_number": report.get("pan_number"),
                    "cibil_score": report.get("credit_score"),
                    "lead_source": "strapi_cibil",
                    "created_at": report.get("created_at"),
                    "last_communicated": report.get("updated_at") or report.get("created_at"),
                    "documents_count": 1,  # At least one CIBIL document
                }

                cibil_leads.append(lead)

            return cibil_leads
        except Exception as e:
            logger.error(f"Error fetching CIBIL users for combined data: {str(e)}")
            return []


# Create singleton instance
lead_service = LeadService()
