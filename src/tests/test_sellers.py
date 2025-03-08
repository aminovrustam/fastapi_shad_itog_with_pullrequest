import pytest
from fastapi import status
from sqlalchemy import select
from src.models.books import Book
from src.models.sellers import Seller


# Тест на ручку создающую продавца
@pytest.mark.asyncio
async def test_create_seller(async_client):
    seller_data = {
        "first_name": "Rustam", 
        "last_name": "Aminov", 
        "email": "ru123@mail.com", 
        "password": "kskfls"
    }
    
    response = await async_client.post("/api/v1/sellers/", json=seller_data)
    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    resp_seller_id = result_data.pop("id", None)
    assert resp_seller_id, "Seller id not returned from endpoint"

    assert result_data == {
        "first_name": "Rustam", 
        "last_name": "Aminov", 
        "email": "ru123@mail.com", 
    }


# Тест на ручку получения списка продавцов
@pytest.mark.asyncio
async def test_get_sellers(db_session, async_client):
    # Создаем продавцов вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    seller = Seller(
        first_name="Rustam", 
        last_name="Aminov", 
        email="ru123@mail.com", 
        password="kskfls"
    )
    seller_2 = Seller(
        first_name="Ozzy", 
        last_name="Osbourne", 
        email="crazytrain@gmail.com", 
        password="usuzdcmf"
    )
    
    db_session.add_all([seller, seller_2])
    await db_session.flush()

    response = await async_client.get("/api/v1/sellers/")

    assert response.status_code == status.HTTP_200_OK

    assert (
        len(response.json()["sellers"]) == 2
    )  # Опасный паттерн! Если в БД есть данные, то тест упадет

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "sellers": [
            {
                "id": seller.id,
                "first_name": "Rustam", 
                "last_name": "Aminov", 
                "email":"ru123@mail.com", 
            },
            {
                "id": seller_2.id,
                "first_name": "Ozzy", 
                "last_name": "Osbourne", 
                "email":"crazytrain@gmail.com", 
            },
        ]
    }


# Тест на ручку получения продавца и его книг
@pytest.mark.asyncio
async def test_get_single_seller(db_session, async_client):
    seller = Seller(
        first_name="Rustam", 
        last_name="Aminov", 
        email="ru123@mail.com", 
        password="kskfls"
    )
    seller_2 = Seller(
        first_name="Ozzy", 
        last_name="Osbourne", 
        email="crazytrain@gmail.com", 
        password="asdff28"
    )
    # Создаем продавцов вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    

    db_session.add_all([seller, seller_2])
    await db_session.flush()

    book = Book(
        author="Lermontov", 
        title="Mtziri", 
        pages=510, 
        year=2024,
        seller_id=seller.id
    )
    
    db_session.add(book)
    await db_session.flush()

    response = await async_client.get(f"/api/v1/sellers/{seller.id}")

    assert response.status_code == status.HTTP_200_OK

    # Проверяем интерфейс ответа, на который у нас есть контракт.
    assert response.json() == {
        "id": seller.id,
        "first_name": "Rustam", 
        "last_name": "Aminov", 
        "email":"ru123@mail.com",
        "books": [
            {   "id": book.id,
                "author": "Lermontov",
                "title": "Mtziri",
                "pages": 510,
                "year": 2024,
            }
        ]
    }


# Тест ручки удаления продавца
@pytest.mark.asyncio
async def test_delete_seller(db_session, async_client):
    seller = Seller(
        first_name = "Rustam",
        last_name = "Aminov",
        email="ru123@mail.com",
        password="kskfls"
    )

    db_session.add(seller)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/sellers/{seller.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    await db_session.flush()

    all_sellers = await db_session.execute(select(Seller))
    res = all_sellers.scalars().all()

    assert len(res) == 0


# Тест ручки обновления данных о продавце
@pytest.mark.asyncio
async def test_update_seller(db_session, async_client):
    # Создаем продавца вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    seller = Seller(
        first_name = "Rustam",
        last_name = "Aminov",
        email="ru123@blabla.ru",
        password="udq11elsja"
    )

    db_session.add(seller)
    await db_session.flush()

    response = await async_client.put(
        f"/api/v1/sellers/{seller.id}",
        json={
            "first_name": "Anton",
            "last_name": "Vasilyev",
            "email": "ru123@blabla.ru",
            "password": "udq11elsja",
            "id": seller.id
        },
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    # Проверяем, что обновились все поля
    res = await db_session.get(Seller, seller.id)
    assert res.first_name == "Anton"
    assert res.last_name == "Vasilyev"
    assert res.email == "ru123@blabla.ru"
    assert res.password == "udq11elsja"
    assert res.id == seller.id


# Тест обращения к продавцу по несуществующему id
@pytest.mark.asyncio
async def test_get_seller_with_invalid_id(db_session, async_client):
    seller = Seller(first_name="Rustam", last_name="Aminov", email="ru123@mail.com", password="kskfls")

    db_session.add(seller)
    await db_session.flush()

    response = await async_client.get(f"/api/v1/sellers/{seller.id + 1}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


# Удаление продавца с неправильным id
@pytest.mark.asyncio
async def test_delete_seller_with_invalid_id(db_session, async_client):
    seller = Seller(
        first_name = "Rustam",
        last_name = "Aminov",
        email="ru123@mail.com",
        password="kskfls"
    )

    db_session.add(seller)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/sellers/{seller.id+1}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    

# Тест на ручку обновления данных о продавце с неправильным id
@pytest.mark.asyncio
async def test_update_with_invalid_id(db_session, async_client):
    # Создаем книги вручную, а не через ручку, чтобы нам не попасться на ошибку которая
    # может случиться в POST ручке
    seller = Seller(
        first_name = "Rustam",
        last_name = "Aminov",
        email="ru123@blabla.ru",
        password="udq11elsja"
    )

    db_session.add(seller)
    await db_session.flush()

    response = await async_client.put(
        f"/api/v1/sellers/{seller.id+1}",
        json={
            "first_name": "Anton",
            "last_name": "Vasilyev",
            "email": "ru123@blabla.ru",
            "password": "udq11elsja",
            "id": seller.id
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


# Тест создание пользователя с неправильным форматом email
@pytest.mark.asyncio
async def test_create_seller_with_invalid_email(db_session, async_client):
    seller_data = {
        "first_name": "Rustam", 
        "last_name": "Aminov", 
        "email": "abracadabra", 
        "password": "kskfls"
    }
    
    response = await async_client.post("/api/v1/sellers/", json=seller_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
