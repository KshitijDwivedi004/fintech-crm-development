from typing import Any, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.db.session import database

CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)


class BaseRepository:
    """
    A repository class for handling CRUD operations related to input model entities.

    This class provides methods for creating, retrieving, updating, and deleting user data
    from the underlying data source.

    """

    async def get(self, model, id: Any):
        query = model.select().where(id == model.c.id)
        return await database.fetch_one(query=query)

    async def get_as_active(self, model, id: Any):
        query = model.select().where(id == model.c.id, model.c.is_active == True)
        return await database.fetch_one(query=query)

    async def get_multi(self, model, skip: int = 0, limit: int = 100):
        query = model.select().offset(skip).limit(limit)
        return await database.fetch_all(query=query)

    async def create(self, model, obj_in: CreateSchemaType):
        obj_in_data = jsonable_encoder(obj_in)
        query = model.insert().values(**obj_in_data)
        await database.execute(query=query)
        return obj_in

    async def remove(self, model, id: str):
        query = model.delete().where(id == model.c.id)
        return await database.execute(query=query)


base_repository = BaseRepository()
