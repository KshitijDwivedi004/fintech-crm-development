from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def verify_password(plain_password, hashed_password):
    """
    Verify password with the given hash
    """
    return pwd_context.verify(plain_password, hashed_password)


async def get_password_hash(password):
    """
    Get password hash for the given password
    """
    return pwd_context.hash(password)
