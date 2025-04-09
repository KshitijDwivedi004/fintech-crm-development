import json
import random

from fastapi import HTTPException

from app.core.helper import send_OTP
from app.core.logger import logger
from app.repository.otp_repository import otp_repository
from app.schemas.otp import CreateOTP, VerifyOTP


async def send_otp(request: CreateOTP):
    # Check block OTP
    opt_blocks = await otp_repository.find_otp_block(request.phone_number)
    if opt_blocks:
        raise HTTPException(
            status_code=404, detail="Sorry, this phone number is blocked for 10 minutes"
        )

    # Generate and save to table OTPs
    otp_code = random.randint(1000, 9999)
    payload = VerifyOTP(phone_number=request.phone_number, otp_code=otp_code)
    await otp_repository.create(payload)

    # Send OTP to User
    res = send_OTP(request.phone_number, otp_code)
    res.decode("utf-8")
    res = json.loads(res)
    if res["status"] != "success":
        logger.error(res["message"])
        raise HTTPException(status_code=404, detail="OTP code not sent")


async def verify_otp(request: VerifyOTP):
    # Check block OTP
    opt_blocks = await otp_repository.find_otp_block(request.phone_number)
    if opt_blocks:
        raise HTTPException(
            status_code=404,
            detail="Sorry, this phone number is blocked for 10 minutes",
        )

    # Check OTP code 4 digit life time
    otp_result = await otp_repository.find_otp_life_time(request.phone_number)
    if not otp_result:
        raise HTTPException(
            status_code=404, detail="OTP code has expired, please request a new one."
        )

    payload = VerifyOTP(**otp_result)

    # Check OTP code, if not verified,
    if otp_result.otp_code != request.otp_code:
        # Increment OTP failed count

        await otp_repository.save_otp_failed_count(payload)

        # If OTP failed count = 3
        # then block otp
        if otp_result.otp_failed_count + 1 == 3:
            await otp_repository.save_block_otp(otp_result.phone_number)
            raise HTTPException(
                status_code=404,
                detail="This phone number is blocked for 10 minutes",
            )

        # Throw exceptions
        raise HTTPException(status_code=404, detail="Incorrect OTP")

    # Disable otp code when succeed verified
    await otp_repository.remove_otp(payload)
