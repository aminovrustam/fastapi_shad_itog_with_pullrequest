import pytest
from sqlalchemy import select
from src.models.books import Book
from fastapi import status
from icecream import ic

from src.models.sellers import Seller


# Тест на ручку создающую книгу
@pytest.mark.asyncio
async def test_create_book(db_session, async_client):
    seller = Seller(
        first_name="Rustam", 
        last_name="Aminov", 
        email="ru123@mail.com", 
        password="kskfls"
        )

    db_session.add(seller)
    await db_session.flush()

    book_data = {
        "title": "Eugeny Onegin",
        "author": "Pushkin", 
        "count_pages": 400, 
        "year": 2024, 
        "seller_id": seller.id
        }
    
    response = await async_client.post("/api/v1/books/", json=book_data)
    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    resp_book_id = result_data.pop("id", None)
    assert resp_book_id, "Book id not returned from endpoint"

    resp_seller_id = result_data.pop("seller_id", None)
    assert resp_book_id, "Seller id not returned from endpoint"

    assert result_data == {
        "title": "Eugeny Onegin",
        "author": "Pushkin",
        "pages": 400,
        "year": 2024,
    }


# Тест на ручку создающую книгу со старым годом
@pytest.mark.asyncio
async def test_create_book_with_old_year(db_session, async_client):
    seller = Seller(
        first_name="Rustam", 
        last_name="Aminov", 
        email="ru123@mail.com", 
        password="kskfls"
    )

    db_session.add(seller)
    await db_session.flush()
    
    data = {
        "title": "Eugeny Onegin",
        "author": "Pushkin",
        "count_pages": 300,
        "year": 1986,
        "seller_id": seller.id
    }
    response = await async_client.post("/api/v1/books/", json=data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Тест на ручку получения списка книг
@pytest.mark.asyncio
async def test_get_books(db_session, async_client):
    seller = Seller(
        first_name="Rustam", 
        last_name="Aminov", 
        email="ru123@mail.com", 
        password="kskfls"
        )

    db_session.add(seller)
    await db_session.flush()
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(
        author="Pushkin", 
        title="Eugeny Onegin", 
        year=2021, 
        pages=231, 
        seller_id=seller.id
        )
    
    book_2 = Book(
        author="Lermontov", 
        title="Mziri", 
        year=2022, 
        pages=104, 
        seller_id=seller.id
        )

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get("/api/v1/books/")

    assert response.status_code == status.HTTP_200_OK

    assert (
        len(response.json()["books"]) == 2
    )  # Опасный паттерн! Если в БД есть данные, то тест упадет

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "books": [
            {
                "title": "Eugeny Onegin",
                "author": "Pushkin",
                "year": 2021,
                "id": book.id,
                "pages": 231,
                "seller_id": seller.id,
            },
            {
                "title": "Mziri",
                "author": "Lermontov",
                "year": 2022,
                "id": book_2.id,
                "pages": 104,
                "seller_id": seller.id,
            },
        ]
    }


# Тест на ручку получения одной книги
@pytest.mark.asyncio
async def test_get_single_book(db_session, async_client):
    seller = Seller(first_name="Ivan", last_name="Ivanov", email="iivanov@mail.ru", password="vano228", books=[])

    db_session.add(seller)
    await db_session.flush()
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2021, pages=231, seller_id=seller.id)
    book_2 = Book(author="Lermontov", title="Mziri", year=2022, pages=104, seller_id=seller.id)

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"/api/v1/books/{book.id}")

    assert response.status_code == status.HTTP_200_OK

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "title": "Eugeny Onegin",
        "author": "Pushkin",
        "year": 2021,
        "pages": 231,
        "id": book.id,
        "seller_id": seller.id
    }


# Тест на ручку обновления книги 
@pytest.mark.asyncio
async def test_update_book(db_session, async_client):
    seller = Seller(first_name="Rustam", last_name="Aminov", email="ru123@mail.com", password="kskfls")

    db_session.add(seller)
    await db_session.flush()
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2021, pages=100, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.put(
        f"/api/v1/books/{book.id}",
        json={
            "title": "Mziri",
            "author": "Lermontov",
            "pages": 500,
            "year": 2021,
            "id": book.id,
            "seller_id": seller.id
        },
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    # Проверяем, что обновились все поля
    res = await db_session.get(Book, book.id)
    assert res.title == "Mziri"
    assert res.author == "Lermontov"
    assert res.pages == 500
    assert res.year == 2021
    assert res.id == book.id

# Тест на ручку удаления книги
@pytest.mark.asyncio
async def test_delete_book(db_session, async_client):
    seller = Seller(first_name="Rustam", last_name="Aminov", email="ru123@mail.com", password="kskfls")

    db_session.add(seller)
    await db_session.flush()

    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()
    ic(book.id)

    response = await async_client.delete(f"/api/v1/books/{book.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    await db_session.flush()
    all_books = await db_session.execute(select(Book))
    res = all_books.scalars().all()

    assert len(res) == 0


# Тест на ручку удаления книги с неправильным id
@pytest.mark.asyncio
async def test_delete_book_with_invalid_book_id(db_session, async_client):
    seller = Seller(first_name="Rustam", last_name="Aminov", email="ru123@mail.com", password="kskfls")

    db_session.add(seller)
    await db_session.flush()

    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/books/{book.id + 1}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# Создание книги с несуществующим продавцом
@pytest.mark.asyncio
async def test_create_book_without_seller(db_session, async_client):

    book_data = {
        "title": "Eugeny Onegin",
        "author": "Pushkin", 
        "count_pages": 400, 
        "year": 2024, 
        "seller_id": 52
        }
    
    response = await async_client.post("/api/v1/books/", json=book_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Обращение к книги с неправильным id
@pytest.mark.asyncio
async def test_get_book_with_invalid_book_id(db_session, async_client):
    seller = Seller(first_name="Rustam", last_name="Aminov", email="ru123@mail.com", password="kskfls")

    db_session.add(seller)
    await db_session.flush()

    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.get(f"/api/v1/books/{book.id + 1}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# Тест на ручку обновления книги с неправильным id
@pytest.mark.asyncio
async def test_update_book_with_invalid_book_id(db_session, async_client):
    seller = Seller(first_name="Rustam", last_name="Aminov", email="ru123@mail.com", password="kskfls")

    db_session.add(seller)
    await db_session.flush()
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2021, pages=100, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.put(
        f"/api/v1/books/{book.id + 1}",
        json={
            "title": "Mziri",
            "author": "Lermontov",
            "pages": 500,
            "year": 2021,
            "id": book.id,
            "seller_id": seller.id
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    