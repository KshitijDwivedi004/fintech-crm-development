# app/api/api_v1/endpoints/leads.py
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.sql.schema import Table

from app.api.api_v1 import deps
from app.repository.lead_repository import lead_repository
from app.schemas.leads import LeadCreate, LeadUpdate, LeadInDB, LeadFilter, LeadCombinedDataResponse, LeadSource, EmploymentType, LeadStatus, NameOrder
from app.models.user import users as UserModel  # Rename the import
from app.service.leads_sync_service import LeadSyncService
from datetime import datetime
from app.service.external_service import external_repository



router = APIRouter()
lead_sync_service = LeadSyncService()

@router.post("/", response_model=dict[str, str])
async def create_lead(
    *,
    lead_in: LeadCreate,
    current_user: Dict[str, Any] = Depends(deps.get_current_active_admin_ca_auditor),
):
    """Create new lead."""
    try:
        lead_id = await lead_repository.merge_or_update_lead(lead_in)
        return {"id": lead_id, "message": "Lead created/updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error creating lead: {str(e)}"
        )

@router.get("/", response_model=List[LeadInDB])
async def search_leads(
    search: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None,
    employment_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_loan_amount: Optional[float] = None,
    max_loan_amount: Optional[float] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=100),
    current_user: Dict[str, Any] = Depends(deps.get_current_active_admin_ca_auditor),
):
    """Search leads with filters."""
    filters = LeadFilter(
        source=source,
        status=status,
        employment_type=employment_type,
        start_date=start_date,
        end_date=end_date,
        min_loan_amount=min_loan_amount,
        max_loan_amount=max_loan_amount
    )
    
    leads = await lead_repository.search_leads(
        search_term=search,
        filters=filters,
        skip=skip,
        limit=limit
    )
    return leads

@router.get("/publications", response_model=List[Dict[str, Any]])
async def get_beehiiv_publications(
    current_user: Dict[str, Any] = Depends(deps.get_current_active_admin_ca_auditor),
):
    """Get list of available Beehiiv publications."""
    try:
        publications = await lead_sync_service.beehiiv_service.fetch_publications()
        return publications
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching publications: {str(e)}"
        )

@router.post("/sync", response_model=dict[str, str])
async def sync_leads(
    strapi_filters: Optional[Dict[str, Any]] = None,
    beehiiv_publication_id: Optional[str] = None,
    form_id: Optional[str] = None,
    subscription_tier: Optional[str] = None,
    #current_user: Dict[str, Any] = Depends(deps.get_current_active_admin_ca_auditor),
):
    """
    Manually trigger lead synchronization from all sources.
    
    Example strapi_filters:
    {
        "loan_type": "business",
        "status": "pending",
        "loan_amount_gt": 50000
    }
    """
    try:
        if form_id:
            # Sync specific form submissions from Strapi
            await lead_sync_service.sync_strapi_leads(form_id=form_id)
        else:
            # Sync all sources with filters
            await lead_sync_service.sync_all(
                strapi_filters=strapi_filters,
                beehiiv_publication_id=beehiiv_publication_id
            )
        return {"message": "Lead synchronization completed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error syncing leads: {str(e)}"
        )

@router.post("/sync/{source}", response_model=dict[str, str])
async def sync_specific_source(
    source: str,
    form_id: Optional[str] = None,
    publication_id: Optional[str] = None,
    subscription_tier: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(deps.get_current_active_admin_ca_auditor),
):
    """
    Manually trigger lead synchronization from a specific source.
    """
    try:
        if source.lower() == "strapi":
            await lead_sync_service.sync_strapi_leads(form_id=form_id)
        elif source.lower() == "beehiiv":
            await lead_sync_service.sync_beehiiv_subscribers(
                publication_id=publication_id,
                subscription_tier=subscription_tier
            )
        elif source.lower() == "whatsapp":
            await lead_sync_service.sync_whatsapp_contacts()
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid source. Must be 'strapi', 'beehiiv', or 'whatsapp'"
            )
        return {"message": f"Lead synchronization from {source} completed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error syncing leads from {source}: {str(e)}"
        )


