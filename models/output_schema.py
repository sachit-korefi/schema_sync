from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from config.database import Base
import json

class OutputSchema(Base):
    __tablename__ = 'output_schemas'

    schema_uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schema_name = Column(String, nullable=True)
    user_uuid = Column(UUID(as_uuid=True))
    schema = Column(JSON, nullable=False)

    def to_dict(self):
        """Convert SQLAlchemy model to dict with UUID as string."""
        return {
            column.name: str(getattr(self, column.name)) if isinstance(getattr(self, column.name), uuid.UUID)
            else getattr(self, column.name)
            for column in self.__table__.columns
        }