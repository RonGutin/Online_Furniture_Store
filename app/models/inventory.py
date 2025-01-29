from cmath import inf
from flask import jsonify
from app.data.DbConnection import SessionLocal, InventoryDB
from sqlalchemy import and_

class Inventory:
    _instance = None  # Singleton instance
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_indx_furniture_by_values(self, furniture_type, color, high, depth, width, is_adjustable, has_armrest, material):
        try:
            ans = None
            with SessionLocal() as session:
                try:
                    result = self.session.query(InventoryDB.id).filter(
                            and_(
                                InventoryDB.furniture_type == furniture_type,
                                InventoryDB.color == color,
                                InventoryDB.high == high,
                                InventoryDB.depth == depth,
                                InventoryDB.width == width,
                                InventoryDB.is_adjustable == is_adjustable,
                                InventoryDB.has_armrest == has_armrest,
                                InventoryDB.material == material
                            )
                        ).first()
                        # Return the ID if a match is found
                    if result:
                        ans = result[0]
                except Exception as e:
                    print(f"Error fetching data: {e}")
                    ans = -1 # there is not furniture with those params 
        except Exception as ex:
            print(f"DB connection error: {ex}")
        finally:
            session.close()
            return ans 

    def update_quntity(self, indx, action, quantity):
        succsuss = True
        try:
            with SessionLocal() as session:
                row = session.query(InventoryDB).filter_by(id=indx).first()
                if row:
                    if action:
                        row.quntity = max(row.quntity - quantity ,0)
                    else:
                        row.quntity += quantity
                else:
                    succsuss = False
        except Exception as e:
            succsuss = False
            print(f"Error fetching data: {e}")
        finally:
            session.close()
            return succsuss

    def get_information_by_query(self, column, column_value): #coulmn = f_type, coulmn_value= Chair
        ans = None
        try:
            with SessionLocal() as session:
                col = getattr(InventoryDB, column, None)
                if col is None:
                    raise ValueError(f"Column '{column}' does not exist in the table.")
                else:
                    result = session.query(InventoryDB).filter(col == column_value).all()
                    if result:
                        json_data = []
                        for row in result:
                            pass ################### להשלים את הלולאה לפי השימוש בפונקציה 
                        ans = jsonify(json_data)
        except Exception as e:
            print(f"Error fetching data: {e}")
        finally:
            session.close()
            return ans 

    def get_information_by_price_range(self, min_price= 0, max_price = inf):
        ans = None
        try:
            with SessionLocal() as session:
                result = session.query(InventoryDB).filter(and_(InventoryDB.price >= min_price, InventoryDB.price <= max_price)).all()
                if result:
                    json_data = []
                    for row in result:
                        pass ################### להשלים את הלולאה לפי השימוש בפונקציה 
                    ans = jsonify(json_data)
                else:
                    pass
                    ############# להחליט מה מחזירים כשהצלחנו לבצע שליפה אבל אין תוצאה מתאימה
        except Exception as e:
            print(f"Error fetching data: {e}")
        finally:
            session.close()
            return ans 