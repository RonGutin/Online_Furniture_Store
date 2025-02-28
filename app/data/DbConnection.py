from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    CheckConstraint,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import text


DATABASE_USERNAME = "root"
DATABASE_PASSWORD = "RAZRAZ123"
DATABASE_HOST = "localhost"
DATABASE_PORT = "3306"
DATABASE_NAME = "FinalProjectDB"

DATABASE_URL = (
    f"mysql+pymysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/"
    f"{DATABASE_NAME}"
)
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
    __tablename__ = "Inventory"
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
    quantity = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint(
            "furniture_type IN (1, 2, 3, 4, 5)", name="check_furniture_type"
        ),
    )


class BasicUserDB(Base):
    """SQLAlchemy model for BasicUser table"""

    __tablename__ = "BasicUser"

    email = Column(String(100), primary_key=True, index=True)
    Uname = Column(String(100), nullable=False)
    Upassword = Column(String(255), nullable=False)


class UserDB(Base):
    """SQLAlchemy model for User table"""

    __tablename__ = "Users"

    email = Column(String(100), primary_key=True, index=True)
    address = Column(String(255), nullable=False)
    credit = Column(Float, default=0.0)


class ManagerDB(Base):
    """SQLAlchemy model for Manager table"""

    __tablename__ = "Managers"
    email = Column(String(100), primary_key=True, index=True)


class OrdersDB(Base):
    """SQLAlchemy model for Orders table"""

    __tablename__ = "Orders"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Ostatus = Column(Integer, nullable=False)
    UserEmail = Column(String(100), nullable=False)
    idCouponsCodes = Column(Integer, nullable=True)


class OrderContainsItemDB(Base):
    """SQLAlchemy model for Order Contains Item table"""

    __tablename__ = "OrderContainsItem"
    OrderID = Column(Integer, primary_key=True, nullable=False)
    ItemID = Column(Integer, primary_key=True, nullable=False)
    Amount = Column(Integer, nullable=False)
