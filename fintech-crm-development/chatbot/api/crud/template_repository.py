from datetime import datetime
from api.db_utils import database, templates
from api.schemas.template_schema import TemplateBase
from fastapi import HTTPException

class TemplateRepository:
    def __init__(self, database):
        self.database = database

    async def create_template(self, template_in: TemplateBase):
        query = templates.insert().values(
            name=template_in.name,
            wa_name=template_in.wa_name,
            category=template_in.category,
            created_at=datetime.utcnow()
        )
        try:
            template_id = await self.database.execute(query=query)
            return await self.get_template_by_id(template_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def get_all_templates(self):
        query = templates.select().order_by(templates.c.created_at.desc())
        return await self.database.fetch_all(query=query)

    async def update_template_status(self, template_id: int, new_status: str):
        query = (
            templates.update()
            .where(templates.c.id == template_id)
            .values(status=new_status)
        )
        try:
            await self.database.execute(query=query)
            return await self.get_template_by_id(template_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    async def get_template_by_id(self, template_id: int):
        query = templates.select().where(templates.c.id == template_id)
        result = await self.database.fetch_one(query=query)
        if not result:
            raise HTTPException(status_code=404, detail="Template not found")
        return result

    async def get_template_by_wa_name(self, wa_name: str):
        """Fetch a template by wa_name."""
        query = templates.select().where(templates.c.wa_name == wa_name)
        result = await self.database.fetch_one(query=query)
        if not result:
            raise HTTPException(status_code=404, detail="Template not found")
        return result


    async def update_template_status_and_structure(self, wa_name: str, status: str, structure: dict):
        """Update a template's status and structure based on wa_name."""
        query = (
            templates.update()
            .where(templates.c.wa_name == wa_name)
            .values(status=status, structure=structure)
        )
        try:
            await self.database.execute(query=query)
            return await self.get_template_by_wa_name(wa_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
template_repository = TemplateRepository(database)