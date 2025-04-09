import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.config import settings
from app.schemas.leads import LeadCreate, LeadSource

class StrapiService:
    def __init__(self):
        self.base_url = settings.STRAPI_API_URL
        self.api_token = settings.STRAPI_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    async def fetch_leads(
        self, 
        last_sync: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch leads from Strapi with custom filters
        
        filters example:
        {
            "loan_type": "business",
            "status": "pending",
            "loan_amount_gt": 50000
        }
        """
        async with httpx.AsyncClient() as client:
            # Build query parameters
            params = {
                "populate": "*",  # Get all relationships
                "sort": "createdAt:desc"
            }
            
            if last_sync:
                params["filters[createdAt][$gt]"] = last_sync.isoformat()

            # Add custom filters
            if filters:
                for key, value in filters.items():
                    if key.endswith('_gt'):
                        base_key = key[:-3]
                        params[f"filters[{base_key}][$gt]"] = value
                    elif key.endswith('_lt'):
                        base_key = key[:-3]
                        params[f"filters[{base_key}][$lt]"] = value
                    else:
                        params[f"filters[{key}][$eq]"] = value

            response = await client.get(
                f"{self.base_url}/api/leads",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()["data"]
            return data

    async def fetch_specific_form_submissions(
        self,
        form_id: str,
        last_sync: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Fetch submissions from a specific form"""
        async with httpx.AsyncClient() as client:
            params = {
                "populate": "*",
                "filters[form][id][$eq]": form_id
            }
            
            if last_sync:
                params["filters[createdAt][$gt]"] = last_sync.isoformat()

            response = await client.get(
                f"{self.base_url}/api/form-submissions",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            return response.json()["data"]

    def transform_lead(self, strapi_lead: Dict[str, Any]) -> LeadCreate:
        """Transform Strapi lead data to our lead schema"""
        attributes = strapi_lead["attributes"]
        
        # Extract loan information from relationships if available
        loan_info = attributes.get("loan_application", {}).get("data", {}).get("attributes", {})
        
        return LeadCreate(
            full_name=attributes.get("name"),
            email=attributes.get("email"),
            phone_number=attributes.get("phone"),
            source=LeadSource.STRAPI,
            source_id=str(strapi_lead["id"]),
            loan_amount=loan_info.get("amount") or attributes.get("loanAmount"),
            employment_type=attributes.get("employmentType"),
            metadata={
                "strapi_data": attributes,
                "form_id": attributes.get("form", {}).get("data", {}).get("id"),
                "loan_type": loan_info.get("type"),
                "additional_details": loan_info
            }
        )
