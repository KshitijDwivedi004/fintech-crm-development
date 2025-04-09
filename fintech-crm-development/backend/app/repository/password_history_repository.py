from sqlalchemy import select, func
from sqlalchemy import insert, update, delete
import sqlalchemy
from app.models.password_history import password_history
from app.models.notes import notes
import uuid
from typing import Dict, Any, List
from app.db.session import database
from app.utils.cryptoUtil import verify_password,get_password_hash

class PasswordHistoryRepository:
    @staticmethod
    async def get_password_history(user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get recent password history for a user"""
        query = (
            select(
                password_history.c.id,
                password_history.c.user_id,
                password_history.c.password_hash,
                password_history.c.created_at
            )
            .where(password_history.c.user_id == user_id)
            .order_by(password_history.c.created_at.desc())
            .limit(limit)
        )
        
        results = await database.fetch_all(query)
        return [dict(row) for row in results]
    
    @staticmethod
    async def add_password_to_history(user_id: str, password_hash: str) -> Dict[str, Any]:
        """Add a password to the user's history"""
        history_id = str(uuid.uuid4())
        query = (
            insert(password_history)
            .values(
                id=history_id,
                user_id=user_id,
                password_hash=password_hash,
                created_at=func.now()
            )
            .returning(
                password_history.c.id,
                password_history.c.user_id,
                password_history.c.password_hash,
                password_history.c.created_at
            )
        )
        
        result = await database.fetch_one(query)
        return dict(result) if result else None
    
    @staticmethod
    async def trim_password_history(user_id: str, max_entries: int = 5) -> bool:
        """Keep only the most recent passwords in history"""
        # Get all entries for this user
        query = (
            select(
                password_history.c.id
            )
            .where(password_history.c.user_id == user_id)
            .order_by(password_history.c.created_at.desc())
        )
        
        all_entries = await database.fetch_all(query)
        
        # If we don't have more than max_entries, nothing to trim
        if len(all_entries) <= max_entries:
            return False
        
        # Get IDs to keep (the most recent max_entries)
        keep_ids = [entry['id'] for entry in all_entries[:max_entries]]
        
        # Delete older entries
        delete_query = (
            delete(password_history)
            .where(
                password_history.c.user_id == user_id, 
                password_history.c.id.not_in(keep_ids)
            )
        )
        
        await database.execute(delete_query)
        return True
    
    @staticmethod
    async def check_password_history(user_id: str, new_password: str, limit: int = 3) -> bool:
        """
        Check if a password is in the recent history
        Returns True if password is ok (not in history)
        Returns False if password is in recent history
        """
        # Get recent password history
        history = await PasswordHistoryRepository.get_password_history(user_id, limit)
        
        # Check if new password matches any in history
        for entry in history:
            if await verify_password(new_password, entry['password_hash']):
                return False
                
        # Also check current password (may be outside of repository scope
        # depending on your architecture)
        
        return True
password_history_repository = PasswordHistoryRepository()