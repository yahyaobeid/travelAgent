# TripHelix — Replit Setup

TripHelix is an AI-powered travel itinerary generator built with Django 5.2 (backend) and React + Vite (frontend).

## Architecture

- **Backend**: Django 5.2 + Django REST Framework, served on `localhost:8000`
- **Frontend**: React 18 + TypeScript + Vite dev server, served on `0.0.0.0:5000` (webview)
- **Database**: Replit PostgreSQL (credentials via `PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`)
- **AI**: OpenAI API (requires `OPENAI_API_KEY` secret)
- **Events**: Ticketmaster API (optional, `TICKETMASTER_API_KEY`)

## Project Layout

```
config/              # Django project root (contains manage.py)
  config/            # Django settings package (settings.py, urls.py)
  core/              # Main app: itinerary CRUD, OpenAI, Ticketmaster
  api/               # REST API views (auth, etc.)
  users/             # Auth app
  itinerary/         # Itinerary API app
  flights/           # Flights app
  cars/              # Car rentals app
  templates/         # Django HTML templates
frontend/            # React + Vite SPA
  src/
    api/             # Typed API clients
    components/      # Reusable UI components
    pages/           # Route-level page components
    contexts/        # React context (auth, etc.)
```

## Workflows

- **Start application** — `cd frontend && npm run dev` on port 5000 (webview)
- **Backend** — `python config/manage.py runserver localhost:8000` (console)

The Vite dev server proxies `/api` requests to the Django backend on port 8000.

## Environment Variables

Set in Replit Secrets/Env Vars:

| Variable | Description |
|---|---|
| `DJANGO_SECRET` | Django SECRET_KEY |
| `DEBUG` | `true` / `false` |
| `POSTGRES_DB` / `PGDATABASE` | Database name |
| `POSTGRES_USER` / `PGUSER` | DB user |
| `POSTGRES_PASSWORD` / `PGPASSWORD` | DB password |
| `POSTGRES_HOST` / `PGHOST` | DB host |
| `POSTGRES_PORT` / `PGPORT` | DB port |
| `OPENAI_API_KEY` | Required for itinerary generation |
| `TICKETMASTER_API_KEY` | Optional; events disabled if absent |

## Django Management Commands

```bash
python config/manage.py migrate
python config/manage.py runserver localhost:8000
python config/manage.py collectstatic --noinput
python config/manage.py createsuperuser
```

## Deployment

Production uses gunicorn serving the Django app on port 5000.
The React SPA is built (`npm run build`) and served as static files via WhiteNoise.
Build command: `cd frontend && npm install && npm run build && python config/manage.py collectstatic --noinput && python config/manage.py migrate`
Run command: `gunicorn --bind=0.0.0.0:5000 --reuse-port --chdir=config config.wsgi:application`
