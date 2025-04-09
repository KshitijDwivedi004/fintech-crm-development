import datetime
import uuid
from typing import Any, Dict, Optional, Union

from sqlalchemy import func, select

from api.db_utils import database
from api.db_utils import users
from api.schemas.user import UserCreate, UserCreateKafka, UserUpdate, UserUpdateDeatils
from api.schemas.user import UserCreateManual
from api.schemas.user import UserCreateManual
import uuid
from datetime import datetime
from fastapi import HTTPException, status
from api.schemas.user import UserUpdateRequest
from api.db_utils import database, contacts
from api.db_utils import database, messages, templates
from api.schemas.message_schema import MessageBase
from sqlalchemy import cast, TIMESTAMP, Numeric
from sqlalchemy import select, func, and_, over, or_




class UserRepository:

    def __init__(self, database):
        self.database = database

    async def get_by_email(self, email: str):
        query = users.select().where(users.c.email == email)
        return await self.database.fetch_one(query)

    async def update_password(self, user_id: str, hashed_password: str):
        query = users.update().where(users.c.id == user_id).values(hashed_password=hashed_password)
        return await self.database.execute(query)

    """
    Repository class for managing users in the system.

    This class provides methods for creating, retrieving, and updating user objects,
    as well as checking the active status of a user.

    Attributes:
        None
    """

    async def create(self, obj_in: UserCreateKafka):
        """
        Create a new user in the system.

        Args:
            obj_in (UserCreateKafka): The user data to create.

        Returns:
            UserCreate: The created user object.
        """
        query = users.insert().values(
            id=str(uuid.uuid4()),
            country_code=obj_in.country_code,
            phone_number=obj_in.phone_number,
            status=obj_in.status,
            is_active=True,
            role="User",
            source=obj_in.source,
        )
        await database.execute(query=query)
        return obj_in

    async def update_basic_details(self, obj_in: UserCreate, id=str):
        """
        Update user basic details in the system.

        Args:
            obj_in (UserCreate): The user data to update.

        Returns:
            UserCreate: The updated user id.
        """
        query = (
            users.update()
            .where(id == users.c.id)
            .values(
                full_name=obj_in.full_name,
                email=obj_in.email,
                updated_on=datetime.now(),
            )
        )
        return await database.execute(query=query)

    async def get_by_phone(self, phone: str):
        """
        Retrieve a user by their phone number.

        Args:
            phone (str): The phone number of the user to retrieve.

        Returns:
            User: The retrieved user object.
        """
        query = users.select().where(phone == users.c.phone_number)
        return await database.fetch_one(query=query)

    async def get_list_users(
        self, name_order: str = None, search_query: dict = None, skip: int = 0, limit: int = 10
    ):
        """
        Retrieve a paginated list of users.

        Args:
            name_order (str, optional): Sorting order by name (A-Z or Z-A).
            search_query (dict, optional): Search filters.
            skip (int, optional): Number of records to skip.
            limit (int, optional): Number of records to return per page.

        Returns:
            List[users]: A paginated list of user objects matching the criteria.
        """
        query = users.select().where(users.c.is_active == True).offset(skip).limit(limit)

        if name_order == "A-Z":
            query = query.where(users.c.full_name.isnot(None)).order_by(users.c.full_name.asc())
        elif name_order == "Z-A":
            query = query.where(users.c.full_name.isnot(None)).order_by(users.c.full_name.desc())
        else:
            query = query.order_by(users.c.last_communicated.desc())

        if search_query:
            for column, value in search_query.items():
                query = query.where(users.c[column].ilike(f"%{value}%"))

        return await database.fetch_all(query=query)

    async def users_count(self, search_query: dict = None, name_order: str = None):
        query = select([func.count()]).select_from(users).where(users.c.is_active == True)
        if search_query:
            for column, value in search_query.items():
                # Add search conditions for each column and value
                query = query.where(users.c[column].ilike(f"%{value}%"))
        if name_order:
            query = query.where(users.c.full_name.isnot(None))
        return await database.fetch_val(query=query)

    async def update(self, id: str, obj_in: Union[UserUpdate, Dict[str, Any]]):
        """
        Update an existing user in the system.

        Args:
            id (str): The ID of the user to update.
            obj_in (Union[UserUpdate, Dict[str, Any]]): The updated user data.

        Returns:
            str: The ID of the updated user.
        """
        query = (
            users.update()
            .where(id == users.c.id)
            .values(
                full_name=obj_in.full_name,
                phone_number=obj_in.phone_number,
                org_Name=obj_in.org_Name,
                pan_number=obj_in.pan_number,
                filling_status=obj_in.filling_status,
                service_selected=obj_in.service_selected,
                tax_payer_type=obj_in.tax_payer_type,
            )
            .returning(users.c.id)
        )
        return await database.execute(query=query)

    async def update_last_communication(self, phone_number: str, response: str):
        """
        Update last communication details in the system.

        Args:
            phone_number (str): The phone number of the user to update.
            response: The timestamps.

        Returns:
            str: The ID of the user.
        """
        query = (
            users.update()
            .where(phone_number == users.c.phone_number)
            .values(
                last_communicated=response,
            )
            .returning(users.c.id)
        )
        return await database.execute(query=query)

    async def is_active(self, user: users):
        """
        Check if a user is active.

        Args:
            user (User): The user to check.

        Returns:
            bool: True if the user is active, False otherwise.
        """
        return user.is_active

    async def set_is_active(self, id: str, is_active: bool):
        """
        Set an auditor's is_active status.

        Args:
            id (str): The ID of the auditor to update.
            is_active (bool): The is_active status value.

        Returns:
            str: The ID of the updated auditor.
        """
        query = (
            users.update()
            .where(id == users.c.id)
            .values(
                is_active=is_active,
            )
            .returning(users.c.id)
        )
        return await database.execute(query=query)

    async def get_recent_users(self, days: int):
        """
        Retrieve a list of users that have been created within the last X days."""

        # Calculate the date threshold
        threshold_date = datetime.utcnow() - datetime.timedelta(days=days)
        query = users.select().where(
            users.c.created_on >= threshold_date, users.c.is_active == True
        )
        return await database.fetch_all(query=query)

    async def update_user_details(self, obj_in: UserUpdateDeatils, id=str):
        """
        Update user basic details in the system.

        Args:
            obj_in (UserUpdateDeatils): The user data to update.

        Returns:
            UserUpdateDeatils: The updated user id.
        """
        query = (
            users.update()
            .where(id == users.c.id)
            .values(
                tax_payer_type=obj_in.tax_payer_type,
                tax_slab=obj_in.tax_slab,
                category=obj_in.category,
                updated_on=datetime.now(),
            )
        )
        return await database.execute(query=query)

    async def get_by_email_and_source(self, email: str, source: str):
        query = users.select().where((users.c.email == email) & (users.c.source == source))
        return await self.database.fetch_one(query)

    async def create_from_external(self, user_data: dict):
        query = users.insert().values(
            id=str(uuid.uuid4()),
            email=user_data.get("email"),
            full_name=user_data.get("full_name"),
            phone_number=user_data.get("phone_number"),
            source=user_data.get("source"),
            loan_amount=user_data.get("loan_amount"),
            employment_type=user_data.get("employment_type"),
            company_name=user_data.get("company_name"),
            monthly_income=user_data.get("monthly_income"),
            loan_purpose=user_data.get("loan_purpose"),
            loan_tenure=user_data.get("loan_tenure"),
            raw_data=user_data.get("raw_data"),
            is_active=True,
            role="External",
            created_on=datetime.now(),
            updated_on=datetime.now(),
        )
        return await self.database.execute(query)

    async def create_manual(self, obj_in: UserCreateManual):
        print("Starting user creation process...")

        if obj_in.phone_number:
            print(f"Checking if user with phone number {obj_in.phone_number} already exists...")
            existing_user = await self.get_by_phone(obj_in.phone_number)
            if existing_user:
                print(f"User with phone number {obj_in.phone_number} already exists.")
                
                # Check if auditor_id is NULL and update it if necessary
                if existing_user.auditor_id is None:
                    update_query = (
                        users.update()
                        .where(users.c.id == existing_user.id)
                        .values(auditor_id="auditor")
                    )
                    try:
                        await self.database.execute(query=update_query)
                        print(f"Updated auditor_id for existing user {existing_user.id}")
                    except Exception as e:
                        print(f"Error updating auditor_id for existing user: {e}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error updating auditor_id for existing user"
                        )
                
                return existing_user  # Return existing user instead of raising exception

        new_user_id = str(uuid.uuid4())
        print(f"Generated new user ID: {new_user_id}")

        values = {
            "id": new_user_id,
            "full_name": obj_in.full_name,
            "email": obj_in.email,
            "phone_number": obj_in.phone_number,
            "country_code": obj_in.country_code,
            "status": obj_in.status,
            "role": obj_in.role,
            "is_active": obj_in.is_active,
            "org_Name": obj_in.org_Name,
            "pan_number": obj_in.pan_number,
            "filling_status": obj_in.filling_status,
            "service_selected": obj_in.service_selected,
            "tax_payer_type": obj_in.tax_payer_type,
            "tax_slab": obj_in.tax_slab,
            "income_slab": obj_in.income_slab,
            "regime_opted": obj_in.regime_opted,
            "gst_number": obj_in.gst_number,
            "category": obj_in.category,
            "source": obj_in.source,
            "loan_amount": obj_in.loan_amount,
            "employment_type": obj_in.employment_type,
            "company_name": obj_in.company_name,
            "monthly_income": obj_in.monthly_income,
            "loan_purpose": obj_in.loan_purpose,
            "loan_tenure": obj_in.loan_tenure,
            "raw_data": obj_in.raw_data,
            "cibil_score": obj_in.cibil_score,
            "subscription_status": obj_in.subscription_status,
            "created_on": datetime.utcnow(),
            "updated_on": datetime.utcnow(),
            "location": obj_in.location,
            "auditor_id": "auditor"  # Set auditor_id to "auditor" for new users
        }

        print("Inserting new user into the database...")
        query = users.insert().values(**values)
        try:
            await self.database.execute(query=query)
            print("User inserted successfully.")
        except Exception as e:
            print(f"Error inserting user into the database: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error inserting user into the database",
            )

        print(f"Fetching created user with ID {new_user_id}...")
        created_user = await self.get_by_id(new_user_id)
        if not created_user:
            print(f"Failed to retrieve created user with ID {new_user_id}.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created user",
            )

        print("User creation process completed successfully.")
        return {"message": "New user created", "user": created_user}
    
    async def get_by_id(self, user_id: str):
        query = users.select().where(users.c.id == user_id)
        return await self.database.fetch_one(query=query)

    async def update_user(self, obj_in: UserUpdateRequest):
        print(f"Starting update process for user ID: {obj_in.id}")

        # Check if user exists
        existing_user = await self.get_by_id(obj_in.id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No user found with the provided ID"
            )

        # Prepare update data - only include fields that were explicitly set
        # This is the key to allowing partial updates
        update_data = {k: v for k, v in obj_in.dict(exclude_unset=True).items() if v is not None}

        # Remove the ID from update_data since we don't want to update that
        if "id" in update_data:
            del update_data["id"]

        # Add the updated_on timestamp
        update_data["updated_on"] = datetime.utcnow()

        # If no fields to update, raise an error
        if len(update_data) <= 1:  # Only contains updated_on
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update"
            )

        # Print update data for debugging
        print(f"Update data: {update_data}")

        query = users.update().where(users.c.id == obj_in.id).values(**update_data)

        try:
            print(f"Updating user with ID {obj_in.id} in the database...")
            await self.database.execute(query=query)
            print("User updated successfully.")
        except Exception as e:
            print(f"Error updating user in the database: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user in the database: {str(e)}",
            )

        updated_user = await self.get_by_id(obj_in.id)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated user",
            )

        print("User update process completed successfully.")
        return updated_user
    
    async def get_users_with_messages(self, unnamed: bool = False, unread: bool = False):
        # Subquery for latest messages
        latest_messages = (
            select(
                messages.c.id,
                messages.c.phone_number,
                messages.c.message_text,
                messages.c.message_id,
                messages.c.message_type,
                messages.c.message_sender,
                messages.c.timestamp,
                messages.c.media_id,
                messages.c.latitude,
                messages.c.longitude,
                func.row_number().over(
                    partition_by=messages.c.phone_number,
                    order_by=messages.c.timestamp.desc()
                ).label("rn")
            )
        ).subquery()

        # Subquery for unread counts
        unread_counts = (
            select(
                messages.c.phone_number,
                func.count().label("unread_count")
            )
            .where(
                messages.c.message_sender == "user",
                messages.c.read == False
            )
            .group_by(messages.c.phone_number)
        ).subquery()

        # Main query selecting all user columns
        query = (
            select(
                users,
                latest_messages.c.id.label("message_id"),
                latest_messages.c.message_text,
                latest_messages.c.message_id.label("message_message_id"),
                latest_messages.c.message_type,
                latest_messages.c.message_sender,
                latest_messages.c.timestamp,
                latest_messages.c.media_id,
                latest_messages.c.latitude,
                latest_messages.c.longitude,
                unread_counts.c.unread_count
            )
            .select_from(
                users.outerjoin(
                    latest_messages,
                    and_(
                        users.c.phone_number == latest_messages.c.phone_number,
                        latest_messages.c.rn == 1
                    )
                ).outerjoin(
                    unread_counts,
                    users.c.phone_number == unread_counts.c.phone_number
                )
            )
            .where(
                and_(
                    users.c.phone_number.isnot(None),
                    users.c.auditor_id.isnot(None)  
                )
            )
        )

        # Apply filters
        conditions = []
        if unnamed:
            conditions.append(users.c.full_name.is_(None))
        if unread:
            conditions.append(func.coalesce(unread_counts.c.unread_count, 0) > 0)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(
            func.coalesce(
                func.to_timestamp(cast(latest_messages.c.timestamp, Numeric)),  
                cast(users.c.created_on, TIMESTAMP)                           
            ).desc(),
            users.c.created_on.desc()
        )
        
        # Execute and process results
        result = await database.fetch_all(query=query)
        
        users_response = []
        for row in result:
            has_message = row["message_id"] is not None
            unread_count = row["unread_count"] or 0
            
            message_data = {}
            if has_message:
                message_data = {
                    "id": row["message_id"],
                    "phone_number": row["phone_number"],
                    "message_text": row["message_text"],
                    "message_id": row["message_message_id"],
                    "message_type": row["message_type"],
                    "message_sender": row["message_sender"],
                    "timestamp": row["timestamp"],
                    "media_id": row["media_id"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"]
                }
            
            # Include all user fields
            user_data = {key: row[key] for key in users.columns.keys()}
            user_data["latest_message"] = message_data if has_message else None
            user_data["unread_user_messages_count"] = unread_count
            
            users_response.append(user_data)
        
        return users_response

    async def search_users(self, keyword: str):
        # Subquery to get latest message per user
        latest_messages = (
            select(
                messages.c.id,
                messages.c.phone_number,
                messages.c.message_text,
                messages.c.message_id,
                messages.c.message_type,
                messages.c.message_sender,
                messages.c.timestamp,
                messages.c.media_id,
                messages.c.latitude,
                messages.c.longitude,
                func.row_number().over(
                    partition_by=messages.c.phone_number,
                    order_by=messages.c.timestamp.desc()
                ).label("rn")
            )
        ).subquery()

        # Subquery for unread message count per user
        unread_counts = (
            select(
                messages.c.phone_number,
                func.count().label("unread_count")
            )
            .where(
                messages.c.message_sender == "user",
                messages.c.read == False
            )
            .group_by(messages.c.phone_number)
        ).subquery()

        # Main query
        query = (
            select(
                users,
                latest_messages.c.id.label("message_id"),
                latest_messages.c.message_text,
                latest_messages.c.message_id.label("message_message_id"),
                latest_messages.c.message_type,
                latest_messages.c.message_sender,
                latest_messages.c.timestamp,
                latest_messages.c.media_id,
                latest_messages.c.latitude,
                latest_messages.c.longitude,
                unread_counts.c.unread_count
            )
            .select_from(
                users.outerjoin(
                    latest_messages,
                    and_(
                        users.c.phone_number == latest_messages.c.phone_number,
                        latest_messages.c.rn == 1
                    )
                ).outerjoin(
                    unread_counts,
                    users.c.phone_number == unread_counts.c.phone_number
                )
            )
            .where(
                or_(
                    users.c.full_name.ilike(f"%{keyword}%"),
                    users.c.phone_number.ilike(f"%{keyword}%"),
                    users.c.email.ilike(f"%{keyword}%")
                )
            )
            .where(users.c.phone_number.isnot(None))
            .where(users.c.auditor_id.isnot(None))  # Added this line
            .order_by(
                func.coalesce(
                    func.to_timestamp(cast(latest_messages.c.timestamp, Numeric)),
                    cast(users.c.created_on, TIMESTAMP)
                ).desc(),
                users.c.created_on.desc()
            )
        )

        # Execute and process results
        results = await database.fetch_all(query=query)
        
        users_response = []
        for row in results:
            has_message = row["message_id"] is not None
            unread_count = row["unread_count"] or 0

            message_data = {}
            if has_message:
                message_data = {
                    "id": row["message_id"],
                    "phone_number": row["phone_number"],
                    "message_text": row["message_text"],
                    "message_id": row["message_message_id"],
                    "message_type": row["message_type"],
                    "message_sender": row["message_sender"],
                    "timestamp": row["timestamp"],
                    "media_id": row["media_id"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"]
                }

            # Include all user fields
            user_data = {key: row[key] for key in users.columns.keys()}
            user_data["latest_message"] = message_data if has_message else None
            user_data["unread_user_messages_count"] = unread_count

            users_response.append(user_data)

        return users_response


user_repository = UserRepository(database)
