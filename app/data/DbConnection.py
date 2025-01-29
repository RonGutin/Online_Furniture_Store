import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import text
from sqlalchemy import Column, Integer, String, Float, Boolean, CheckConstraint

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
    print(f"Error connecting to DB or applying discount: {e}")


class CouponsCodes(Base):
    __tablename__ = "CouponsCodes"
    idCouponsCodes = Column(Integer, primary_key=True, index=True)
    CouponValue = Column(String(48), unique=True, nullable=False)
    Discount = Column(Integer, nullable=False)


class InventoryDB(Base):
    __tablename__ = 'Inventory'
    id = Column(Integer, primary_key=True, autoincrement=True)
    furniture_type = Column(Integer, nullable=False)
    color = Column(String(50), nullable=False)
    f_name = Column(String(500), nullable=False)
    f_desc = Column(String(1000), nullable=False)
    price = Column(Float, nullable=False)
    high = Column(Integer, nullable=False)
    depth = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    is_adjustable = Column(Boolean, nullable=False, default=False)
    has_armrest = Column(Boolean, nullable=False, default=False)
    material = Column(String(50), nullable=False)
    quntity = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint(
            'furniture_type IN (1, 2, 3, 4, 5)',
            name='check_furniture_type'
        ),
    )

class UserDB(Base):
    """SQLAlchemy model for User table"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Will store the hashed password from Authentication || need to think if it should be here or not (security)
    address = Column(String(255), nullable=False)
    credit = Column(Float, default=0.0)
    type = Column(String(50))  # For user/manager discrimination
