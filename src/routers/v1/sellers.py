from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from src.models.books import Book
from src.models.sellers import Seller
from src.schemas import IncomingSeller, ReturnedAllsellers, ReturnedSeller
from icecream import ic
from sqlalchemy.ext.asyncio import AsyncSession
from src.configurations import get_async_session
from src.schemas.books import ReturnedBook, ReturnedBookWithotSeller
from src.schemas.sellers import ReturnedSellerWithBooks

sellers_router = APIRouter(tags=["sellers"], prefix="/sellers")

# CRUD - Create, Read, Update, Delete

DBSession = Annotated[AsyncSession, Depends(get_async_session)]


# Ручка для создания записи о книге в БД. Возвращает созданную книгу
@sellers_router.post(
    "/", response_model=ReturnedSeller, status_code=status.HTTP_201_CREATED
)  # Прописываем модель ответа
async def create_seller(
    seller: IncomingSeller,
    session: DBSession,
):  # прописываем модель валидирующую входные данные
    # session = get_async_session() вместо этого мы используем иньекцию зависимостей DBSession

    # это - бизнес логика. Обрабатываем данные, сохраняем, преобразуем и т.д.
    new_seller = Seller(
        first_name=seller.first_name,
        last_name=seller.last_name,
        email=seller.email,
        password=seller.password
    )

    session.add(new_seller)
    await session.flush()

    return new_seller


# Ручка возвращающая список продавцов
@sellers_router.get("/", response_model=ReturnedAllsellers)
async def get_all_sellers(session: DBSession):
    query = select(Seller)
    result = await session.execute(query)
    sellers = result.scalars().all()
    return {"sellers": sellers}


# Ручка возвращающая продавца и список его книг 
@sellers_router.get("/{seller_id}", response_model=ReturnedSellerWithBooks)
async def get_seller(seller_id: int, session: DBSession):
    seller = await session.get(Seller, seller_id)

    if seller is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    
    query = select(Book).filter(Book.seller_id == seller_id)
    books_dp = await session.execute(query)
    books_db = books_dp.scalars().all()

    books = [ReturnedBookWithotSeller(
        id = book.id,
        title=book.title,
        author=book.author,
        year=book.year,
        pages=book.pages,
    ) for book in books_db]

    seller_responce = {
        "id": seller.id,
        "first_name": seller.first_name,
        "last_name": seller.last_name,
        "email": seller.email,
        "books": books
    }
    
    return seller_responce

# Ручка для обновления данных о продавце
@sellers_router.put("/{seller_id}", response_model=ReturnedSeller)
async def update_seller(seller_id: int, new_data: ReturnedSeller, session: DBSession):
    # Оператор "морж", позволяющий одновременно и присвоить значение и проверить его.
    if updated_seller := await session.get(Seller, seller_id):
        updated_seller.first_name = new_data.first_name
        updated_seller.last_name = new_data.last_name
        updated_seller.email = new_data.email

        await session.flush()

        return updated_seller

    return Response(status_code=status.HTTP_404_NOT_FOUND)


# Ручка для удаления данных о продавце
@sellers_router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(seller_id: int, session: DBSession):
    deleted_seller = await session.get(Seller, seller_id)
    ic(deleted_seller)  # Красивая и информативная замена для print. Полезна при отладке.
    if deleted_seller:
        await session.delete(deleted_seller)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)