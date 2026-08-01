# Care Plan MVP

Minimal runnable version:

- Django monolith
- One frontend page
- One synchronous backend API
- In-memory storage, no database
- Generation status: `pending -> processing -> completed/failed`

## Local Run

```bash
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:8000
```

Open `http://127.0.0.1:8000/`

## Docker Run

```bash
docker compose up --build
```

## API

- `POST /api/care-plans/`
- `GET /api/care-plans/<id>/`
