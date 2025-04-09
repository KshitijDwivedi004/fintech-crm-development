from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
from app.repository.lead_repository import lead_repository
from app.service.external.strapi import StrapiService
from app.service.external.beehiiv import BeehiivService
from app.core.logger import logger

class LeadSyncService:
    def __init__(self):
        self.strapi_service = StrapiService()
        self.beehiiv_service = BeehiivService()

    async def sync_strapi_leads(
        self, 
        last_sync: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None,
        form_id: Optional[str] = None
    ):
        """Sync leads from Strapi with filters"""
        try:
            if form_id:
                leads = await self.strapi_service.fetch_specific_form_submissions(
                    form_id=form_id,
                    last_sync=last_sync
                )
            else:
                leads = await self.strapi_service.fetch_leads(
                    last_sync=last_sync,
                    filters=filters
                )

            for lead_data in leads:
                transformed_lead = self.strapi_service.transform_lead(lead_data)
                await lead_repository.merge_or_update_lead(transformed_lead)
            
            logger.info(f"Successfully synced {len(leads)} leads from Strapi")
        except Exception as e:
            logger.error(f"Error syncing Strapi leads: {str(e)}")
            raise

    async def sync_beehiiv_subscribers(
        self,
        publication_id: Optional[str] = None,
        last_sync: Optional[datetime] = None,
        subscription_tier: Optional[str] = None
    ):
        """Sync subscribers from Beehiiv for specific publication"""
        try:
            # Fetch publication details if ID provided
            publication_data = None
            if publication_id:
                publications = await self.beehiiv_service.fetch_publications()
                publication_data = next(
                    (p for p in publications if p["id"] == publication_id),
                    None
                )

            subscribers = await self.beehiiv_service.fetch_subscribers(
                publication_id=publication_id,
                last_sync=last_sync,
                subscription_tier=subscription_tier
            )

            for subscriber in subscribers:
                transformed_lead = self.beehiiv_service.transform_subscriber(
                    subscriber,
                    publication_data
                )
                await lead_repository.merge_or_update_lead(transformed_lead)

            logger.info(f"Successfully synced {len(subscribers)} subscribers from Beehiiv")
        except Exception as e:
            logger.error(f"Error syncing Beehiiv subscribers: {str(e)}")
            raise

    async def sync_all(
        self,
        last_sync: Optional[datetime] = None,
        strapi_filters: Optional[Dict[str, Any]] = None,
        beehiiv_publication_id: Optional[str] = None
    ):
        """Sync leads from all sources with filters"""
        await asyncio.gather(
            self.sync_strapi_leads(last_sync, strapi_filters),
            self.sync_beehiiv_subscribers(beehiiv_publication_id, last_sync)
        )