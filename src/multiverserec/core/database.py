from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DSN = "postgresql://admin:secret@localhost:5432/recommender"

engine = create_engine(DSN)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()