from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.api_key import APIKey


class APIKeyService:
    @staticmethod
    def get_api_keys(
        db: Session, skip: int = 0, limit: int = 100
    ) -> List[APIKey]:
        return db.query(APIKey).offset(skip).limit(limit).all()

    @staticmethod
    def get_api_key(db: Session, api_key_id: int) -> Optional[APIKey]:
        return db.query(APIKey).filter(APIKey.id == api_key_id).first()

    @staticmethod
    def get_api_key_by_key(db: Session, key: str) -> Optional[APIKey]:
        return db.query(APIKey).filter(APIKey.key == key).first()

    @staticmethod
    def create_api_key(db: Session, name: str) -> APIKey:
        api_key = APIKey(
            key=APIKey.generate_api_key(32),
            name=name,
            is_active=True,
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key

    @staticmethod
    def update_api_key(
        db: Session, api_key: APIKey, update_data: dict
    ) -> APIKey:
        for field, value in update_data.items():
            setattr(api_key, field, value)
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key

    @staticmethod
    def delete_api_key(db: Session, api_key: APIKey) -> None:
        db.delete(api_key)
        db.commit()

    @staticmethod
    def update_last_used(db: Session, api_key: APIKey) -> APIKey:
        api_key.mark_used()
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key
