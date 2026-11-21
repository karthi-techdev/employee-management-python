import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:2002@localhost:5432/hr_assistant")

engine = create_engine(DB_URL)
local_session = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

