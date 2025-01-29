from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
import re
from typing import Optional, List
from datetime import datetime
from app.models.ShoppingCart import ShoppingCart
from app.data.DbConnection import SessionLocal, UserDB

class User:
    """
    User class for managing user authentication and profile information in the furniture store.
    
    Attributes:
        name (str): User's name
        email (str): User's email address
        password (str): Hashed password
        address (str): User's delivery address
        credit (float): User's credit available to spend
        cart (ShoppingCart): User's shopping cart
        orders (List): List of user's orders
    """
    
    def __init__(self, name: str, email: str, password: str, address: str, credit :float = 0):
        """
        Initialize a new User instance.
        Note: This should only be called by the Authentication class.
        """
        self.name = name
        self.email = self._validate_email(email)
        self.password = password  # Already hashed by Authentication
        self.address = address
        self.credit = credit
        self.cart = ShoppingCart(self) 
        self.orders = []

    def _validate_email(self, email: str) -> str:
        """
        Validate email format using regex.
        
        Args:
            email (str): Email address to validate
            
        Returns:
            str: Validated email address
            
        Raises:
            ValueError: If email format is invalid
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        return email.lower()

    def update_user_details(self, address: Optional[str] = None, email: Optional[str] = None) -> None:
        """Update user profile information."""
        if (address is None and email is None): return
        session = SessionLocal()
        try:
            user_db = session.query(UserDB).filter(UserDB.email == self.email).first()
            if not user_db:
                raise ValueError("User not found in database")

            if address is not None:
                user_db.address = address
                self.address = address
            if email is not None:
                new_email = self._validate_email(email)
                user_db.email = new_email
                self.email = new_email

            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating user details: {e}")
        finally:
            session.close()
            
    def update_credit(self, credit: float) -> None:
        """Update user's credit balance."""
        session = SessionLocal()
        try:
            user_db = session.query(UserDB).filter(UserDB.email == self.email).first()
            if not user_db:
                raise ValueError("User not found in database")

            user_db.credit = credit
            self.credit = credit
            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating credit: {e}")
        finally:
            session.close()

    def delete_user(self) -> None:
        """Delete user from database."""
        session = SessionLocal()
        try:
            user_db = session.query(UserDB).filter(UserDB.email == self.email).first()
            if user_db:
                session.delete(user_db)
                session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error deleting user: {e}")
        finally:
            session.close()
    
    def view_cart(self) -> str:
        return str(self.cart)

    def get_order_hist(self) -> List:
        """
        Retrieve user's order history.
        
        Returns:
            List: List of Order objects associated with the user
        """
        return self.orders
    
    def set_new_password(self, new_password: str) -> None:
        """Update user's password."""
        session = SessionLocal()
        try:
            user_db = session.query(UserDB).filter(UserDB.email == self.email).first()
            if not user_db:
                raise ValueError("User not found in database")

            hashed_password = self._hash_password(new_password)
            user_db.password = hashed_password
            self.password = hashed_password
            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating password: {e}")
        finally:
            session.close()

    def checkout(self) -> bool:
        #needs implementation of Order class
        pass
        
    def __str__(self) -> str:
        """String representation of the User object."""
        return f"User(Name ={self.name}, Email={self.email}, Address={self.address}, Credit={self.credit})"
    