
# Foodgram — сервис рецептов

**Foodgram** — это онлайн-сервис для публикации рецептов, подписок на авторов, добавления рецептов в избранное и формирования списка покупок.
Зарегистрированные пользователи могут создавать рецепты, управлять подписками и выгружать список покупок в формате TXT.

---

##  Стек технологий

* **Backend**: Python 3, Django, Django REST Framework
* **Frontend**: React, JavaScript
* **База данных**: PostgreSQL
* **Контейнеризация**: Docker, docker-compose
* **Веб-сервер**: Nginx
* **Аутентификация**: Djoser + токены

---

##  Как развернуть проект в Docker

1. Клонируйте репозиторий:

```
git clone <url вашего репо>
cd <папка проекта>
```

2. Создайте файл `.env` на основе шаблона:

```
cp .env.example .env
```

3. Запустите проект:

```
docker-compose -f docker-compose.prod.yml up -d --build
```

4. Создайте суперпользователя:

```
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

Проект будет доступен по адресу: [http://localhost/](http://localhost/)

---

##  Примеры запросов и ответов

### 1. Получение токена авторизации

POST `/api/auth/token/login/`

**Запрос:**

```
{
  "email": "vpupkin@yandex.ru",
  "password": "Qwerty123"
}
```

**Ответ:**

```
{
  "auth_token": "string"
}
```

---

### 2. Регистрация пользователя

POST `/api/users/`

**Запрос:**

```
{
  "email": "vpupkin@yandex.ru",
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Иванов",
  "password": "Qwerty123"
}
```

**Ответ:**

```
{
  "email": "vpupkin@yandex.ru",
  "id": 1,
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Иванов"
}
```

---

### 3. Получение списка рецептов

GET `/api/recipes/?page=1&limit=2`

**Запрос:**

```
# Замените <your_token> на ваш токен авторизации
curl -X GET "http://localhost/api/recipes/?page=1&limit=2" \
  -H "Authorization: Token <your_token>" \
  -H "Content-Type: application/json"
```

**Ответ:**

```
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
```

---

### 4. Наполнение базы данных ингредиентами

```
cd foodgram/backend
python manage.py load_csv
```

---

##  Автор

* Домен проекта: [https://projectfoodgram.ddns.net/recipes](https://projectfoodgram.ddns.net/recipes)
* Разработчик: Вячеслав
* GitHub: [VyacheslavShestakov09](https://github.com/VyacheslavShestakov09)
