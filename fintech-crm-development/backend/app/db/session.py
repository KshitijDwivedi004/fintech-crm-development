import databases
import sqlalchemy
from sqlalchemy import create_engine, MetaData

from app.core.config import settings

# Convert the URI format for the databases library
# databases expects postgresql:// not postgresql+psycopg2://
DATABASE_URI = str(settings.DATABASE_URI).replace("postgresql+psycopg2://", "postgresql://")

# Use the converted URI for the databases library
database = databases.Database(DATABASE_URI)

# Define metadata only once
metadata = MetaData()

# Use the original URI with the driver for SQLAlchemy
engine = create_engine(settings.DATABASE_URI)


async def get_database():
    if not database.is_connected:
        await database.connect()
    yield database
