# Bond Search Tool — Контекст проекта

## Обзор проекта

Сервис автоматизированного подбора выгодных облигаций с использованием данных Московской Биржи (MOEX). Проект состоит из трёх взаимосвязанных компонентов:

- **fast_app** — FastAPI приложение для представления данных и взаимодействия с пользователем через HTTP API и веб-интерфейс
- **moex_app** — aiohttp приложение для еженедельного сбора актуальных данных об облигациях из MOEX API
- **db** — PostgreSQL база данных для хранения информации об облигациях

## Архитектура

Проект реализован по принципам **луковой архитектуры** с разделением на слои:

```
src/
├── bond_screener_api/     # FastAPI слой (presentation)
│   ├── main.py           # Точка входа, роуты
│   ├── dependencies.py   # DI для сервисов
│   └── routers.py        # API роутеры
├── moex_app/             # MOEX сборщик данных (external integration)
│   └── main.py          # Планировщик задач
├── services/            # Бизнес-логика
│   ├── moex.py         # Стратегии работы с MOEX API
│   ├── fastapi.py      # FastAPI сервисы
│   └── task_manager.py # Планировщик задач
├── repositories/        # Слой доступа к данным
│   └── bond.py         # Репозиторий для работы с облигациями
├── models/             # SQLAlchemy модели
│   └── bond.py        # Модель MoexBonds
├── schemas/           # Pydantic схемы
│   └── bond.py       # Схемы для валидации данных
└── database/          # Конфигурация БД
    └── base.py       # Session factory
```

## Технологии

- **Python 3.10**
- **FastAPI 0.109** — REST API
- **aiohttp 3.9** — Асинхронный HTTP-клиент для MOEX API
- **SQLAlchemy 2.0** — ORM
- **Alembic 1.13** — Миграции БД
- **PostgreSQL 14.7** — База данных
- **Pydantic 2.6** — Валидация данных
- **Docker & Docker Compose** — Контейнеризация
- **Bootstrap 5.3** — Frontend

## Сборка и запуск

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
POSTGRES_DB=moex
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

### Запуск через Docker Compose

```bash
# Сборка контейнеров
docker-compose build

# Запуск всех сервисов
docker-compose up

# Запуск в фоновом режиме
docker-compose up -d
```

### Сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| `db` | 5433:5432 | PostgreSQL |
| `fast_app` | 8000:8000 | FastAPI приложение |
| `moex_app` | — | Сборщик данных MOEX |

### Миграции БД

```bash
# Применить миграции
alembic upgrade head

# Создать новую миграцию
alembic revision --autogenerate -m "description"

# Откатить миграцию
alembic downgrade -1
```

### Локальная разработка

```bash
# Установка зависимостей FastAPI
pip install -r requirements/fastapi_app.txt

# Установка зависимостей moex_app
pip install -r requirements/moex_app.txt

# Запуск FastAPI
python src/bond_screener_api/main.py

# Запуск сборщика MOEX
python src/moex_app/main.py
```

## API Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Приветственное сообщение |
| GET | `/bonds` | Получить данные об облигациях (JSON) |
| GET | `/view_bonds` | Веб-интерфейс с фильтрами |

### Параметры фильтрации `/view_bonds`

- `max_year_percent` / `min_year_percent` — Диапазон годовой доходности
- `max_list_level` / `min_list_level` — Уровень листинга
- `amortizations` — Облигации с амортизацией
- `floater` — Облигации с плавающим купоном
- `ofz_bonds` — Только ОФЗ
- `max_days_to_redemption` / `min_days_to_redemption` — Дней до погашения

## Модель данных

Таблица `bonds` содержит следующую информацию:

- **Идентификация**: `secid`, `shortname`, `isin`
- **Параметры**: `face_value`, `face_unit`, `list_level`, `matdate`
- **Купоны**: `coupon_frequency`, `coupon_date`, `coupon_percent`, `coupon_value`
- **Доходность**: `price`, `moex_yield`, `year_percent`, `accint` (НКД)
- **Риски**: `highrisk`, `amortizations`, `floater`
- **Тип**: `type` (ofi_bond, corporate_bond, municipal_bond, ofz_bond, и т.д.)

## Практики разработки

### Код-стайл

- Используется **Ruff** для линтинга (настроен в alembic.ini для миграций)
- Типизация через **type hints** и **Pydantic модели**
- Асинхронный код для HTTP-запросов

### Тестирование

- Тесты не обнаружены в репозитории
- Рекомендуется добавить pytest для покрытия критической логики

### Вклад в проект

1. Следовать структуре слоёв (services → repositories → models)
2. Использовать Pydantic схемы для валидации входящих/исходящих данных
3. Новые миграции создавать через Alembic
4. Логирование через `logging` модуль

## Примечания

- MOEX API не требует аутентификации
- Сбор данных происходит еженедельно по будням в 00:00
- В docker-compose.yaml указан volume для сохранения данных PostgreSQL: `/home/user/Project/data:/var/lib/postgresql/data` (требуется замена на актуальный путь)
- Frontend использует Jinja2 шаблоны с Bootstrap 5
