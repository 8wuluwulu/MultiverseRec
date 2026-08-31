# 🗺️ MultiverseRec — Roadmap для junior

> Гибридная рекомендательная система книг и фильмов  
> **Стек:** Python · SQLAlchemy · PostgreSQL + pgvector · GigaChat API

---

## Что вообще происходит в этом проекте?

Представь: пользователь пишет "хочу что-то мрачное про будущее". Система:
1. Превращает этот текст в **вектор** (список из 1024 чисел) через GigaChat
2. Ищет в базе данных записи, у которых вектор **максимально похож** на запрос
3. Возвращает смесь книг и фильмов — это и есть "гибридные рекомендации"

---

## Текущее состояние проекта

| Файл | Что там | Статус |
|---|---|---|
| `models/Content.py` | SQLAlchemy-модель (= таблица в БД) | ✅ есть, но нужно поправить |
| `models/Book.py` | Класс книги | ⚠️ нужно переделать |
| `models/Movie.py` | Класс фильма | ⚠️ нужно переделать |
| `core/database.py` | Подключение к Postgres | ✅ готово |
| `core/init_db.py` | Создание таблиц | ✅ готово |
| `core/embedder.py` | Генерация векторов | ⬜ пустой файл |
| `core/searcher.py` | Поиск | ⬜ пустой файл |
| `managers/transaction.py` | Работа с БД | ⬜ пустой файл |
| `managers/model_context.py` | Менеджер нейросети | ⬜ пустой файл |
| `decorators/` | Декораторы | ⬜ пустые файлы |

---

## Этап 1 — Починить то, что есть
> ⏱️ ~1-2 дня

Прежде чем писать новое — нужно разобраться с текущим кодом.

### Проблема 1: неправильный размер вектора

В [`Content.py`](file:///D:/MultiverseRec/src/multiverserec/models/Content.py) сейчас написано:
```python
embedding = Column(Vector(384))
```

Но GigaChat возвращает векторы размером **1024**, а не 384. Если оставить 384 — получишь ошибку при первой записи.

**Исправить на:**
```python
embedding = Column(Vector(1024))
```

> 💡 Что такое вектор? Это просто список чисел. Например `[0.12, -0.44, 0.87, ...]` длиной 1024. Чем ближе два вектора друг к другу математически — тем более похожи тексты, из которых они сгенерированы.

### Проблема 2: Book и Movie не умеют писаться в БД

Сейчас `Book` наследует от `Content`, но сама в БД не маппится — это просто Python-класс. А таблица у нас одна — `content`. Значит `Book` должен **создавать объект Content**, а не быть отдельной сущностью.

**Переделать `Book` в фабрику:**
```python
# models/Book.py
from typing import Optional
from multiverserec.models.Content import Content

class Book:
    @staticmethod
    def create(title: str, author: str, description: str,
               genres: list[str], pages: int,
               rating: Optional[float] = None,
               embedding: Optional[list[float]] = None) -> Content:
        return Content(
            title=title,
            description=description,
            content_type="book",
            rating=rating,
            embedding=embedding,
            meta={
                "author": author,
                "pages": pages,
                "genres": genres,
            }
        )

    @staticmethod
    def get_searchable_text(title: str, author: str, description: str, genres: list[str]) -> str:
        """Текст, который будем превращать в вектор"""
        return f"{title} {author} {description} {' '.join(genres)}"
```

Аналогично переделай `Movie`.

### Написать `managers/transaction.py`

Это **контекстный менеджер** — специальный класс, который используется с `with`. Он автоматически делает commit если всё хорошо, и rollback если что-то сломалось.

> 💡 Зачем это нужно? Без него ты каждый раз пишешь `db.commit()` и `db.close()` вручную, и если забудешь — данные не сохранятся или соединение зависнет.

```python
# managers/transaction.py
from multiverserec.core.database import SessionLocal
from sqlalchemy.orm import Session

class DatabaseTransaction:
    def __enter__(self) -> Session:
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Если было исключение — откатываем изменения
            self.db.rollback()
        else:
            # Всё хорошо — сохраняем
            self.db.commit()
        self.db.close()
```

**Как использовать:**
```python
from multiverserec.managers.transaction import DatabaseTransaction
from multiverserec.models.Book import Book

with DatabaseTransaction() as db:
    book = Book.create(
        title="Дюна",
        author="Фрэнк Херберт",
        description="Эпическая сага о пустынной планете...",
        genres=["фантастика", "эпос"],
        pages=688,
        rating=9.0
    )
    db.add(book)
# После выхода из with — автоматически commit и close
```

### Написать первый скрипт с данными

Создай `scripts/generate_sample_data.py` и добавь туда 5-7 книг и фильмов вручную (без эмбеддингов пока). Это нужно, чтобы убедиться что запись в БД работает.

**Итог этапа:** запускаешь скрипт → проверяешь в pgAdmin или через `psql` что данные появились ✅

---

## Этап 2 — GigaChat API: получить доступ
> ⏱️ ~полдня

Прежде чем писать код — нужно зарегистрироваться и получить ключ.

### Шаги:

1. Идёшь на [developers.sber.ru/studio](https://developers.sber.ru/studio)
2. Регистрируешься
3. Создаёшь новый проект → выбираешь **GigaChat API**
4. Получаешь строку `credentials` — это `Base64(clientId:secretKey)`, выглядит примерно как `ZDk4...длинная строка...`
5. Создаёшь файл `.env` в корне проекта:

```
GIGACHAT_CREDENTIALS=ZDk4...твоя_строка...
GIGACHAT_SCOPE=GIGACHAT_API_PERS
```

> [!WARNING]
> Никогда не коммить `.env` в git! Убедись что он прописан в `.gitignore` — у тебя он уже должен быть там.

6. Устанавливаешь зависимости:
```bash
uv add gigachat python-dotenv
```

---

## Этап 3 — Генерация эмбеддингов (главный этап)
> ⏱️ ~2-3 дня

### Написать `utils/config.py`

Сначала научимся читать `.env` файл:

```python
# utils/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # читает .env файл

GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")

if not GIGACHAT_CREDENTIALS:
    raise ValueError("Не задан GIGACHAT_CREDENTIALS в .env файле!")
```

### Написать `core/embedder.py`

```python
# core/embedder.py
from gigachat import GigaChat
from gigachat.models import EmbeddingsBody
from multiverserec.utils.config import GIGACHAT_CREDENTIALS, GIGACHAT_SCOPE

class GigaChatEmbedder:
    """Класс для генерации векторных представлений текста через GigaChat API"""

    def __init__(self):
        self.credentials = GIGACHAT_CREDENTIALS
        self.scope = GIGACHAT_SCOPE

    def generate(self, text: str) -> list[float]:
        """Превращает один текст в вектор из 1024 чисел"""
        with GigaChat(credentials=self.credentials, scope=self.scope, verify_ssl_certs=False) as client:
            response = client.embeddings(EmbeddingsBody(input=[text], model="Embeddings"))
            return response.data[0].embedding

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Превращает список текстов в список векторов. Быстрее чем вызывать generate() в цикле"""
        with GigaChat(credentials=self.credentials, scope=self.scope, verify_ssl_certs=False) as client:
            response = client.embeddings(EmbeddingsBody(input=texts, model="Embeddings"))
            # Сортируем по индексу, чтобы порядок совпал с порядком входных текстов
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]
```

**Проверка:**
```python
embedder = GigaChatEmbedder()
vector = embedder.generate("Дюна Херберт фантастика")
print(len(vector))   # должно быть 1024
print(vector[:5])    # первые 5 чисел
```

### Написать `managers/model_context.py`

Это контекстный менеджер для embedder-а — чтобы не создавать его заново на каждый запрос:

```python
# managers/model_context.py
from multiverserec.core.embedder import GigaChatEmbedder

class ModelContext:
    """Контекстный менеджер — создаёт embedder один раз и отдаёт его"""

    def __enter__(self) -> GigaChatEmbedder:
        self.embedder = GigaChatEmbedder()
        return self.embedder

    def __exit__(self, *args):
        pass  # ничего закрывать не нужно, GigaChat SDK сам управляет соединением
```

**Использование:**
```python
with ModelContext() as embedder:
    vector = embedder.generate("Гарри Поттер волшебство приключения")
```

### Написать декораторы

> 💡 Декоратор — это функция, которая «оборачивает» другую функцию и добавляет ей поведение. Пишется через `@` перед функцией.

**`decorators/timing.py`** — показывает сколько времени выполняется функция:
```python
import time
import functools

def timing(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"[timing] {func.__name__} выполнился за {elapsed:.2f}с")
        return result
    return wrapper

# Использование:
# @timing
# def generate(...): ...
```

**`decorators/retry.py`** — повторяет при ошибке (нужно для нестабильного API):
```python
import time
import functools

def retry(max_attempts: int = 3, delay: float = 1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise  # последняя попытка — пробрасываем ошибку дальше
                    print(f"[retry] Попытка {attempt} не удалась: {e}. Повтор через {delay}с...")
                    time.sleep(delay)
        return wrapper
    return decorator

# Использование:
# @retry(max_attempts=3, delay=1.0)
# def generate(...): ...
```

**Итог этапа:** `embedder.generate("любой текст")` → список из 1024 чисел ✅

---

## Этап 4 — Загрузка реальных данных
> ⏱️ ~2 дня

### Где взять данные

1. Регистрируешься на [kaggle.com](https://kaggle.com)
2. Скачиваешь два датасета:
   - Книги: [Goodreads Books](https://www.kaggle.com/datasets/jealousleopard/goodreadsbooks) → кладёшь в `data/raw/books.csv`
   - Фильмы: [IMDB Top 1000](https://www.kaggle.com/datasets/harshitshankhdhar/imdb-dataset-of-top-1000-movies-and-tv-shows) → кладёшь в `data/raw/movies.csv`

### Написать `scripts/import_data.py`

```python
import pandas as pd
import time
from multiverserec.managers.model_context import ModelContext
from multiverserec.managers.transaction import DatabaseTransaction
from multiverserec.models.Book import Book

def import_books(filepath: str):
    df = pd.read_csv(filepath).head(500)  # для начала берём первые 500
    
    with ModelContext() as embedder:
        # Генерируем все тексты для эмбеддинга
        texts = []
        for _, row in df.iterrows():
            text = Book.get_searchable_text(
                title=str(row.get("title", "")),
                author=str(row.get("authors", "")),
                description=str(row.get("description", "")),
                genres=[]
            )
            texts.append(text)

        # Батчами по 10 штук (из-за rate limit GigaChat)
        all_embeddings = []
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = embedder.generate_batch(batch)
            all_embeddings.extend(embeddings)
            print(f"Обработано {min(i + batch_size, len(texts))}/{len(texts)}")
            time.sleep(0.5)  # пауза чтобы не превысить rate limit

        # Сохраняем в БД
        with DatabaseTransaction() as db:
            for (_, row), embedding in zip(df.iterrows(), all_embeddings):
                book = Book.create(
                    title=str(row.get("title", "Unknown")),
                    author=str(row.get("authors", "Unknown")),
                    description=str(row.get("description", "")),
                    genres=[],
                    pages=int(row.get("num_pages", 0)),
                    rating=float(row.get("average_rating", 0)) or None,
                    embedding=embedding
                )
                db.add(book)
        
        print(f"Импортировано {len(all_embeddings)} книг!")

if __name__ == "__main__":
    import_books("data/raw/books.csv")
```

> [!WARNING]
> GigaChat имеет ограничение на количество запросов в секунду (rate limit). Если делать запросы слишком часто — получишь ошибку 429. Поэтому добавлен `time.sleep(0.5)` между батчами.

**Итог этапа:** `SELECT COUNT(*) FROM content;` → 500+ строк с заполненным `embedding` ✅

---

## Этап 5 — Поиск
> ⏱️ ~2 дня

> 💡 Как работает векторный поиск? У каждой записи в БД есть вектор. Когда пользователь пишет запрос — мы тоже превращаем его в вектор и ищем те записи, чьи векторы **ближе всего** к запросу. Близость измеряется через "косинусное расстояние".

### Создать индекс (ускоряет поиск в 10-100 раз)

После загрузки всех данных выполни в psql или pgAdmin:
```sql
CREATE INDEX ON content USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

> ⚠️ Создавай индекс **только после** загрузки данных. При пустой или почти пустой таблице он бесполезен.

### Написать `core/searcher.py`

```python
# core/searcher.py
from sqlalchemy import text
from multiverserec.core.database import SessionLocal
from multiverserec.core.embedder import GigaChatEmbedder

class HybridSearcher:
    def __init__(self, embedder: GigaChatEmbedder):
        self.embedder = embedder

    def vector_search(self, query: str, limit: int = 10) -> list[dict]:
        """Поиск по смыслу текста через векторное сравнение"""
        query_vector = self.embedder.generate(query)
        
        db = SessionLocal()
        try:
            sql = text("""
                SELECT id, title, content_type, meta,
                       1 - (embedding <=> :vec) AS similarity
                FROM content
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :vec
                LIMIT :limit
            """)
            result = db.execute(sql, {"vec": str(query_vector), "limit": limit})
            return [dict(row._mapping) for row in result]
        finally:
            db.close()

    def text_search(self, query: str, limit: int = 10) -> list[dict]:
        """Поиск по ключевым словам в названии и описании"""
        db = SessionLocal()
        try:
            sql = text("""
                SELECT id, title, content_type, meta
                FROM content
                WHERE to_tsvector('russian', title || ' ' || COALESCE(description, ''))
                      @@ plainto_tsquery('russian', :query)
                LIMIT :limit
            """)
            result = db.execute(sql, {"query": query, "limit": limit})
            return [dict(row._mapping) for row in result]
        finally:
            db.close()

    def hybrid_search(self, query: str, limit: int = 10) -> list[dict]:
        """Объединяет оба метода, убирает дубликаты"""
        vector_results = self.vector_search(query, limit)
        text_results = self.text_search(query, limit)
        
        # Объединяем, убираем дубликаты по id
        seen_ids = set()
        combined = []
        for item in vector_results + text_results:
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                combined.append(item)
        
        return combined[:limit]
```

**Проверка:**
```python
with ModelContext() as embedder:
    searcher = HybridSearcher(embedder)
    results = searcher.hybrid_search("мрачная антиутопия про будущее")
    for r in results:
        print(r["content_type"], "—", r["title"])
```

**Итог этапа:** поиск работает и возвращает релевантные результаты ✅

---

## Этап 6 — CLI интерфейс
> ⏱️ ~1-2 дня

Устанавливаем библиотеки:
```bash
uv add click rich
```

Пишем `src/multiverserec/cli.py`:
```bash
python cli.py search "космос и одиночество"
python cli.py search "магия" --type book --limit 5
python cli.py import-books data/raw/books.csv
python cli.py status
```

---

## Этап 7 — Логирование
> ⏱️ ~1 день

- [ ] `utils/logger.py` — настроить `logging`, чтобы видеть что происходит в приложении
- [ ] Декоратор `@log_query` — записывает каждый поисковый запрос в таблицу `search_history`
- [ ] Декоратор `@handle_exception` — перехватывает ошибки и красиво их логирует

---

## Этап 8 — Тесты
> ⏱️ ~2 дня

```bash
uv add pytest
```

| Файл | Что тестируем |
|---|---|
| `test_models.py` | `Book.create()` возвращает правильный `Content` с нужными полями в `meta` |
| `test_transaction.py` | данные сохраняются, при ошибке — rollback |
| `test_embedder.py` | **мокируем** GigaChat (не тратим реальные API-запросы), проверяем что наш код правильно обрабатывает ответ |
| `test_search.py` | поиск возвращает непустой список |

> 💡 "Мок" (mock) — это заглушка вместо реального API. Ты говоришь тесту "представь что GigaChat вернул вот этот вектор" — и тест проверяет логику твоего кода без реального обращения в интернет.

---

## Этап 9 — Деплой
> ⏱️ ~1 день

- [ ] Dockerfile для приложения
- [ ] Обновить `docker-compose.yml` — запустить всё через `docker compose up`
- [ ] GitHub Actions — автоматически запускать тесты при каждом `git push`

---

## Общая хронология

```
Неделя 1  │ Этапы 1-3  (починка + GigaChat эмбеддинги)
Неделя 2  │ Этапы 4-5  (загрузка данных + поиск)
Неделя 3  │ Этапы 6-7  (CLI + логирование)
Неделя 4  │ Этапы 8-9  (тесты + деплой)
```

---

## Порядок написания файлов (оптимальный)

```
1. models/Content.py          ← Vector(384) → Vector(1024)
2. models/Book.py             ← переделать в фабрику
3. models/Movie.py            ← переделать в фабрику
4. managers/transaction.py    ← нужен для записи в БД
5. scripts/generate_sample_data.py ← проверяем что БД работает
6. utils/config.py            ← читаем .env
7. core/embedder.py           ← GigaChat интеграция
8. managers/model_context.py  ← обёртка над embedder
9. decorators/timing.py       ← пригодится сразу
10. decorators/retry.py       ← нужен до импорта данных
11. scripts/import_data.py    ← загружаем реальные данные
12. core/searcher.py          ← поиск
13. cli.py                    ← интерфейс
14. tests/                    ← тесты
```

---

> **Следующий шаг прямо сейчас:** открой [`Content.py`](file:///D:/MultiverseRec/src/multiverserec/models/Content.py) и замени `Vector(384)` на `Vector(1024)` — это самое быстрое и важное исправление перед стартом.
