from abc import ABC, abstractmethod
from sqlalchemy import Column, Integer, String, Float, ForeignKey, and_
from sqlalchemy.orm import relationship
import re 
from typing import Optional, List
from datetime import datetime
from app.models.ShoppingCart import ShoppingCart
from app.data.DbConnection import SessionLocal, UserDB , BasicUserDB , ManagerDB , OrdersDB, InventoryDB
from app.models.Authentication import Authentication
from app.models.EnumsClass import OrderStatus, FurnitureType
from app.models.order import Order
from app.models.FurnituresClass import Furniture,Table,Chair
from app.utils import transform_pascal_to_snake 



class BasicUser(ABC):
    
    def __init__(self, name: str, email: str, password: str):
            """
            Initialize a new User instance.
            Note: This should only be called by the Authentication class.
            """
            self.name = name
            self.email = self._validate_email(email)
            self.password = password  # Already hashed by Authentication
            
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
    
    def update_chair_amount_in_DB(self, item: Chair, quantity: int,f_type_enum: int, sign: bool) -> None:
        """
        Updates quantity field for a specific Chair in the InventoryDB.
        sign - boolean that points if it is auser making a checkout (sign = 0) 
        or a manager updating inventory(sign = 1) 
        """
        session = SessionLocal()
        try:
            invetory_item = session.query(InventoryDB.id).filter(
                                    and_(
                                        InventoryDB.furniture_type == f_type_enum,
                                        InventoryDB.color == item.color,
                                        InventoryDB.high == item.dimensions[0],
                                        InventoryDB.depth == item.dimensions[1],
                                        InventoryDB.width == item.dimensions[2],
                                        InventoryDB.is_adjustable == item.is_adjustable,
                                        InventoryDB.has_armrest == item.has_armrest,
                                    )
                                ).first()
            if sign:   
                invetory_item.quantity += quantity
            else:
                invetory_item.quantity -= quantity

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error in updating Chair quantity in DB: {e}")
            return None
        finally:
            session.close()  

    def update_table_amount_in_DB(self, item: Table, quantity: int,f_type_enum: int, sign: bool) -> None:
        """
        Updates quantity field for a specific Table in the InventoryDB.
        sign - boolean that points if it is a user is making a checkout (sign = 0) 
        or a manager updating inventory(sign = 1) 
        """
        session = SessionLocal()
        try:
            invetory_item = session.query(InventoryDB.id).filter(
                                    and_(
                                        InventoryDB.furniture_type == f_type_enum,
                                        InventoryDB.color == item.color,
                                        InventoryDB.high == item.dimensions[0],
                                        InventoryDB.depth == item.dimensions[1],
                                        InventoryDB.width == item.dimensions[2],
                                        InventoryDB.material == item.material
                                    )
                                ).first()
            if sign:   
                invetory_item.quantity += quantity
            else:
                invetory_item.quantity -= quantity

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error in updating Table quantity in DB: {e}")
            return None
        finally:
            session.close()  

    @abstractmethod
    def set_password(self) -> None:
        pass

    @abstractmethod
    def __repr__(self):
        pass
    
class User(BasicUser):
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
        super().__init__(name, email, password)
        self.address = address
        self.credit = credit
        self.cart = ShoppingCart(self) 
        self.orders = []

    def update_user_details(self, address: Optional[str] = None, name: Optional[str] = None) -> None:
        """Update user profile information."""
        if (address is None and name is None): return
        session = SessionLocal()
        try:
            user_db = session.query(UserDB).filter(UserDB.email == self.email).first()
            if not user_db:
                raise ValueError("User not found in database")
            
            basic_user_db = session.query(BasicUserDB).filter(BasicUserDB.email == self.email).first() # no check beacause if exists in UserDB -> exists in BasicUserDB

            if address is not None:
                user_db.address = address
                self.address = address
            if name is not None:
                basic_user_db.Uname = name
                self.name = name

            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating user details: {e}")
        finally:
            session.close()
            
    def update_credit(self, credit: float) -> None:
        """Update user's credit balance."""
        try: 
            session = SessionLocal()
            user_db = session.query(UserDB).filter(UserDB.email == self.email).first()
            if not user_db:
                raise ValueError("User not found in database")

            user_db.credit += credit
            self.credit = user_db.credit
            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating credit: {e}")
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
    
    def set_password(self, new_password: str) -> None:
        Authentication.set_new_password(self,new_password)
        return

    def update_amount_in_inventory(self,item: Furniture, quantity: int, sign: bool) -> None:
        furniture_type = transform_pascal_to_snake(item.__class__.__name__)
        f_type_enum = FurnitureType[furniture_type].value
        if isinstance(item,Table):
            self.update_table_amount_in_DB(item, quantity,f_type_enum,sign)
        elif isinstance(item,Chair):
            self.update_chair_amount_in_DB(item, quantity,f_type_enum,sign)  

    def checkout(self, credit_card_num: int, coupon_code: Optional[int] = None) -> bool:
        ans = False
        session = SessionLocal()
        try:
            if coupon_code: total_price,coupon_id = self.cart.apply_discount(coupon_code)
            else: total_price = self.cart.get_total_price()    
            
            if self.credit:
                if self.credit <= total_price: 
                    total_price -= self.credit
                    self.update_credit(self.credit*-1)
                else:
                    self.update_credit(total_price*-1)
                    total_price = 0    
                
            if Authentication.validate_credit_card(total_price,credit_card_num):
                for item,amount in self.cart.items:
                    self.update_amount_in_inventory(item,amount,sign=False)
            else:
                raise ValueError("Invalid Credit Card")
            
            new_order = Order(self.email,self.cart,coupon_id)
            self.orders.append(new_order)
            ans = True

        except Exception as e:
            session.rollback()
            print(f"Error in checkout Proc: {e}")
        finally:
            session.close()        
            return ans

    def __repr__(self) -> str:
        """String representation of the User object."""
        return f"User: Name ={self.name}, Email={self.email}, Address={self.address}, Credit={self.credit}"
    
class Manager(BasicUser):
    
    def __init__(self, name: str, email: str, password: str):
        """
        Initialize a new User instance.
        Note: This should only be called by the Authentication class.
        """
        super().__init__(name, email, password)
        
    def __repr__(self) -> str:
        """String representation of the Manager object."""
        return f"Manager: Name = {self.name}, Email = {self.email}"
    
    def delete_user(self, email) -> None:
        """Delete user from databases."""
        session = SessionLocal()
        try:
            user_db = session.query(UserDB).filter(UserDB.email == email).first()
            basic_user_db = session.query(BasicUserDB).filter(BasicUserDB.email == email).first()
            if user_db:
                session.delete(user_db)
            if basic_user_db: 
                session.delete(basic_user_db)

            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error deleting user: {e}")
        finally:
            session.close()
            
    def set_password(self, new_password: str) -> None:
        Authentication.set_new_password(self,new_password)
        return  
    
    def add_manager(self, name: str, email: str, password: str) -> "Manager":    
        return Authentication.create_manager(name, email, password)

    def update_order_status(self, order_id : int) -> None:
        """
        Updating order status in Database
        If already delivered raises an error
        """
        session = SessionLocal()
        try:
            order_db = session.query(OrdersDB).filter(OrdersDB.id == order_id).first()
            if order_db.id == OrderStatus.DELIVERED:
                raise ValueError(f"Order number {order_id} already delivered")
            else:
                order_db.Ostatus += 1
            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating Order status: {e}")
        finally:
            session.close()        
                
    def update_inventory(self):
        pass
    
    def get_all_orders(self):
        pass        