# Care Plan MVP

Minimal runnable version:

- Django monolith
- One frontend page
- One request/queue backend API
- PostgreSQL-backed care plan storage
- Redis queue for asynchronous care plan generation
- Generation status: `pending -> processing -> completed/failed`

## Local Run

```bash
pip install -r requirements.txt
set POSTGRES_DB=careplan
set POSTGRES_USER=careplan
set POSTGRES_PASSWORD=careplan
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Open `http://127.0.0.1:8000/`

## Docker Run

```bash
docker compose up --build
```

Docker starts PostgreSQL on `localhost:5432` and Redis on `localhost:6379`.

TablePlus local connection:

- Host: `localhost`
- Port: `5432`
- Database: `careplan`
- User: `careplan`
- Password: `careplan`

## API

- `POST /api/care-plans/`
- `GET /api/care-plans/<id>/`

`POST /api/care-plans/` stores the request with `status='pending'`, pushes the care plan ID to Redis, and returns immediately with `202 Accepted`.
