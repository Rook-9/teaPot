from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # Подставим Railway URL через переменную окружения

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class TeaEntry(Base):
    __tablename__ = "tea_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    tea_name = Column(String(100))
    description = Column(String)
    how_to_brew = Column(String)
    rating = Column(Float)
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
