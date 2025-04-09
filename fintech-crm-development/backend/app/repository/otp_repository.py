import uuid
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy import func, text

from app.db.session import database
from app.models.otp import otp_blocks, otps
from app.schemas.otp import CreateOTP, InfoOTP, VerifyOTP
from app.models.password_reset import otp_table


class OTPRepository:
    """
    Repository class for managing OTP (One-Time Password) operations.

    This class provides methods to create and manage OTPs, including verifying OTP codes,
    handling OTP failure counts, blocking OTPs, and disabling/removing OTPs.
    """

    async def create(self, obj_in: VerifyOTP):
        """
        Create a new OTP entry.

        Args:
            obj_in (VerifyOTP): The VerifyOTP object containing the OTP details.

        Returns:
            VerifyOTP: The created VerifyOTP object.
        """
        query = otps.insert().values(
            phone_number=obj_in.phone_number,
            otp_code=obj_in.otp_code,
            status=True,
            otp_failed_count=0,
        )
        await database.execute(query=query)
        return obj_in

    async def find_otp_block(self, phone: str):
        """
        Find a blocked OTP for the given phone number.

        Args:
            phone (str): The phone number for which to find the blocked OTP.

        Returns:
            Optional[Record]: The blocked OTP record if found, else None.
        """
        query = otp_blocks.select().where(
            otp_blocks.c.phone_number == phone,
            func.now() - text("interval '10 minutes'") <= otp_blocks.c.created_on,
        )
        return await database.fetch_one(query=query)

    async def find_otp_life_time(self, phone: str):
        """
        Find an active OTP within its lifetime for the given phone number.

        Args:
            phone (str): The phone number for which to find the active OTP.

        Returns:
            Optional[Record]: The active OTP record if found, else None.
        """
        query = otps.select().where(
            otps.c.phone_number == phone,
            func.now() - text("interval '10 minutes'") <= otps.c.created_on,
        )
        return await database.fetch_one(query=query)

    async def save_otp_failed_count(self, obj_in: VerifyOTP):
        """
        Save the incremented OTP failed count for the given OTP.

        Args:
            obj_in (VerifyOTP): The VerifyOTP object containing the OTP details.

        Returns:
            None
        """
        query = (
            otps.update()
            .where(otps.c.phone_number == obj_in.phone_number, obj_in.otp_code == otps.c.otp_code)
            .values(
                otp_failed_count=otps.c.otp_failed_count + 1,
            )
        )
        return await database.execute(query=query)

    async def save_block_otp(self, phone: str):
        """
        Save a blocked OTP for the given phone number.

        Args:
            phone (str): The phone number for which to block the OTP.

        Returns:
            None
        """
        query = otp_blocks.insert().values(
            phone_number=phone,
        )
        await database.execute(query=query)

    async def disable_otp(self, obj_in: VerifyOTP):
        """
        Disable the given OTP by setting its status to False.

        Args:
            obj_in (VerifyOTP): The VerifyOTP object containing the OTP details.

        Returns:
            None
        """
        query = (
            otps.update()
            .where(otps.c.phone_number == obj_in.phone_number, obj_in.otp_code == otps.c.otp_code)
            .values(
                status=False,
            )
        )
        return await database.execute(query=query)

    async def remove_otp(self, obj_in: VerifyOTP):
        """
        Remove the given OTP entry.

        Args:
            obj_in (VerifyOTP): The VerifyOTP object containing the OTP details.

        Returns:
            None
        """
        query = otps.delete().where(
            otps.c.phone_number == obj_in.phone_number, obj_in.otp_code == otps.c.otp_code
        )
        return await database.execute(query=query)
    
    async def store_otp(self, email: str, otp: str):
        expires_at = datetime.utcnow() + timedelta(minutes=10)  
        query = otp_table.insert().values(
            id=str(uuid.uuid4()),
            email=email,
            otp=otp,
            expires_at=expires_at
        )
        await database.execute(query=query)

    async def verify_otp(self, email: str, otp: str):
        query = otp_table.select().where(
            otp_table.c.email == email,
            otp_table.c.otp == otp,
            otp_table.c.is_used == False,
            otp_table.c.expires_at > datetime.utcnow()
        )
        result = await database.fetch_one(query=query)
        if result:
            # Mark OTP as used
            update_query = (
                otp_table.update()
                .where(otp_table.c.id == result.id)
                .values(is_used=True)
            )
            await database.execute(update_query)
            return True
        return False



otp_repository = OTPRepository()
