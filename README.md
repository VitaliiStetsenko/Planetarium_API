# 🪐 Planetarium API

A Django REST Framework API for browsing astronomy shows and booking seats in a planetarium — think of it as a mini "movie theater" backend, but for space shows. 🌌

> 🇷🇺 Русская версия ниже: [перейти к описанию на русском](#-планетарий-api)

---

## 🚀 Tech Stack

| Layer | Tool |
|---|---|
| 🐍 Language | Python, Django 6.1 |
| 🔌 API | Django REST Framework |
| 🔑 Auth | JWT (`djangorestframework-simplejwt`) |
| 🗄️ Database | PostgreSQL |
| 📦 Containers | Docker + docker-compose |
| 📖 Docs | drf-spectacular (Swagger UI + Redoc) |
| 🐞 Debugging | django-debug-toolbar |

---

## ✨ What's inside

- 🎬 **Astronomy Shows** — title, description, themes, cover image
- 🎨 **Show Themes** — tag shows by topic (e.g. "Planets", "Deep Space")
- 🏛️ **Planetarium Domes** — rows/seats configuration, auto-calculated `capacity`
- 🗓️ **Show Sessions** — a show scheduled in a dome at a specific time
- 🎟️ **Reservations & Tickets** — book one or more seats in a single atomic request
- 🔍 **Custom search & filtering** (see table below)
- 🖼️ **Image upload** endpoint for astronomy shows
- 🧮 **Live seat availability** — `tickets_available` is calculated on the fly (`capacity - booked seats`), no manual syncing needed
- ⚡ **Query optimization** — `select_related` / `prefetch_related` everywhere that matters, to avoid N+1 queries
- 🚦 **Rate limiting** — 100 req/min for anonymous users, 200 req/min for authenticated ones
- 📄 **Pagination** — 5 items per page by default, configurable up to 20

---

## 🔍 Search & Filtering

| Endpoint | Query param | What it does |
|---|---|---|
| `GET /astronomy_show/` | `theme` | Filter by one or several theme IDs, comma-separated (`?theme=1,2`) |
| `GET /astronomy_show/` | `title` | Case-insensitive partial match on the title |
| `GET /show_session/` | `theme` | Filter sessions by the theme of their astronomy show |
| `GET /show_session/` | `title` | Case-insensitive partial match on the astronomy show's title |
| `GET /show_session/` | `planetarium_dome` | Case-insensitive partial match on the dome's name |
| `GET /show_session/` | `date` | Only sessions happening on this exact date (`YYYY-MM-DD`) |

All filters are combinable — e.g. `?theme=1&date=2026-09-05` narrows down to one theme on one day.

---

## 🔐 Who can do what

Two custom permission classes drive access control:

- **`AdminAllOrReadOnly`** — anyone can read, only **staff** can write. Used on themes, shows, domes and sessions (basically, the "catalog" side of the API — content only admins should curate).
- **`AdminAllAuthenticatedReadPostDelete`** — read/create/cancel is open to any **logged-in** user, but editing (`PUT`/`PATCH`) is **staff-only**. Used on reservations (customers book and cancel their own tickets, but can't "edit" a booking after the fact — you cancel and rebook instead).

| Endpoint | 🌐 Anonymous | 👤 Authenticated user | 🛡️ Staff |
|---|---|---|---|
| `show_theme/` | Read | Read | Read + Write + Delete |
| `astronomy_show/` | Read | Read | Read + Write + Delete + Upload image |
| `planetarium_dome/` | Read | Read | Read + Write |
| `show_session/` | Read | Read | Read + Write + Delete |
| `reservation/` | ❌ No access | Read *(own only)* + Create + Cancel *(own only)* | Read/Create/Cancel/Edit *(all users' reservations)* |
| `user/register/` | ✅ Open (sign up) | ✅ Open | ✅ Open |
| `user/token/` (login) | ✅ Open | ✅ Open | ✅ Open |
| `user/me/` | ❌ No access | Read + Update *(own profile only)* | Read + Update *(own profile only)* |

📌 A regular user's `reservation/` list only ever shows **their own** bookings — staff see everyone's.

---

## 🗺️ Endpoint map

```
/api/user/register/          POST         create an account
/api/user/token/             POST         obtain access + refresh JWT
/api/user/token/refresh/     POST         refresh an access token
/api/user/token/verify/      POST         verify a token is still valid
/api/user/me/                GET, PUT/PATCH   view / edit your own profile

/api/planetarium/show_theme/          CRUD
/api/planetarium/astronomy_show/      CRUD  (+ ?theme=, ?title=)
/api/planetarium/astronomy_show/{id}/upload_image/   POST  (staff only)
/api/planetarium/planetarium_dome/    CRUD
/api/planetarium/show_session/        CRUD  (+ ?theme=, ?title=, ?planetarium_dome=, ?date=)
/api/planetarium/reservation/         list / create / cancel

/api/schema/swagger-ui/      interactive API docs
/api/schema/redoc/           alternative API docs
```

---

## ⚙️ Running the project

```bash
git clone <this-repo>
cd PlanetariumApp
cp .env.example .env   # fill in your own DB credentials
docker-compose up --build
```

The API will be available at `http://127.0.0.1:8001/`, Swagger docs at `/api/schema/swagger-ui/`.

The user to login: email: user@gmail.com, password: testuser1337

To fill the database with a couple of sample records for every endpoint:

```bash
docker-compose exec planetarium python manage.py seed_demo_data
```

---
---

# 🪐 Планетарий API

API на Django REST Framework для просмотра космических шоу и бронирования мест в планетарии — по сути, бэкенд для "кинотеатра", только про космос. 🌌

---

## 🚀 Стек технологий

| Слой | Инструмент |
|---|---|
| 🐍 Язык | Python, Django 6.1 |
| 🔌 API | Django REST Framework |
| 🔑 Авторизация | JWT (`djangorestframework-simplejwt`) |
| 🗄️ База данных | PostgreSQL |
| 📦 Контейнеры | Docker + docker-compose |
| 📖 Документация | drf-spectacular (Swagger UI + Redoc) |
| 🐞 Отладка | django-debug-toolbar |

---

## ✨ Что внутри

- 🎬 **Космические шоу** — название, описание, темы, обложка
- 🎨 **Темы шоу** — тегирование шоу по теме (например, "Планеты", "Дальний космос")
- 🏛️ **Планетарии** — конфигурация рядов/мест, автоматически рассчитываемая `capacity`
- 🗓️ **Сеансы** — конкретное шоу в конкретном планетарии в конкретное время
- 🎟️ **Брони и билеты** — бронирование сразу нескольких мест одним атомарным запросом
- 🔍 **Кастомный поиск и фильтрация** (см. таблицу ниже)
- 🖼️ **Загрузка изображений** для космических шоу
- 🧮 **Живой подсчёт свободных мест** — `tickets_available` считается на лету (`вместимость - забронированные места`), не требует ручной синхронизации
- ⚡ **Оптимизация запросов** — `select_related` / `prefetch_related` там, где это важно, чтобы избежать проблемы N+1 запросов
- 🚦 **Rate limiting** — 100 запросов/мин для анонимов, 200 запросов/мин для авторизованных
- 📄 **Пагинация** — по умолчанию 5 элементов на странице, настраивается до 20

---

## 🔍 Поиск и фильтрация

| Эндпоинт | Query-параметр | Что делает                                                        |
|---|---|-------------------------------------------------------------------|
| `GET /astronomy_show/` | `theme` | Фильтр по одной или нескольким темам через запятую (`?theme=1,2`) |
| `GET /astronomy_show/` | `title` | Частичное совпадение по названию, без учёта регистра              |
| `GET /show_session/` | `theme` | Фильтр сеансов по теме шоу                                        |
| `GET /show_session/` | `title` | Частичное совпадение по названию шоу                              |
| `GET /show_session/` | `planetarium_dome` | Частичное совпадение по названию планетария                       |
| `GET /show_session/` | `date` | Только сеансы в конкретную дату (`YYYY-MM-DD`)                    |

Все фильтры можно комбинировать — например, `?theme=1&date=2026-09-05` сузит выборку до одной темы за один день.

---

## 🔐 Кто что может делать

За доступ отвечают два кастомных класса прав:

- **`AdminAllOrReadOnly`** — читать может кто угодно, писать — только **staff**. Используется на темах, шоу, куполах и сеансах (по сути, "каталожная" часть API — контент, который должны курировать только админы).
- **`AdminAllAuthenticatedReadPostDelete`** — читать/создавать/отменять может любой **залогиненный** пользователь, а редактировать (`PUT`/`PATCH`) — только **staff**. Используется на бронях (покупатель бронирует и отменяет свои билеты, но не может "отредактировать" бронь задним числом — только отменить и забронировать заново).

| Эндпоинт | 🌐 Аноним | 👤 Авторизованный | 🛡️ Staff |
|---|---|---|---|
| `show_theme/` | Чтение | Чтение | Чтение + запись + удаление |
| `astronomy_show/` | Чтение | Чтение | Чтение + запись + удаление + загрузка изображения |
| `planetarium_dome/` | Чтение | Чтение | Чтение + запись + удаление |
| `show_session/` | Чтение | Чтение | Чтение + запись + удаление |
| `reservation/` | ❌ Нет доступа | Чтение *(только своих)* + создание + отмена *(только своих)* | Чтение/создание/отмена/редактирование *(броней всех пользователей)* |
| `user/register/` | ✅ Открыт (регистрация) | ✅ Открыт | ✅ Открыт |
| `user/token/` (логин) | ✅ Открыт | ✅ Открыт | ✅ Открыт |
| `user/me/` | ❌ Нет доступа | Чтение + изменение *(только своего профиля)* | Чтение + изменение *(только своего профиля)* |

📌 В списке `reservation/` обычный пользователь видит только **свои** брони — staff видит брони всех.

---

## 🗺️ Карта эндпоинтов

```
/api/user/register/          POST         регистрация аккаунта
/api/user/token/             POST         получить access + refresh JWT
/api/user/token/refresh/     POST         обновить access-токен
/api/user/token/verify/      POST         проверить валидность токена
/api/user/me/                GET, PUT/PATCH   просмотр / редактирование своего профиля

/api/planetarium/show_theme/          CRUD
/api/planetarium/astronomy_show/      CRUD  (+ ?theme=, ?title=)
/api/planetarium/astronomy_show/{id}/upload_image/   POST  (только staff)
/api/planetarium/planetarium_dome/    CRUD
/api/planetarium/show_session/        CRUD  (+ ?theme=, ?title=, ?planetarium_dome=, ?date=)
/api/planetarium/reservation/         список / создание / отмена

/api/schema/swagger-ui/      интерактивная документация API
/api/schema/redoc/           альтернативная документация API
```

---

## ⚙️ Запуск проекта

```bash
git clone <ссылка-на-репозиторий>
cd PlanetariumApp
cp .env.example .env   # укажите свои данные для подключения к БД
docker-compose up --build
```

API будет доступен по адресу `http://127.0.0.1:8001/`, документация Swagger — по `/api/schema/swagger-ui/`.

Пользователь для логина: email: user@gmail.com, password: testuser1337

Чтобы наполнить базу парой демонстрационных записей на каждый эндпоинт:

```bash
docker-compose exec planetarium python manage.py seed_demo_data
```