import datetime
import uuid

from sqlalchemy import func, select

from app.core.config import settings
from app.db.session import database
from app.models.user import documents, documents_type
from app.schemas.document import DocumentCreate, DocumentUpdate


class DocumentRepository:
    """
    Repository class for managing documents in the system.

    This class provides methods to create, retrieve, and update documents in the system.
    """

    async def create(self, obj_in: DocumentCreate):
        """
        Create a new document in the system.

        Args:
            obj_in (DocumentCreate): The document data to create.

        Returns:
            DocumentCreate: The created document object.
        """
        query = documents.insert().values(
            document_type=obj_in.document_type,
            document_size=obj_in.document_size,
            container=settings.CONTAINER_NAME,
            document_path=obj_in.document_path,
            user_id=obj_in.user_id,
            document_type_id=obj_in.document_type_id,
            status=obj_in.status,
            is_active=True,
            document_name=obj_in.document_name,
        )
        return await database.execute(query=query)

    async def update_document(self, document_type: str, document_size: int, document_type_id: int):
        """
        Update a document in the system.

        Args:
            document_type (str): The type of document.
            document_size (int): The size of the document.
            document_type_id (int): The ID of the document type.

        Returns:
            int: The ID of the updated document.
        """
        query = (
            documents.update()
            .where(document_type_id == documents.c.document_type_id)
            .values(
                document_type=document_type,
                document_size=document_size,
                updated_on=datetime.datetime.now(),
            )
        )
        return await database.execute(query=query)

    async def update_document_path(self, document_path: str, document_id: str):
        """
        Update a document path in the system.

        Args:
            document_path (str): The document path to update.
            document_id (str): The ID of the document.

        Returns:
            int: The ID of the updated document.
        """
        query = (
            documents.update()
            .where(document_id == documents.c.id)
            .values(
                document_path=document_path,
            )
        )
        return await database.execute(query=query)

    async def update_document_status(self, status: bool, document_id: str):
        """
        Update a document's active status in the system.

        Args:
            status (bool): The active status to set.
            document_id (str): The ID of the document.

        Returns:
            int: The ID of the updated document.
        """
        query = (
            documents.update()
            .where(document_id == documents.c.id)
            .values(
                is_active=status,
            )
        )
        return await database.execute(query=query)

    async def update_document_with_id(
        self, document_type: str, document_size: int, document_id: int, document_name: str = None
    ):
        """
        Update a document in the system using its ID.

        Args:
            document_type (str): The type of document.
            document_size (int): The size of the document.
            document_id (int): The ID of the document.
            document_name (str, optional): The new name for the document

        Returns:
            int: The ID of the updated document.
        """

        update_values = {
            "document_type": document_type,
            "document_size": document_size,
            "updated_on": datetime.datetime.now(),
        }

        if document_name is not None:
            update_values["document_name"] = document_name

        query = documents.update().where(document_id == documents.c.id).values(**update_values)
        return await database.execute(query=query)

    async def get_user_documents(self, user_id: str):
        """
        Retrieve documents associated with a user.

        Args:
            user_id (str): The ID of the user.

        Returns:
            List[Document]: A list of retrieved document objects.
        """
        query = (
            documents.select()
            .where(
                user_id == documents.c.user_id,
                documents.c.is_active == True,
            )
            .order_by(documents.c.updated_on.desc())
        )
        return await database.fetch_all(query=query)

    async def file_extension(self, document_path: str):
        """
        Retrieve document type based on document path.

        Args:
            document_path (str): The path of the document.

        Returns:
            str: The document type.
        """
        query = (
            documents.select()
            .where(document_path == documents.c.document_path, documents.c.is_active == True)
            .with_only_columns([documents.c.document_type])
        )
        return await database.fetch_val(query=query)

    async def get_user_documents_count(self, user_id: str):
        """
        Retrieve count of documents associated with a user.

        Args:
            user_id (str): The user ID.

        Returns:
            int: Count of retrieved document objects.
        """
        query = (
            select([func.count()])
            .where(documents.c.user_id == user_id, documents.c.is_active == True)
            .select_from(documents)
        )
        return await database.fetch_val(query=query)

    async def get_documents_type(self, document_type_id: int):
        """
        Retrieve document type using document type id.

        Args:
            document_type_id (int): The document type id.

        Returns:
            dict: The retrieved document type object.
            eg: {'id': 1, 'document_name': 'National ID'}
        """
        query = documents_type.select().where(document_type_id == documents_type.c.id)
        return await database.fetch_one(query=query)

    async def get_documents_type_count(self):
        """
        Retrieve count of document types.

        Returns:
            int: Count of document types.
        """
        query = select([func.count()]).select_from(documents_type)
        return await database.fetch_val(query=query)

    async def get_documents_using_id(self, user_id: str, document_type_id: int):
        """
        Retrieve documents associated with a user using document type id.

        Args:
            user_id (str): The ID of the user.
            document_type_id (int): The document type id.

        Returns:
            dict: The retrieved document object.
        """
        query = documents.select().where(
            document_type_id == documents.c.document_type_id, user_id == documents.c.user_id
        )
        return await database.fetch_one(query=query)

    async def update(self, id: str, status: str):
        """
        Update the status of a document.

        Args:
            id (str): The ID of the document to update.
            status (str): The updated status of the document.

        Returns:
            str: The ID of the updated document.
        """
        query = (
            documents.update()
            .where(id == documents.c.id)
            .values(status=status)
            .returning(documents.c.id)
        )
        return await database.execute(query=query)

    async def get_recent_documents(self, days: int):
        """
        Retrieve documents that were created within the last n days.

        Args:
            days (int): Number of days to look back.

        Returns:
            List[Document]: A list of recent document objects.
        """
        # Calculate the date threshold
        threshold_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        query = documents.select().where(documents.c.created_on >= threshold_date)
        return await database.fetch_all(query=query)

    async def get_document_type_list(self):
        """
        Retrieve all document types.

        Returns:
            List[dict]: A list of all document types.
        """
        query = documents_type.select()
        return await database.fetch_all(query=query)

    async def get_document_type_by_id(self, document_type_id: int):
        """
        Retrieve a document type from the database based on the provided ID.

        Args:
            document_type_id (int): The ID of the document type to retrieve.

        Returns:
            dict: The document type data or None if not found.
        """
        query = documents_type.select().where(documents_type.c.id == document_type_id)
        result = await database.fetch_one(query)
        if result:
            document_type_data = dict(result)
            return document_type_data
        return None

    async def get_document_by_id(self, document_id: int):
        """
        Retrieve a document by its ID.

        Args:
            document_id (int): The ID of the document to retrieve.

        Returns:
            dict: The retrieved document object, or None if not found.
        """
        query = documents.select().where(
            documents.c.id == document_id, documents.c.is_active == True
        )
        return await database.fetch_one(query=query)

    async def update_document_name(self, document_id: int, document_name: str):
        """
        Update a document's name in the system.

        Args:
            document_id (int): The ID of the document to update.
            document_name (str): The new name for the document.

        Returns:
            int: The ID of the updated document.
        """
        query = (
            documents.update()
            .where(document_id == documents.c.id)
            .values(
                document_name=document_name,
                updated_on=datetime.datetime.now(),
            )
        )
        return await database.execute(query=query)

    async def update_document_metadata(
        self, document_id: int, document_type: str, document_size: int
    ):
        """
        Update a document's metadata (type and size) in the system.

        Args:
            document_id (int): The ID of the document to update.
            document_type (str): The file type of the document.
            document_size (int): The size of the document in bytes.

        Returns:
            int: The ID of the updated document.
        """
        query = (
            documents.update()
            .where(document_id == documents.c.id)
            .values(
                document_type=document_type,
                document_size=document_size,
                updated_on=datetime.datetime.now(),
            )
        )
        return await database.execute(query=query)


document_repository = DocumentRepository()
