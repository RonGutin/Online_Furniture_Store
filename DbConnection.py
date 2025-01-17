import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import text
from sqlalchemy import Column, Integer, String, Float



DATABASE_USERNAME = "root"
DATABASE_PASSWORD = "HaHa12345!"
DATABASE_HOST = "localhost"
DATABASE_PORT = "3306"
DATABASE_NAME = "FinalProjectDB"

DATABASE_URL = f"mysql+pymysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

try:
    session = SessionLocal()
    result = session.execute(text("SELECT 1"))
    print("Connection successful!")

    session.close()
except Exception as e:
    print(f"Error connecting to DB or applying discount:: {e}")

class CouponsCodes(Base):
    __tablename__ = "CouponsCodes"
    idCouponsCodes = Column(Integer, primary_key=True, index=True)
    CouponValue = Column(String(48), unique=True, nullable=False)
    Discount = Column(Integer, nullable=False)