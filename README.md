# 🍲 Foodgram — сервис рецептов

**Foodgram** — это онлайн-сервис для публикации рецептов, подписок на авторов, добавления рецептов в избранное и формирования списка покупок.  
Зарегистрированные пользователи могут создавать рецепты, управлять подписками и выгружать список покупок в формате TXT.
---

## 🚀 Стек технологий

- **Backend**: Python 3, Django, Django REST Framework  
- **Frontend**: React, JavaScript  
- **База данных**: PostgreSQL  
- **Контейнеризация**: Docker, docker-compose  
- **Веб-сервер**: Nginx  
- **Аутентификация**: Djoser + токены  

---

## 🔧 Как развернуть проект в Docker

1. Клонируйте репозиторий:
   ```bash
   git clone <url вашего репо>
   cd <папка проекта>

2. Создайте файл .env на основе шаблона:
   ```bash
   cp .env.example .env


3. Запустите проект:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build

Миграция и статика включена в docker-compose.prod.yml

4. Создайте суперпользователя:

   ```bash
   docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

После этого проект будет доступен по адресу:
 http://localhost/


Примеры запросов и ответов
 Получение токена авторизации

POST /api/auth/token/login/

Запрос:
   ```bash
   {
    "email": "vpupkin@yandex.ru",
    "password": "Qwerty123"
   }


Ответ:
   ```bash
   {
   "auth_token": "string"
   }


Регистрация пользователя

POST /api/users/

Запрос:
   ```bash
   {
   "email": "vpupkin@yandex.ru",
   "username": "vasya.pupkin",
   "first_name": "Вася",
   "last_name": "Иванов",
   "password": "Qwerty123"
   }


Ответ:
   ```bash
   {
   "email": "vpupkin@yandex.ru",
   "id": 1,
   "username": "vasya.pupkin",
   "first_name": "Вася",
   "last_name": "Иванов"
   }

Список рецептов

GET /api/recipes/?page=1&limit=2

Ответ:
   ```bash
  {
    "count": 123,
    "previous": null,
    "results": [
      {
        "id": 1,
        "tags": [{"id": 1, "name": "Завтрак", "slug": "breakfast"}],
        "author": {"id": 1, "username": "vasya", "email": "vpupkin@yandex.ru"},
        "ingredients": [
          {"id": 1, "name": "Картофель", "measurement_unit": "г", "amount": 100}
        ],
        "is_favorited": false,
        "is_in_shopping_cart": false,
        "name": "Жареная картошка",
        "image": "Путь до изображения",
        "text": "Очень вкусная картошка",
        "cooking_time": 30
      }
    ]
  }

Так же БД можно наполнить подготовленными ингредиентами с помощью файла load_csv.py

 ```bash
cd foodgram/backend
python manage.py load_csv

Автор

Домен проекта сейчас - https://projectfoodgram.ddns.net/recipes
Разработчик: Вячеслав
GitHub: https://github.com/VyacheslavShestakov09