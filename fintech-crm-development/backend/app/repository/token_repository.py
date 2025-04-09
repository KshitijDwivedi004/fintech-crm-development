from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, update
from app.db.session import database
from app.models.tokens import tokens

async def validate_token(token: str):
    """Fetch token details from the database."""
    query = select(tokens).where(tokens.c.token == token)
    
    db_token = await database.fetch_one(query)  # Fetch a single row
    if not db_token:
        raise HTTPException(status_code=400, detail="Token not found")
    if db_token['used']:
        raise HTTPException(status_code=400, detail="Token already used")
    
    expires_at = db_token['expires_at']
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    # Convert current time to UTC-aware
    current_time = datetime.utcnow().replace(tzinfo=timezone.utc)

    if expires_at < current_time:
        raise HTTPException(status_code=400, detail="Token expired")
    
async def marked_token_as_used(token: str):
    """Mark a token as used."""
    query = (
        tokens
        .update()
        .where(tokens.c.token == token)
        .values(used=True)
    )
    await database.execute(query)


async def insert_token(token: str, email: str, expires_at: datetime):
    """Insert a new account setup token into the database."""
    query = tokens.insert().values(
        token=token,
        user_email=email,
        used=False,
        expires_at=expires_at
    )
    await database.execute(query)
