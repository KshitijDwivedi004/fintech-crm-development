import os
from typing import Dict, List, Optional, Union
import httpx
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from app.core.config import settings
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class ExternalDataRepository:
    def __init__(self):
        # Strapi configuration
        self.strapi_base_url = settings.STRAPI_API_URL
        self.strapi_api_token = settings.STRAPI_API_TOKEN
        
        # Beehiiv configuration
        self.beehiiv_api_key = settings.BEEHIIV_API_KEY
        self.beehiiv_publication_id = settings.BEEHIIV_PUBLICATION_ID
        self.beehiiv_base_url = "https://api.beehiiv.com/v2"

        # Validate required environment variables
        if not all([self.strapi_base_url, self.strapi_api_token, 
                   self.beehiiv_api_key, self.beehiiv_publication_id]):
            raise ValueError("Missing required environment variables")

        # Initialize HTTP client with default timeout
        self.timeout = httpx.Timeout(30.0)



    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_strapi_loan_applications(self) -> List[Dict]:
        """
        Fetch all loan applications from Strapi using pagination with retry logic.
        """
        headers = {
            'Authorization': f'Bearer {self.strapi_api_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.strapi_base_url}/api/loan-applies"
        page = 1
        page_size = 100  # Max records per request
        all_applications = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                while True:
                    params = {
                        'pagination[page]': page,
                        'pagination[pageSize]': page_size,
                        'sort': 'createdAt:desc'
                    }

                    response = await client.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    data = response.json()

                    applications = [
                        {
                            'id': app.get('id'),
                            'documentId': app.get('documentId'),
                            'name': app.get('name'),
                            'email': app.get('email'),
                            'phone_number': app.get('phone_number'),
                            'amount': app.get('amount'),
                            'loan_type': app.get('loan_type'),
                            'createdAt': app.get('createdAt'),
                            'source': 'strapi_loan'
                        }
                        for app in data.get('data', [])
                    ]

                    if not applications:
                        break  # Stop fetching if no more records

                    all_applications.extend(applications)
                    page += 1  # Move to the next page

            return all_applications

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Strapi REST error: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Network error occurred: {e}")


    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_strapi_cibil_users(self, page: int = 1, page_size: int = 1000) -> List[Dict]:
        """
        Fetch CIBIL users from Strapi with retry logic
        """
        headers = {
            'Authorization': f'Bearer {self.strapi_api_token}',
            'Content-Type': 'application/json'
        }

        url = f"{self.strapi_base_url}/api/cibil-check-users"
        params = {
            'pagination[page]': page,
            'pagination[pageSize]': page_size,
            'sort': 'first_name:asc'
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

                users = []
                for user in data.get('data', []):
                    user_data = {
                        'id': user.get('id'),
                        'documentId': user.get('documentId'),
                        'name': f"{user.get('first_name')} {user.get('last_name')}".strip(),
                        'phone_number': user.get('mobile_number'),
                        'pan_number': user.get('pan_number'),
                        'cibil_score': user.get('CIBIL_score'),
                        'createdAt': user.get('createdAt'),
                        'source': 'strapi_cibil'
                    }
                    users.append(user_data)
                return users
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Strapi REST error: {e.response.text}")
        

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_beehiiv_subscribers(self) -> List[Dict]:
        """
        Fetch subscribers from Beehiiv with retry logic and pagination
        """
        headers = {
            "Authorization": f"Bearer {self.beehiiv_api_key}",
            "Content-Type": "application/json"
        }
        
        all_subscribers = []
        cursor: Optional[str] = None
        
        try:
            while True:
                endpoint = f"/publications/{self.beehiiv_publication_id}/subscriptions"
                params = {"limit": 100}
                if cursor:
                    params["cursor"] = cursor
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        f"{self.beehiiv_base_url}{endpoint}",
                        headers=headers,
                        params=params
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    for subscriber in data.get('data', []):
                        subscriber_data = {
                            'id': subscriber.get('id'),
                            'email': subscriber.get('email'),
                            'status': subscriber.get('status'),
                            'createdAt': self.parse_unix_timestamp(subscriber.get('created')),
                            'source': 'beehiiv'
                        }
                        all_subscribers.append(subscriber_data)
                    
                    pagination = data.get("pagination", {})
                    cursor = pagination.get("next_cursor")
                    
                    if not cursor or not pagination.get("has_more"):
                        break
            
            return all_subscribers

        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, 
                              detail="Error fetching subscribers from Beehiiv")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, 
                              detail="Service temporarily unavailable")

    async def get_all_external_data(self) -> Dict:
        """
        Fetch all external data concurrently from different sources
        """
        try:
            # Fetch all data concurrently
             #cibil_users,
            loan_applications, cibil_users, subscribers = await asyncio.gather(
                self.fetch_strapi_loan_applications(),
                self.fetch_strapi_cibil_users(),
                self.fetch_beehiiv_subscribers()
            )
            
            return {
                'loan_applications': loan_applications,
                'cibil_users': cibil_users,
                'subscribers': subscribers
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching external data: {str(e)}"
            )
    def parse_unix_timestamp(self,timestamp: int) -> str:
        """Convert Unix timestamp to formatted datetime string with timezone +0530"""
        dt_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)  # Convert to UTC
        dt_ist = dt_utc + timedelta(hours=5, minutes=30)  # Convert to IST (+0530)
        return dt_ist.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " +0530"

# Create singleton instance
external_repository = ExternalDataRepository()

