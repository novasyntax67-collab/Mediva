from typing import Generic, Type, TypeVar, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
import uuid

# Define TypeVar bound to any SQLAlchemy model class
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any) -> Optional[ModelType]:
        query = select(self.model).filter(
            self.model.id == id,
            self.model.deleted_at == None
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        query = select(self.model).filter(
            self.model.deleted_at == None
        ).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, *, obj_in: CreateSchemaType, actor_id: Optional[uuid.UUID] = None) -> ModelType:
        obj_in_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in
        
        # Instantiate model object
        db_obj = self.model(**obj_in_data)
        
        # Populate auditing metadata if present
        if hasattr(db_obj, "created_by") and actor_id:
            db_obj.created_by = actor_id
        if hasattr(db_obj, "updated_by") and actor_id:
            db_obj.updated_by = actor_id

        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def update(
        self, *, db_obj: ModelType, obj_in: UpdateSchemaType, actor_id: Optional[uuid.UUID] = None
    ) -> ModelType:
        obj_data = db_obj.__dict__
        update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        # Populate updating metadata & increment locking version
        if hasattr(db_obj, "updated_by") and actor_id:
            db_obj.updated_by = actor_id
        if hasattr(db_obj, "lock_version"):
            db_obj.lock_version = (db_obj.lock_version or 1) + 1

        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def remove(self, *, id: Any, actor_id: Optional[uuid.UUID] = None) -> Optional[ModelType]:
        db_obj = await self.get(id)
        if db_obj:
            # Perform soft delete
            if hasattr(db_obj, "deleted_at"):
                db_obj.deleted_at = datetime.utcnow()
                if hasattr(db_obj, "updated_by") and actor_id:
                    db_obj.updated_by = actor_id
                self.db.add(db_obj)
            else:
                await self.db.delete(db_obj)
            await self.db.flush()
        return db_obj
