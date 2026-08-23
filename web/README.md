# CarePlan web

Next.js App Router product interface and Node.js backend-for-frontend for the existing Django CarePlan API.

```bash
cp .env.example .env.local
npm ci
npm run dev
```

The interface runs at `http://127.0.0.1:3000`. `DJANGO_API_BASE_URL` defaults to `http://127.0.0.1:8000`; Docker Compose sets it to `http://web:8000`.

The browser uses same-origin `/api/care-plans` routes. Node route handlers forward to Django, validate successful JSON with Zod, preserve upstream status codes, and return downloads without exposing the Django service URL.

Quality checks:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```
