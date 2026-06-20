# Mail Backup Checker

Monitoring a mail.ru mailbox for backup notifications with SQLite storage and SMTP alerts.

## How it works

1. **IMAP monitoring** — connects to a mail.ru mailbox (folder `Backup`) and periodically checks for new emails
2. **Parsing** — extracts from email headers: client code, machine name, task, location, organization, index, status
3. **SQLite** — stores results in a database. Duplicates are filtered by `message_uid`
4. **SMTP notifications** — on `error`/`warning` statuses, sends email to configured recipients
5. **REST API** — FastAPI provides endpoints for viewing notifications, stats, and clients

## Installation

Install uv
```bash
# Windows (winget)
winget install astral-sh.uv
```
```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install the program
```bash
git clone https://github.com/kingograder/mail-backup-checker.git
cd mail-backup-checker

# Install dependencies
uv sync

# Copy and configure environment variables
cp .env.example .env
```

## Configuration

Edit `.env`

## Running

```bash
uv run python main.py
```

The app is available at `http://localhost:8000`. API docs — `http://localhost:8000/docs`.

## API

| Method | Description |
|--------|-------------|
| `GET /api/notifications` | List notifications with filtering and pagination |
| `GET /api/notifications/stats` | Statistics (total, last_24h, last_week, last_month) |
| `GET /api/notifications/{message_uid}` | Get notification by UID |
| `GET /api/clients` | List clients |
| `GET /api/clients/{code}` | Get client by code |

### Filter parameters

- `date_from` / `date_to` — date range
- `client` — client code
- `status` — good / warning / error
- `sort_by` — id, code, machine, task, status, created_at, message_uid
- `sort_order` — asc / desc
- `limit` / `offset` — pagination
