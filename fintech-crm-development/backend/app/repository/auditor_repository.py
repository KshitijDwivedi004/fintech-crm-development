from datetime import datetime, timedelta
import uuid
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException
import sqlalchemy

from app.core.config import settings
from app.db.session import database
from app.models.auditor import auditor, auditor_profile, auditor_task
from app.repository.telecaller_repository import TelecallerRepository
from app.schemas.auditor import (
    AuditorCreate,
    AuditorCreateId,
    AuditorTaskBase,
    AuditorTaskCreate,
    AuditorUpdate,
    ProfilePictureCreate,
)
from app.utils.cryptoUtil import verify_password
from app.models.failed_login_attempts import failed_login_attempts
from sqlalchemy import func


class AuditorRepository:
    """
    A repository class for handling CRUD operations related to auditors.

    This class provides methods for creating, retrieving, updating, and deleting auditor data
    from the underlying data source.

    Attributes:
        None
    """

    async def create(self, obj_in: AuditorCreateId):
        """
        Create a new auditor.

        Args:
            obj_in (AuditorCreateId): The data for creating a new auditor.

        Returns:
            AuditorCreateId: The created auditor object.
        """
        auditor_id = str(uuid.uuid4())
        query = auditor.insert().values(
            id=auditor_id,
            full_name=obj_in.full_name,
            email=obj_in.email,
            phone_number=obj_in.phone_number,
            password=obj_in.password,
            expertise=obj_in.expertise,
            is_active=False,
            role="Auditor",
            created_by=obj_in.created_by,
            experience=obj_in.experience,
            qualification=obj_in.qualification,
            task_read=obj_in.task_read,
            task_write=obj_in.task_create,
            task_create=obj_in.task_create,
            task_delete=obj_in.task_delete,
            task_import=obj_in.task_import,
            task_export=obj_in.task_export,
            chat_read=obj_in.chat_read,
            chat_write=obj_in.chat_write,
            chat_create=obj_in.chat_create,
            chat_delete=obj_in.chat_delete,
            chat_import=obj_in.chat_import,
            chat_export=obj_in.chat_export,
        )

        # First execute the query to insert the auditor record
        await database.execute(query=query)

        # Only after the auditor record exists, create the telecaller
        telecaller_repository = TelecallerRepository()
        await telecaller_repository.create_telecaller(auditor_id)

        return obj_in

    async def get_by_email(self, email: str):
        """
        Retrieve an auditor by email.

        Args:
            email (str): The email address of the auditor.

        Returns:
            Auditor: The retrieved auditor object.
        """
        query = auditor.select().where(func.lower(auditor.c.email) == func.lower(email))
        return await database.fetch_one(query=query)

    async def get_by_phone(self, phone: str):
        """
        Retrieve an auditor by phone number.

        Args:
            phone (str): The phone number of the auditor.

        Returns:
            Auditor: The retrieved auditor object.
        """
        query = auditor.select().where(phone == auditor.c.phone_number)
        return await database.fetch_one(query=query)

    async def update(self, id: str, obj_in: Union[AuditorUpdate, Dict[str, Any]]):
        """
        Update an auditor's information.

        Args:
            id (str): The ID of the auditor to update.
            obj_in (Union[AuditorUpdate, Dict[str, Any]]): The updated data for the auditor.

        Returns:
            str: The ID of the updated auditor.
        """
        query = (
            auditor.update()
            .where(id == auditor.c.id)
            .values(
                full_name=obj_in.full_name,
                email=obj_in.email,
                phone_number=obj_in.phone_number,
                password=obj_in.password,
                expertise=obj_in.expertise,
                is_active=obj_in.is_active,
                experience=obj_in.experience,
                qualification=obj_in.qualification,
                task_read=obj_in.task_read,
                task_write=obj_in.task_create,
                task_create=obj_in.task_create,
                task_delete=obj_in.task_delete,
                task_import=obj_in.task_import,
                task_export=obj_in.task_export,
                chat_read=obj_in.chat_read,
                chat_write=obj_in.chat_write,
                chat_create=obj_in.chat_create,
                chat_delete=obj_in.chat_delete,
                chat_import=obj_in.chat_import,
                chat_export=obj_in.chat_export,
            )
            .returning(auditor.c.id)
        )
        return await database.execute(query=query)

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
            auditor.update()
            .where(id == auditor.c.id)
            .values(
                is_active=is_active,
            )
            .returning(auditor.c.id)
        )
        return await database.execute(query=query)

    async def get_list_auditor(self, created_by: str, skip: int = 0, limit: int = 100):
        """
        Retrieve a list of auditors created by a CA.

        Args:
            created_by (str): The email of the CA who created the auditors.
            skip (int, optional): Number of records to skip. Defaults to 0.
            limit (int, optional): Maximum number of records to retrieve. Defaults to 100.

        Returns:
            List[auditor]: A list of auditor objects matching the criteria.
        """
        query = (
            auditor.select()
            .where(created_by == auditor.c.created_by, auditor.c.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return await database.fetch_all(query=query)

    async def get_by_email_or_phone(self, request: str):
        """
        Retrieve an auditor by email or phone number.

        Args:
            request (str): The email or phone number of the auditor.

        Returns:
            Auditor: The retrieved auditor object, or None if not found.
        """
        user = await self.get_by_email(email=request)
        if not user:
            user = await self.get_by_phone(phone=request)
        return user

    async def get_hashed_password_email_or_phone(self, request: str):
        """
        Get the hashed password for an auditor by email or phone number.

        Args:
            request (str): The email or phone number of the auditor.

        Returns:
            str: The hashed password, or None if not found.
        """
        query = auditor.select().where(request == auditor.c.phone_number)
        if not query:
            query = auditor.select().where(request == auditor.c.email)
        return await database.execute(query=query)

    async def get_failed_attempt_count(self, username: str):
        """
        Get the count of failed login attempts for a user within the last hour.

        Args:
            username (str): The username (email or phone) to check

        Returns:
            int: The count of failed attempts
        """
        time_threshold = datetime.utcnow() - timedelta(hours=1)

        query = sqlalchemy.select([sqlalchemy.func.count()]).where(
            (failed_login_attempts.c.username == username)
            & (failed_login_attempts.c.attempt_time > time_threshold)
        )

        return await database.fetch_val(query)

    async def authenticate(self, request: str, password: str):
        """
        Authenticate an auditor by email or phone number and password.

        Args:
            request (str): The email or phone number of the auditor.
            password (str): The password to authenticate.

        Returns:
            Auditor: The authenticated auditor object, or None if authentication fails.
        """
        user = await self.get_by_email_or_phone(request)
        if not user:
            return None  # User does not exist

        # Check failed attempts in last hour
        failed_attempts = await self.get_failed_attempt_count(request)

        if failed_attempts >= 3:
            raise HTTPException(
                status_code=403, detail="You've exceeded the maximum attempts. Please contact your administrator to reset your account."
            )

        # Verify password
        if not await verify_password(password, user.password):
            # Insert failed attempt
            insert_query = failed_login_attempts.insert().values(
                id=str(uuid.uuid4()),
                username=request,
                user_id=user["id"],
                attempt_time=datetime.utcnow(),
            )
            await database.execute(insert_query)

            remaining_attempts = 3 - (failed_attempts + 1)  # Calculate remaining attempts
            if remaining_attempts > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Wrong password. {remaining_attempts} attempt{'s' if remaining_attempts > 1 else ''} left or Click 'Forgot Password' to reset.",
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail="You've exceeded the maximum attempts. Please contact your administrator to reset your account."
                )

        # Successful login -> Reset failed attempts
        delete_query = failed_login_attempts.delete().where(
            failed_login_attempts.c.username == request
        )
        await database.execute(delete_query)

        return user

    async def is_active(self, user: auditor):
        """
        Check if an auditor is active.

        Args:
            user (Auditor): The auditor object to check.

        Returns:
            bool: True if the auditor is active, False otherwise.
        """
        return user.is_active

    async def create_profile_picture(self, obj_in: ProfilePictureCreate):
        """
        Create a profile picture for an auditor.

        Args:
            obj_in (ProfilePictureCreate): The data for creating a profile picture.

        Returns:
            ProfilePictureCreate: The created profile picture object.
        """
        query = auditor_profile.insert().values(
            id=str(uuid.uuid4()),
            filename=obj_in.filename,
            filetype=obj_in.filetype,
            filesize=obj_in.filesize,
            container=settings.PROFILEPICTURECONTAINER_NAME,
            filepath=f"{obj_in.auditor_id}/{obj_in.filename}",
            auditor_id=obj_in.auditor_id,
        )
        await database.execute(query=query)
        return obj_in

    async def get_auditor_profilePicture(self, auditor_id: str):
        """
        Get the profile picture of an auditor.

        Args:
            auditor_id (str): The ID of the auditor.

        Returns:
            ProfilePicture: The retrieved profile picture object.
        """
        query = auditor_profile.select().where(auditor_id == auditor_profile.c.auditor_id)
        return await database.fetch_one(query=query)

    async def update_profile(self, id: str):
        """
        Update an auditor's profile.

        Args:
            id (str): The ID of the auditor.

        Returns:
            str: The ID of the updated auditor profile.
        """
        # Check if profile exists first
        profile = await self.get_auditor_profilePicture(id)

        if profile:
            # Update existing profile
            query = (
                auditor_profile.update()
                .where(auditor_profile.c.auditor_id == id)
                .values(updated_on=sqlalchemy.func.now())
                .returning(auditor_profile.c.id)
            )
            return await database.execute(query=query)
        else:
            # Profile doesn't exist, create a new one
            profile_data = ProfilePictureCreate(
                filename="profilePicture", filetype="image", filesize=0, auditor_id=id
            )
            return await self.create_profile_picture(profile_data)

    async def remove_profile(self, id: str):
        """
        Remove an auditor's profile.

        Args:
            id (str): The ID of the auditor.

        Returns:
            str: The ID of the removed auditor profile.
        """
        query = auditor_profile.delete().where(id == auditor_profile.c.id)
        return await database.execute(query=query)

    async def create_task(self, obj_in: AuditorTaskCreate):
        """
        Create a task for an auditor.

        Args:
            obj_in (AuditorTaskCreate): The data for creating a task.

        Returns:
            AuditorTaskCreate: The created task object.
        """
        query = auditor_task.insert().values(
            id=str(uuid.uuid4()),
            task_type=obj_in.task_type,
            priority=obj_in.priority,
            task_name_1=obj_in.task_name_1,
            task_name_2=obj_in.task_name_2,
            task_name_3=obj_in.task_name_3,
            created_by=obj_in.created_by,
            created_for=obj_in.created_for,
            status=obj_in.status,
            is_active=True,
        )
        await database.execute(query=query)
        return obj_in

    async def update_task(self, id: str, obj_in: Union[AuditorTaskBase, Dict[str, Any]]):
        """
        Update an auditor's task.

        Args:
            id (str): The ID of the task to update.
            obj_in (Union[AuditorTaskBase, Dict[str, Any]]): The updated data for the task.

        Returns:
            str: The ID of the updated task.
        """
        query = (
            auditor_task.update()
            .where(id == auditor_task.c.id)
            .values(
                task_type=obj_in.task_type,
                priority=obj_in.priority,
                task_name_1=obj_in.task_name_1,
                task_name_2=obj_in.task_name_2,
                task_name_3=obj_in.task_name_3,
                status=obj_in.status,
                updated_on=sqlalchemy.func.now(),
            )
            .returning(auditor_task.c.id)
        )
        return await database.execute(query=query)

    async def task_is_active(self, id: str):
        """
        Set an auditor's task as inactive.

        Args:
            id (str): The ID of the task to update.

        Returns:
            str: The ID of the updated task.
        """
        query = (
            auditor_task.update()
            .where(id == auditor_task.c.id)
            .values(
                is_active=False,
                updated_on=sqlalchemy.func.now(),
            )
            .returning(auditor_task.c.id)
        )
        return await database.execute(query=query)

    async def get_list_auditor_task(self, created_for: str, skip: int = 0, limit: int = 100):
        """
        Retrieve a list of auditor tasks.

        Args:
            created_for (str): The ID of the auditor for whom the tasks are created.
            skip (int): The number of tasks to skip from the beginning (default: 0).
            limit (int): The maximum number of tasks to retrieve (default: 100).

        Returns:
            List[Dict]: A list of auditor tasks matching the criteria.
        """
        query = (
            auditor_task.select()
            .where(created_for == auditor_task.c.created_for, auditor_task.c.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return await database.fetch_all(query=query)

    async def activate_account(self, id: str, password: str):
        """
        Activate an auditor's account by updating the password and setting is_active to True.

        Args:
            id (str): The ID of the auditor.
            password (str): The new password to update.

        Returns:
            bool: True if activation is successful, False otherwise.
        """
        query = (
            auditor.update()
            .where(auditor.c.id == id)
            .values(password=password, is_active=True)
            .returning(auditor.c.id)
        )
        updated_id = await database.execute(query=query)
        return bool(updated_id)

    async def update_password(self, id: str, new_password: str):
        """
        Update an auditor's password.

        Args:
            id (str): The ID of the auditor.
            new_password (str): The new password (hashed).

        Returns:
            bool: True if update was successful, False otherwise.
        """
        query = (
            auditor.update()
            .where(auditor.c.id == id)
            .values(password=new_password)
            .returning(auditor.c.id)
        )
        updated_id = await database.execute(query=query)
        return bool(updated_id)

    async def create_profile_picture_with_url(self, profile_data):
        """
        Create a profile picture for an auditor with direct image URL.

        Args:
            profile_data (dict): Dictionary containing all profile picture data

        Returns:
            str: ID of the created profile picture
        """
        query = auditor_profile.insert().values(
            id=profile_data.get("id", str(uuid.uuid4())),
            filename=profile_data["filename"],
            filetype=profile_data["filetype"],
            filesize=profile_data["filesize"],
            container=profile_data["container"],
            filepath=profile_data["filepath"],
            auditor_id=profile_data["auditor_id"],
            image_url=profile_data["image_url"],  # Store the direct URL
        )
        return await database.execute(query=query)

    async def update_profile_picture(self, auditor_id, profile_data):
        """
        Update an existing profile picture with new data

        Args:
            auditor_id (str): ID of the auditor
            profile_data (dict): New profile picture data

        Returns:
            str: ID of the updated profile
        """
        # First check if profile exists
        profile = await self.get_auditor_profilePicture(auditor_id)

        if profile:
            # Update existing profile
            query = (
                auditor_profile.update()
                .where(auditor_profile.c.auditor_id == auditor_id)
                .values(**profile_data)
                .returning(auditor_profile.c.id)
            )
            return await database.execute(query=query)
        else:
            # Profile doesn't exist, create a new one with the auditor_id
            profile_data["auditor_id"] = auditor_id
            profile_data["id"] = str(uuid.uuid4())
            return await self.create_profile_picture_with_url(profile_data)


auditor_repository = AuditorRepository()
