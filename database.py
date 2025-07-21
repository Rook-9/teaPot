from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# DATABASE_URL должен быть задан в переменных окружения или .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")  # или "sqlite:///:memory:"


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TeaEntry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    tea_name = Column(String(100))
    description = Column(String)
    how_to_brew = Column(String)
    rating = Column(Float)
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def save_entry(user_id, tea_name=None, description=None, how_to_brew=None, rating=None, price=None):
    session = SessionLocal()
    entry = TeaEntry(
        user_id=user_id,
        tea_name=tea_name,
        description=description,
        how_to_brew=how_to_brew,
        rating=rating,
        price=price
    )
    session.add(entry)
    session.commit()
    session.close()

def get_entries(user_id):
    session = SessionLocal()
    entries = session.query(TeaEntry).filter_by(user_id=user_id).order_by(desc(TeaEntry.created_at)).all()
    session.close()
    return entries

def search_by_name(user_id, name_part):
    session = SessionLocal()
    results = session.query(TeaEntry).filter(
        TeaEntry.user_id == user_id,
        TeaEntry.tea_name.ilike(f"%{name_part}%")
    ).order_by(desc(TeaEntry.created_at)).all()
    session.close()
    return results

def search_by_rating(user_id, min_rating):
    session = SessionLocal()
    results = session.query(TeaEntry).filter(
        TeaEntry.user_id == user_id,
        TeaEntry.rating >= min_rating
    ).order_by(desc(TeaEntry.rating)).all()
    session.close()
    return results

def show_all_entries(user_id):
    return get_entries(user_id)

def get_entries_paginated(user_id: int, limit: int, offset: int):
    session = SessionLocal()
    entries = session.query(TeaEntry).filter_by(user_id=user_id).order_by(desc(TeaEntry.created_at)).offset(offset).limit(limit).all()
    session.close()
    return entries

def count_entries(user_id: int):
    session = SessionLocal()
    total = session.query(TeaEntry).filter_by(user_id=user_id).count()
    session.close()
    return total

def delete_entry(entry_id: int):
    session = SessionLocal()
    session.query(TeaEntry).filter_by(id=entry_id).delete()
    session.commit()
    session.close()

init_db()
