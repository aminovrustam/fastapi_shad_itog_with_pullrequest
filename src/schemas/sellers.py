import re
from pydantic import BaseModel, Field, field_validator, EmailStr
from pydantic_core import PydanticCustomError
from .books import ReturnedBook, ReturnedBookWithotSeller

__all__ = ["IncomingSeller", "ReturnedSeller", "ReturnedSellerWithBooks", "ReturnedAllsellers"]


# Базовый класс "Продавца", содержащий поля, которые есть во всех классах-наследниках.
class BaseSeller(BaseModel):
    first_name: str
    last_name: str
    email: str


# Класс для валидации входящих данных. Не содержит id так как его присваивает БД.
class IncomingSeller(BaseSeller):
    password: str

    # Валидация почтового адресса
    @field_validator("email")
    @staticmethod
    def validate_email(val: str):
        pattern = r'^[A-Za-z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(pattern, val):
            raise PydanticCustomError('Validation error', 'Email is wrong!')
        return val    


# Класс, валидирующий исходящие данные. Он уже содержит id
class ReturnedSeller(BaseSeller):
    id: int

# Класс для возврата продавца со списком связанных с ним книг
class ReturnedSellerWithBooks(BaseSeller):
    id: int
    books: list[ReturnedBookWithotSeller]

# Класс для возврата массива объектов "Продавец"
class ReturnedAllsellers(BaseModel):
    sellers: list[ReturnedSeller]