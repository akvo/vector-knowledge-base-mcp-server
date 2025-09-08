from datetime import datetime
from sqlalchemy.orm import Session
from app.models.knowledge import KnowledgeBase


def test_created_at_auto_set(session: Session):
    obj = KnowledgeBase(name="test", description="A test knowledge base")
    session.add(obj)
    session.commit()
    session.refresh(obj)

    assert obj.created_at is not None
    assert isinstance(obj.created_at, datetime)
    assert obj.updated_at is not None


def test_updated_at_changes(session: Session):
    obj = KnowledgeBase(name="initial", description="test")
    session.add(obj)
    session.commit()
    session.refresh(obj)

    old_updated = obj.updated_at

    obj.name = "updated"
    session.commit()
    session.refresh(obj)

    assert (
        obj.updated_at > old_updated
    ), f"updated_at did not change: old={old_updated}, new={obj.updated_at}"
