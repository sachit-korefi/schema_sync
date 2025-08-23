from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from models.user import User
from DAO.base_dao import BaseDAO
import uuid

class UserDAO(BaseDAO):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_all_users(self) -> List[User]:
        return self.get_all(User, {})  # Empty filters to get all users

    def create_user(self, user_data: Dict[str, Any]) -> User:
        return self.insert(User, user_data)

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.get_one(User, {"user_email": email})

    def get_user_by_uuid(self, user_uuid: uuid.UUID) -> Optional[User]:
        return self.get_one(User, {"user_uuid": user_uuid})

    def update_user_by_uuid(self, user_uuid: uuid.UUID, update_data: Dict[str, Any]) -> int:
        return self.update(User, {"user_uuid": user_uuid}, update_data)
