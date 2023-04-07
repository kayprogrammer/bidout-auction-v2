from datetime import datetime
from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseManager(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get_all(self, db: Session) -> Optional[List[ModelType]]:
        return db.query(self.model).all()

    def get_by_id(self, db: Session, id: UUID) -> Optional[ModelType]:
        return db.query(self.model).filter_by(id=id).first()

    def get_by_slug(self, db: Session, slug: str) -> Optional[ModelType]:
        return db.query(self.model).filter_by(slug=slug).first()

    def create(self, db: Session, obj_in: Optional[ModelType]) -> Optional[ModelType]:
        if not obj_in:
            return None
        obj_in["created_at"] = datetime.utcnow()
        obj_in["updated_at"] = obj_in["created_at"]
        obj = self.model(**obj_in)

        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(
        self, db: Session, db_obj: Optional[ModelType], obj_in: Optional[ModelType]
    ) -> Optional[ModelType]:
        if not db_obj:
            return None
        for attr, value in obj_in.items():
            setattr(db_obj, attr, value)
        db_obj.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: Optional[ModelType]):
        if db_obj:
            db.delete(db_obj)
            db.commit()

    def delete_by_id(self, db: Session, id: UUID):
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
