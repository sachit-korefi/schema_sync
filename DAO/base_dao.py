from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from typing import Type, Any, Dict, List
from sqlalchemy import distinct, Column


class BaseDAO:
    def __init__(self, db: Session):
        self.db = db

    def insert(self, model: Type[Any], data: Dict) -> Any:
        record = model(**data)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def bulk_insert_records(self, model: Type[Any], data: List[Dict]):
        records = [model(**item) for item in data]
        self.db.add_all(records)
        self.db.commit()
        return records

    def bulk_upsert_records(self, model: Type[Any], data: List[Dict], conflict_cols: List[str], update_cols: List[str]):
        stmt = pg_insert(model).values(data)
        update_dict = {col: getattr(stmt.excluded, col) for col in update_cols}
        stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=update_dict)
        self.db.execute(stmt)
        self.db.commit()

    def get_all(self, model: Type[Any], filters: Dict) -> List[Any]:
        return self.db.query(model).filter_by(**filters).all()

    def get_one(self, model: Type[Any], filters: Dict) -> Any:
        return self.db.query(model).filter_by(**filters).first()

    def update(self, model: Type[Any], filters: Dict, update_data: Dict) -> int:
        result = self.db.query(model).filter_by(**filters).update(update_data)
        self.db.commit()
        return result

    def delete(self, model: Type[Any], filters: Dict) -> int:
        result = self.db.query(model).filter_by(**filters).delete()
        self.db.commit()
        return result

    def get_distinct(self, column: Column, filters: Dict = None) -> List[Any]:
        query = self.db.query(distinct(column))
        if filters:
            query = query.filter_by(**filters)
        return query.all()
