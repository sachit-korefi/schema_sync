from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from config.database import Base
import json

class User(Base):
    __tablename__ = 'users'

    user_uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_email = Column(String, unique=True, nullable=False)
    user_password = Column(String, nullable=False)
    user_firstname = Column(String, nullable=False)
    user_lastname = Column(String, nullable=False)

    def to_dict(self):
        """Convert SQLAlchemy model to dict with UUID as string."""
        return {
            column.name: str(getattr(self, column.name)) if isinstance(getattr(self, column.name), uuid.UUID)
            else getattr(self, column.name)
            for column in self.__table__.columns
        }

    def to_json(self):
        """Convert SQLAlchemy model to JSON string."""
        return json.dumps(self.to_dict())