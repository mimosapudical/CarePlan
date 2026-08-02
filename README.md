# Care Plan MVP

Minimal runnable version:

- Django monolith
- One frontend page
- Celery + Redis for asynchronous care plan generation
- Generation status: `pending -> processing -> completed/failed`
- Frontend does **not** auto-refresh; open the care plan URL yourself to see completion

## Local Run

Terminal 1 (API):

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

Terminal 2 (Celery worker):

```bash
celery -A careplan_mvp worker --loglevel=info
```

Open `http://127.0.0.1:8000/`

## Docker Run

```bash
docker compose up --build
```

Starts `web`, Celery `worker`, PostgreSQL (`localhost:5432`), and Redis (`localhost:6379`).

GCP credentials: Compose mounts your Windows Application Default Credentials into `web`/`worker` and sets `GOOGLE_APPLICATION_CREDENTIALS`. Ensure `.env` has `GCP_PROJECT` / `GCP_LOCATION`, and that you once ran:

```bash
gcloud auth application-default login
```

TablePlus local connection:

- Host: `localhost`
- Port: `5432`
- Database: `careplan`
- User: `careplan`
- Password: `careplan`

## API

- `POST /api/care-plans/`
- `GET /api/care-plans/<id>/`

`POST /api/care-plans/` stores `status='pending'`, enqueues `generate_care_plan_task` via Celery, and returns `202 Accepted` immediately.

The Celery task calls the LLM, retries up to 3 times with exponential backoff on failure, and updates DB status to `processing` → `completed` / `failed`.

## How to verify Celery is working

Watch worker logs:

```bash
docker compose logs -f worker
```

You should see:

1. `celery@... ready.` when the worker starts
2. After form submit: `Task careplans.generate_care_plan[...] received`
3. Then either `succeeded` / `completed`, or retry lines, or final failure

On the page you only get `Received` + `careplan_id` — **no auto update**. Manually open:

`http://127.0.0.1:8000/api/care-plans/<careplan_id>/`

(or use Search → View) to see whether status became `completed`.

Optional learning command (not used by Docker anymore):

```bash
python manage.py process_careplan_queue
```
