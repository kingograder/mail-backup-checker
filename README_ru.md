# Mail Backup Checker

Мониторинг почтового ящика на наличие уведомлений о резервном копировании с сохранением результатов в SQLite и отправкой SMTP-уведомлений.

## Как работает

1. **IMAP-мониторинг** — программа подключается к почтовому ящику (папка `Backup`) и периодически проверяет новые письма
2. **Парсинг** — из заголовков писем извлекаются: код клиента, имя компьютера, задание, расположение, организация, индекс, статус
3. **SQLite** — результаты сохраняются в базу данных. Дубликаты отфильтровываются по `message_uid`
4. **SMTP-уведомления** — при статусах `error`/`warning` отправляется email на указанные адреса
5. **REST API** — FastAPI предоставляет эндпоинты для просмотра уведомлений, статистики и клиентов

## Установка

Установка uv
```bash
Windows (winget)
winget install astral-sh.uv
```
```bash
Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Установка программы
```bash
git clone https://github.com/kingograder/mail-backup-checker.git
cd mail-backup-checker

# Установка зависимостей
uv sync

# Копирование и настройка переменных окружения
cp .env.example .env
```

## Настройка

Отредактируйте `.env`

## Запуск

```bash
uv run python main.py
```

Приложение доступно по адресу `http://localhost:8000`. Документация API — `http://localhost:8000/docs`.

## API

| Метод | Описание |
|-------|----------|
| `GET /api/notifications` | Список уведомлений с фильтрацией и пагинацией |
| `GET /api/notifications/stats` | Статистика (total, last_24h, last_week, last_month) |
| `GET /api/notifications/{message_uid}` | Уведомление по UID |
| `GET /api/clients` | Список клиентов |
| `GET /api/clients/{code}` | Клиент по коду |

### Параметры фильтрации

- `date_from` / `date_to` — диапазон дат
- `client` — код клиента
- `status` — good / warning / error
- `sort_by` — id, code, machine, task, status, created_at, message_uid
- `sort_order` — asc / desc
- `limit` / `offset` — пагинация
