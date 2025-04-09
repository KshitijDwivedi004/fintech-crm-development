# app/repository/leads_repository.py
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_, select, func

from app.db.session import database
from app.models.leads import leads
from app.schemas.leads import LeadCreate, LeadUpdate, LeadFilter, LeadSource

class LeadRepository:
    async def create(self, obj_in: LeadCreate) -> str:
        """Create a new lead"""
        lead_id = str(uuid.uuid4())
        query = leads.insert().values(
            id=lead_id,
            **obj_in.dict(exclude_unset=True),
            is_active=True
        )
        await database.execute(query)
        return lead_id

    async def update(self, lead_id: str, obj_in: LeadUpdate) -> bool:
        """Update a lead"""
        query = (
            leads.update()
            .where(leads.c.id == lead_id)
            .values(**obj_in.dict(exclude_unset=True))
        )
        result = await database.execute(query)
        return bool(result)

    async def get_by_id(self, lead_id: str):
        """Get a lead by ID"""
        query = leads.select().where(leads.c.id == lead_id)
        return await database.fetch_one(query)

    async def get_by_source_id(self, source: str, source_id: str):
        """Get a lead by source and source_id"""
        query = leads.select().where(
            and_(
                leads.c.source == source,
                leads.c.source_id == source_id
            )
        )
        return await database.fetch_one(query)

    async def get_by_phone(self, phone_number: str):
        """Get a lead by phone number"""
        query = leads.select().where(leads.c.phone_number == phone_number)
        return await database.fetch_one(query)

    async def get_by_email(self, email: str):
        """Get a lead by email"""
        query = leads.select().where(leads.c.email == email)
        return await database.fetch_one(query)

    async def search_leads(
        self,
        search_term: Optional[str] = None,
        filters: Optional[LeadFilter] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search leads with filters"""
        query = leads.select().where(leads.c.is_active == True)

        # Apply search term
        if search_term:
            search_filter = or_(
                leads.c.full_name.ilike(f"%{search_term}%"),
                leads.c.email.ilike(f"%{search_term}%"),
                leads.c.phone_number.ilike(f"%{search_term}%")
            )
            query = query.where(search_filter)

        # Apply filters
        if filters:
            if filters.source:
                query = query.where(leads.c.source == filters.source)
            if filters.status:
                query = query.where(leads.c.status == filters.status)
            if filters.employment_type:
                query = query.where(leads.c.employment_type == filters.employment_type)
            if filters.start_date:
                query = query.where(leads.c.created_at >= filters.start_date)
            if filters.end_date:
                query = query.where(leads.c.created_at <= filters.end_date)
            if filters.min_loan_amount:
                query = query.where(leads.c.loan_amount >= filters.min_loan_amount)
            if filters.max_loan_amount:
                query = query.where(leads.c.loan_amount <= filters.max_loan_amount)

        # Add pagination
        query = query.offset(skip).limit(limit)
        query = query.order_by(leads.c.created_at.desc())

        return await database.fetch_all(query)

    async def merge_or_update_lead(self, lead_data: LeadCreate) -> str:
        """Merge or update lead data based on identifiers"""
        existing_lead = None

        # Check for existing lead by source_id
        if lead_data.source_id:
            existing_lead = await self.get_by_source_id(
                lead_data.source, lead_data.source_id
            )

        # Check by phone number
        if not existing_lead and lead_data.phone_number:
            existing_lead = await self.get_by_phone(lead_data.phone_number)

        # Check by email
        if not existing_lead and lead_data.email:
            existing_lead = await self.get_by_email(lead_data.email)

        if existing_lead:
            # Update existing lead
            update_data = LeadUpdate(
                **{k: v for k, v in lead_data.dict().items() if v is not None}
            )
            await self.update(existing_lead.id, update_data)
            return existing_lead.id
        else:
            # Create new lead
            return await self.create(lead_data)

lead_repository = LeadRepository()