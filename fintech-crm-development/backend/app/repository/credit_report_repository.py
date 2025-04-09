from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, desc, func, or_
from app.models.credit_report import credit_reports
from app.db.session import database
from app.core.logger import logger


class CreditReportRepository:
    """
    Repository for credit report operations using SQLAlchemy Core
    """

    async def create(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new credit report entry in the database
        """
        # Ensure created_at and updated_at fields are set
        if "created_at" not in report_data:
            report_data["created_at"] = datetime.utcnow()
        if "updated_at" not in report_data:
            report_data["updated_at"] = datetime.utcnow()

        # Set defaults for new fields if not provided
        if "lead_source" not in report_data:
            report_data["lead_source"] = "Website"

        query = credit_reports.insert().values(**report_data)
        report_id = await database.execute(query)
        return {**report_data, "id": report_id}

    async def update(
        self, pan_number: str, phone_number: str, report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing credit report
        """
        # Always update the updated_at timestamp
        report_data["updated_at"] = datetime.utcnow()

        query = (
            credit_reports.update()
            .where(
                and_(
                    credit_reports.c.pan_number == pan_number,
                    credit_reports.c.phone_number == phone_number,
                )
            )
            .values(**report_data)
        )
        await database.execute(query)
        return await self.get_by_pan_and_phone(pan_number, phone_number)

    async def update_user_id(self, pan_number: str, phone_number: str, user_id: str) -> bool:
        """
        Update the user_id for a credit report identified by PAN and phone number

        Args:
            pan_number: The PAN number
            phone_number: The phone number
            user_id: The user ID to set

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = """
                UPDATE credit_reports
                SET user_id = :user_id, updated_at = NOW()
                WHERE pan_number = :pan_number AND phone_number = :phone_number
            """

            params = {"user_id": user_id, "pan_number": pan_number, "phone_number": phone_number}

            result = await self.database.execute(query=query, values=params)
            return result is not None
        except Exception as e:
            self.logger.error(f"Error updating user_id for credit report: {str(e)}")
            return False

    async def delete_by_phone(self, phone_number: str) -> bool:
        """
        Delete (soft delete) all credit reports for a given phone number

        Args:
            phone_number: The phone number to delete reports for

        Returns:
            bool: True if operation was successful
        """
        try:
            query = (
                credit_reports.update()
                .where(credit_reports.c.phone_number == phone_number)
                .values(is_valid=False, updated_at=datetime.utcnow())
            )

            result = await self.database.execute(query)
            return True
        except Exception as e:
            logger.error(f"Error deleting credit report by phone number: {str(e)}")
            return False

    async def get_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent valid credit report for a phone number

        Args:
            phone_number: The phone number to search for

        Returns:
            The credit report record or None if not found
        """
        try:
            query = (
                select([credit_reports])
                .where(
                    and_(
                        credit_reports.c.phone_number == phone_number,
                        credit_reports.c.is_valid == True,
                    )
                )
                .order_by(credit_reports.c.created_at.desc())
            )

            result = await self.database.fetch_one(query)
            if result:
                return dict(result)
            return None
        except Exception as e:
            logger.error(f"Error fetching credit report by phone number: {str(e)}")
            return None

    async def soft_delete_by_phone(self, phone_number: str) -> bool:
        """
        Soft delete credit reports by phone number

        Args:
            phone_number: Phone number associated with the credit reports

        Returns:
            bool: True if at least one record was updated, False otherwise
        """
        try:
            from sqlalchemy import update
            from app.models.credit_report import credit_reports
            from datetime import datetime

            query = (
                update(credit_reports)
                .where(credit_reports.c.phone_number == phone_number)
                .values(is_valid=False, updated_at=datetime.utcnow())
            )

            result = await self.database.execute(query)

            # Return True if at least one record was affected
            return result > 0
        except Exception as e:
            logger.error(f"Error in soft_delete_by_phone: {str(e)}")
            return False

    async def delete(self, report_id: int) -> bool:
        """
        Soft-delete a credit report by setting is_valid to False
        """
        query = (
            credit_reports.update()
            .where(credit_reports.c.id == report_id)
            .values(is_valid=False, updated_at=datetime.utcnow())
        )
        result = await database.execute(query)
        return result > 0

    async def hard_delete(self, report_id: int) -> bool:
        """
        Hard-delete a credit report (completely remove from database)
        """
        query = credit_reports.delete().where(credit_reports.c.id == report_id)
        result = await database.execute(query)
        return result > 0

    async def get_by_id(self, report_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a credit report by ID
        """
        query = select([credit_reports]).where(
            and_(
                credit_reports.c.id == report_id,
                credit_reports.c.is_valid == True,
            )
        )

        result = await database.fetch_one(query)
        if result:
            return dict(result)
        return None

    async def get_by_pan_and_phone(
        self, pan_number: str, phone_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a credit report by PAN number and phone number
        """
        query = (
            select([credit_reports])
            .where(
                and_(
                    credit_reports.c.pan_number == pan_number,
                    credit_reports.c.phone_number == phone_number,
                    credit_reports.c.is_valid == True,
                )
            )
            .order_by(desc(credit_reports.c.updated_at))
        )

        result = await database.fetch_one(query)
        if result:
            return dict(result)
        return None

    async def get_recent_report(
        self, pan_number: str, phone_number: str, days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Get a recent credit report (within specified days) by PAN number and phone number
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = (
            select([credit_reports])
            .where(
                and_(
                    credit_reports.c.pan_number == pan_number,
                    credit_reports.c.phone_number == phone_number,
                    credit_reports.c.updated_at >= cutoff_date,
                    credit_reports.c.is_valid == True,
                )
            )
            .order_by(desc(credit_reports.c.updated_at))
        )

        result = await database.fetch_one(query)
        if result:
            return dict(result)
        return None

    async def get_all_reports(
        self, limit: int = 100, skip: int = 0, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all credit reports with pagination and optional user filtering
        """
        conditions = [credit_reports.c.is_valid == True]

        if user_id:
            conditions.append(credit_reports.c.user_id == user_id)

        query = (
            select([credit_reports])
            .where(and_(*conditions))
            .order_by(desc(credit_reports.c.updated_at))
            .limit(limit)
            .offset(skip)
        )

        results = await database.fetch_all(query)
        return [dict(result) for result in results]

    async def search_reports(
        self, search_term: str, limit: int = 100, skip: int = 0, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for credit reports by name, PAN, or phone number with optional user filtering
        """
        # Convert search term to lowercase for case-insensitive search
        search_pattern = f"%{search_term}%"

        conditions = [
            credit_reports.c.is_valid == True,
            or_(
                credit_reports.c.first_name.ilike(search_pattern),
                credit_reports.c.last_name.ilike(search_pattern),
                credit_reports.c.pan_number.ilike(search_pattern),
                credit_reports.c.phone_number.ilike(search_pattern),
            ),
        ]

        if user_id:
            conditions.append(credit_reports.c.user_id == user_id)

        query = (
            select([credit_reports])
            .where(and_(*conditions))
            .order_by(desc(credit_reports.c.updated_at))
            .limit(limit)
            .offset(skip)
        )

        results = await database.fetch_all(query)
        return [dict(result) for result in results]

    async def count_reports(self, user_id: Optional[str] = None) -> int:
        """
        Count total number of valid credit reports with optional user filtering
        """
        conditions = [credit_reports.c.is_valid == True]

        if user_id:
            conditions.append(credit_reports.c.user_id == user_id)

        query = select([func.count()]).select_from(credit_reports).where(and_(*conditions))

        result = await database.fetch_val(query)
        return result if result else 0


credit_report_repository = CreditReportRepository()
