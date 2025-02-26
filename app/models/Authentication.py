import bcrypt
from typing import Union
from app.data.DbConnection import SessionLocal, BasicUserDB, UserDB, ManagerDB
from app.models.Users import User, Manager


class Authentication:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def _hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def validate_auth(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    def create_user(
        self, name: str, email: str, password: str, address: str, credit: float = 0
    ) -> User:

        session = SessionLocal()
        try:
            existing_basic_user = (
                session.query(BasicUserDB).filter(BasicUserDB.email == email).first()
            )
            if existing_basic_user:
                print("This email already exists in BasicUserDB")
                return None

            hashed_password = self._hash_password(password)

            basic_user_db = BasicUserDB(
                name=name, email=email, password=hashed_password
            )

            user_db = UserDB(email=email, address=address, credit=credit)

            session.add(basic_user_db)
            session.add(user_db)
            session.commit()

            return User(name, email, hashed_password, address, credit)

        except Exception as e:
            session.rollback()
            print(f"Error creating user: {e}")
            return None
        finally:
            session.close()

    def create_manager(self, name: str, email: str, password: str) -> Manager:
        session = SessionLocal()
        try:
            existing_basic_user = (
                session.query(BasicUserDB).filter(BasicUserDB.email == email).first()
            )
            if existing_basic_user:
                print("This email already exists in BasicUserDB")
                return None

            hashed_password = self._hash_password(password)

            basic_manager_db = BasicUserDB(
                name=name, email=email, password=hashed_password
            )

            manager_db = ManagerDB(email=email)

            session.add(basic_manager_db)
            session.add(manager_db)
            session.commit()

            return Manager(name, email, hashed_password)

        except Exception as e:
            session.rollback()
            print(f"Error creating manager: {e}")
            return None
        finally:
            session.close()

    def sign_in(self, email: str, password: str) -> Union[User, Manager, None]:
        session = SessionLocal()
        try:
            basic_user = (
                session.query(BasicUserDB).filter(BasicUserDB.email == email).first()
            )
            user = session.query(UserDB).filter(UserDB.email == email).first()
            if user and self.validate_auth(password, basic_user.password):
                return User(
                    basic_user.Uname,
                    user.email,
                    basic_user.Upassword,
                    user.address,
                    user.credit,
                )

            manager = session.query(ManagerDB).filter(ManagerDB.email == email).first()
            if manager and self.validateAuth(password, manager.password):
                return Manager(manager.name, manager.email, manager.password)

            print("Invalid credentials or user/manager does not exist")
            return None

        except Exception as e:
            session.rollback()
            print(f"Error during login: {e}")
            return None

        finally:
            session.close()

    def set_new_password(
        self, curr_basic_user: Union[User, Manager, None], new_password: str
    ) -> None:
        """Update user's/manager's password."""
        session = SessionLocal()
        try:
            basic_user_db = (
                session.query(BasicUserDB)
                .filter(BasicUserDB.email == curr_basic_user.email)
                .first()
            )
            if not basic_user_db:
                raise ValueError("User/Manager not found in database")

            hashed_password = self._hash_password(new_password)
            basic_user_db.Upassword = hashed_password

            session.commit()
            print(f"Password successfully changed for:\n{curr_basic_user}")

        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating password: {e}")
        finally:
            session.close()

    def validate_credit_card(total_price: int, credit_card_num: int) -> bool:
        if not total_price:
            return True
        if isinstance(credit_card_num, int):
            return True
        return False
