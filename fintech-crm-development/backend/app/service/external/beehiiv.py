import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.config import settings
from app.schemas.leads import LeadCreate, LeadSource

class BeehiivService:
    def __init__(self):
        self.base_url = "https://api.beehiiv.com/v2"
        self.api_key = settings.BEEHIIV_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def fetch_publications(self) -> List[Dict[str, Any]]:
        """Fetch all available publications"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/publications",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()["data"]

    async def fetch_subscribers(
        self, 
        publication_id: Optional[str] = None,
        last_sync: Optional[datetime] = None,
        status: str = "active",
        subscription_tier: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch subscribers from Beehiiv with filters
        
        Args:
            publication_id: Optional specific publication ID
            last_sync: Optional last sync timestamp
            status: Subscriber status (active, pending, etc.)
            subscription_tier: Optional specific tier
        """
        async with httpx.AsyncClient() as client:
            params = {
                "limit": 100,
                "status": status
            }
            
            if publication_id:
                params["publication_id"] = publication_id
            
            if last_sync:
                params["created_after"] = last_sync.isoformat()
            
            if subscription_tier:
                params["subscription_tier"] = subscription_tier

            response = await client.get(
                f"{self.base_url}/subscribers",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            return response.json()["data"]

    async def fetch_subscriptions_by_email(
        self,
        email: str
    ) -> List[Dict[str, Any]]:
        """Fetch all subscriptions for a specific email"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/subscribers/email/{email}",
                headers=self.headers
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            return response.json()["data"]

    def transform_subscriber(
        self, 
        subscriber: Dict[str, Any],
        publication_data: Optional[Dict[str, Any]] = None
    ) -> LeadCreate:
        """Transform Beehiiv subscriber data to our lead schema"""
        # Extract subscription details
        subscription_info = subscriber.get("subscription", {})
        
        return LeadCreate(
            full_name=subscriber.get("name"),
            email=subscriber.get("email"),
            source=LeadSource.BEEHIIV,
            source_id=subscriber.get("id"),
            metadata={
                "beehiiv_data": subscriber,
                "publication": publication_data,
                "subscription_status": subscription_info.get("status"),
                "subscription_tier": subscription_info.get("tier"),
                "subscription_date": subscription_info.get("created_at"),
                "custom_fields": subscriber.get("custom_fields", {})
            }
        )