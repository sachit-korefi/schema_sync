from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Union
from models.output_schema import OutputSchema
from DAO.base_dao import BaseDAO


class OutputSchemaDAO(BaseDAO):
    def __init__(self, db: Session):
        super().__init__(db)

    def create_output_schema(self, user_uuid: str, schema_details: Dict[str, Any]) -> OutputSchema:
        output_schema = {
            "user_uuid": user_uuid,
            "schema_name": schema_details["schema_name"],
            "schema": schema_details["schema"],
        }
        return self.insert(OutputSchema, output_schema)

    def get_output_schemas_by_user_uuid(self, user_uuid: str) -> List[OutputSchema]:
        json_schemas = []
        schemas = self.get_all(OutputSchema, {"user_uuid": user_uuid})
        for schema in schemas:
            json_schemas.append(schema.to_dict())
        return json_schemas

    def get_output_schema_by_schema_uuid(self, schema_uuid: str) -> Optional[OutputSchema]:
        return self.get_one(OutputSchema, {"schema_uuid": schema_uuid})

    def update_output_schema_by_schema_uuid(self, schema_uuid: str, schema_details: Dict[str, Any]) -> Optional[OutputSchema]:
        return self.update(OutputSchema, filters={"schema_uuid": schema_uuid}, update_data=schema_details)


    def delete_schema_by_schema_uuid(self, schema_uuid: str) -> Optional[OutputSchema]:
        return self.delete(OutputSchema, filters={"schema_uuid": schema_uuid})
