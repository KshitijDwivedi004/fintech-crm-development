import uuid
from typing import Any, Dict, Union

import sqlalchemy

from app.core.config import settings
from app.db.session import database
from app.models.auditor import auditor, auditor_task
from app.models.ca import ca, ca_profile
from app.schemas.CA import CACreate, CAUpdate, ProfilePictureCreate
from app.utils.cryptoUtil import verify_password
from sqlalchemy import func


class CARepository:
    """
    Repository class for managing CAs (Certification Authorities) in the system.

    This class provides methods for creating, retrieving, updating, and deleting CA objects,
    as well as performing various operations related to CAs such as authentication, profile management,
    and retrieving lists of auditors created by CAs.

    Attributes:
        None
    """

    async def create(self, obj_in: CACreate):
        """
        Create a new CA (Chartered Accountant) record.

        Args:
            obj_in (CACreate): The CA object to create.

        Returns:
            CACreate: The created CA object.
        """
        query = ca.insert().values(
            id=str(uuid.uuid4()),
            full_name=obj_in.full_name,
            email=obj_in.email,
            phone_number=obj_in.phone_number,
            password=obj_in.password,
            is_active=True,
            role="CA",
        )
        await database.execute(query=query)
        return obj_in

    async def get_by_email(self, email: str):
        """
        Retrieve a CA record by email.

        Args:
            email (str): The email of the CA to retrieve.

        Returns:
            CA: The CA object matching the email, or None if not found.
        """
        query = ca.select().where(func.lower(ca.c.email) == func.lower(email))
        return await database.fetch_one(query=query)

    async def get_by_phone(self, phone: str):
        """
        Retrieve a CA record by phone number.

        Args:
            phone (str): The phone number of the CA to retrieve.

        Returns:
            CA: The CA object matching the phone number, or None if not found.
        """
        query = ca.select().where(phone == ca.c.phone_number)
        return await database.fetch_one(query=query)

    async def update(self, id: str, obj_in: Union[CAUpdate, Dict[str, Any]]):
        """
        Update a CA record.

        Args:
            id (str): The ID of the CA to update.
            obj_in (Union[CAUpdate, Dict[str, Any]]): The updated CA object.

        Returns:
            str: The ID of the updated CA.
        """
        query = (
            ca.update()
            .where(id == ca.c.id)
            .values(
                full_name=obj_in.full_name,
                email=obj_in.email,
                phone_number=obj_in.phone_number,
                password=obj_in.password,
            )
            .returning(ca.c.id)
        )
        return await database.execute(query=query)

    async def get_by_email_or_phone(self, request: str):
        """
        Retrieve a CA record by email or phone number.

        Args:
            request (str): The email or phone number of the CA to retrieve.

        Returns:
            CA: The CA object matching the email or phone number, or None if not found.
        """
        row = await self.get_by_email(email=request)
        if not row:
            row = await self.get_by_phone(phone=request)
        return row

    async def get_hashed_password_email_or_phone(self, request: str):
        """
        Retrieve the hashed password of a CA record by email or phone number.

        Args:
            request (str): The email or phone number of the CA to retrieve the password for.

        Returns:
            str: The hashed password of the CA.
        """
        query = ca.select().where(request == ca.c.phone_number)
        if not query:
            query = ca.select().where(request == ca.c.email)
        return await database.execute(query=query)

    async def authenticate(self, request: str, password: str):
        """
        Authenticate a CA by email or phone number and password.

        Args:
            request (str): The email or phone number of the CA to authenticate.
            password (str): The password to authenticate with.

        Returns:
            CA: The authenticated CA object, or None if authentication fails.
        """
        user = await self.get_by_email_or_phone(request)
        if user and await verify_password(password, user.password):
            return user
        return None

    async def is_active(self, user: ca):
        """
        Check if a CA is active.

        Args:
            user (ca): The CA object to check.

        Returns:
            bool: True if the CA is active, False otherwise.
        """
        return user.is_active

    async def ca_is_active(self, id: str, is_active: bool):
        """
        Set a CA's is_active status.

        Args:
            id (str): The ID of the CA to update.
            is_active (bool): The is_active status value.

        Returns:
            str: The ID of the updated CA.
        """
        query = (
            ca.update()
            .where(id == ca.c.id)
            .values(
                is_active=is_active,
            )
            .returning(ca.c.id)
        )
        return await database.execute(query=query)

    async def is_superuser(self, ca: ca):
        """
        Check if a CA is a superuser (admin).

        Args:
            ca (ca): The CA object to check.

        Returns:
            bool: True if the CA is a superuser, False otherwise.
        """
        user = await self.get_by_email(email=ca.email)
        if user.role == "Admin":
            return True
        return False

    async def is_CA(self, ca: ca):
        """
        Check if a CA is a regular CA.

        Args:
            ca (ca): The CA object to check.

        Returns:
            bool: True if the CA is a regular CA, False otherwise.
        """
        user = await self.get_by_email(email=ca.email)
        if user.role == "CA":
            return True
        return False

    async def create_profile_picture(self, obj_in: ProfilePictureCreate):
        """
        Create a profile picture for a CA.

        Args:
            obj_in (ProfilePictureCreate): The profile picture object to create.

        Returns:
            ProfilePictureCreate: The created profile picture object.
        """
        query = ca_profile.insert().values(
            id=str(uuid.uuid4()),
            filename=obj_in.filename,
            filetype=obj_in.filetype,
            filesize=obj_in.filesize,
            container=settings.PROFILEPICTURECONTAINER_NAME,
            filepath=f"{obj_in.ca_id}/{obj_in.filename}",
            ca_id=obj_in.ca_id,
        )
        await database.execute(query=query)
        return obj_in

    async def get_ca_profilePicture(self, ca_id: str):
        """
        Retrieve the profile picture of a CA.

        Args:
            ca_id (str): The ID of the CA.

        Returns:
            ProfilePicture: The profile picture object for the CA, or None if not found.
        """
        query = ca_profile.select().where(ca_id == ca_profile.c.ca_id)
        return await database.fetch_one(query=query)

    async def update_profile(self, id: str):
        """
        Update the profile of a CA.

        Args:
            id (str): The ID of the CA to update the profile for.

        Returns:
            str: The ID of the updated profile.
        """
        query = (
            ca_profile.update()
            .where(id == ca_profile.c.ca_id)
            .values(updated_on=sqlalchemy.func.now())
            .returning(ca_profile.c.id)
        )
        return await database.execute(query=query)

    async def remove_profile(self, id: str):
        """
        Remove the profile of a CA.

        Args:
            id (str): The ID of the CA to remove the profile for.

        Returns:
            str: The ID of the removed profile.
        """
        query = ca_profile.delete().where(id == ca_profile.c.ca_id)
        return await database.execute(query=query)

# Add these methods to your CARepository class

async def create_profile_picture_with_url(self, profile_data):
    """
    Create a profile picture for a CA with direct image URL.
    
    Args:
        profile_data (dict): Dictionary containing all profile picture data
        
    Returns:
        str: ID of the created profile picture
    """
    query = ca_profile.insert().values(
        id=profile_data.get("id", str(uuid.uuid4())),
        filename=profile_data["filename"],
        filetype=profile_data["filetype"],
        filesize=profile_data["filesize"],
        container=profile_data["container"],
        filepath=profile_data["filepath"],
        ca_id=profile_data["ca_id"],
        image_url=profile_data["image_url"]  # Store the direct URL
    )
    return await database.execute(query=query)

async def update_profile_picture(self, ca_id, profile_data):
    """
    Update an existing profile picture with new data
    
    Args:
        ca_id (str): ID of the CA
        profile_data (dict): New profile picture data
        
    Returns:
        str: ID of the updated profile
    """
    # First check if profile exists
    profile = await self.get_ca_profilePicture(ca_id)
    
    if profile:
        # Update existing profile
        query = (
            ca_profile.update()
            .where(ca_profile.c.ca_id == ca_id)
            .values(**profile_data)
            .returning(ca_profile.c.id)
        )
        return await database.execute(query=query)
    else:
        # Profile doesn't exist, create a new one with the ca_id
        profile_data["ca_id"] = ca_id
        profile_data["id"] = str(uuid.uuid4())
        return await self.create_profile_picture_with_url(profile_data)


ca_repository = CARepository()
