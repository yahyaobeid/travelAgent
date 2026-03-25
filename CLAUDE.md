# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TripHelix is a Django 5.2 travel itinerary generator. Users enter a destination, dates, and preferences; the app calls OpenAI to produce a day-by-day plan and Ticketmaster to surface real events during the trip. Anonymous users can preview itineraries; authenticated users can save, edit, and delete them.

## Commands

All Django management commands use `config/manage.py` — **not** a root-level `manage.py`.

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python config/manage.py runserver

# Run migrations
python config/manage.py migrate

# Run all tests
python config/manage.py test core users

# Run a single test class
python config/manage.py test core.tests.ItineraryCreateViewTests

# Run a single test method
python config/manage.py test core.tests.ItineraryCreateViewTests.test_save_requires_login

# Collect static files
python config/manage.py collectstatic --noinput
```

## Environment Variables

Copy `.env` to the project root (parent of `config/`). Required variables:

| Variable | Description |
|---|---|
| `DJANGO_SECRET` | Django `SECRET_KEY` |
| `DEBUG` | `true` / `false` |
| `POSTGRES_DB` | Database name (default: `triphelix`) |
| `POSTGRES_USER` | DB user (default: `default`) |
| `POSTGRES_PASSWORD` | DB password |
| `POSTGRES_HOST` | DB host (default: `localhost`) |
| `POSTGRES_PORT` | DB port (default: `5432`) |
| `OPENAI_API_KEY` | Required for itinerary generation |
| `OPENAI_MODEL` | Model for itinerary text (default: `gpt-4o-mini`) |
| `OPENAI_DESTINATION_MODEL` | Model for destination parsing (default: `gpt-4o-mini`) |
| `TICKETMASTER_API_KEY` | Optional; event lookup silently disabled if absent |

## Architecture

### Directory Layout

```
config/                  # Django project root (contains manage.py)
  config/                # Django settings package
    settings.py
    urls.py
  core/                  # Main app: itinerary CRUD, OpenAI, Ticketmaster
    models.py
    views.py
    services.py          # OpenAI itinerary generation
    eventbrite.py        # Ticketmaster event fetching + destination parsing
    forms.py
    utils.py             # render_markdown()
    urls.py
  users/                 # Auth app: login/register
  templates/             # HTML templates (BASE_DIR / "templates")
  static/                # Static assets (served by whitenoise)
```

### Key Design Decisions

**OpenAI SDK usage**: The app uses `client.responses.create(model=..., input=[...])` — the newer Responses API, not `chat.completions.create`. Don't switch these.

**Destination normalization** (`eventbrite.py`): When the user enters a multi-city trip, destinations are parsed first via OpenAI (structured JSON output), with a heuristic line-by-line parser as fallback. Both paths produce `Destination` named tuples with per-city date ranges.

**Anonymous preview flow**: Unauthenticated users can generate and preview an itinerary. The result is stored in `request.session[PENDING_SESSION_KEY]`. After login, `save_pending_itinerary` persists it. This avoids hitting the OpenAI API a second time.

**Travel styles**: Four system prompts are defined in `services.py` (`GENERAL_SYSTEM_PROMPT`, `CULTURE_SYSTEM_PROMPT`, `URBAN_SYSTEM_PROMPT`, `ADVENTURE_SYSTEM_PROMPT`) keyed by `Itinerary.STYLE_*` constants. The user-facing prompt is built separately by `_build_prompt()`.

**Markdown rendering** (`utils.py`): `render_markdown()` uses `python-markdown` with `extra` and `sane_lists` extensions. Falls back to a hand-rolled converter if the package is unavailable.

### URL Namespaces

- `core:home`, `core:itinerary_new`, `core:itinerary_preview`, `core:itinerary_save_pending`
- `core:itinerary_detail`, `core:itinerary_edit`, `core:itinerary_delete`
- `users:login`, `users:register`, etc.

### Testing Approach

Tests use Django's `TestCase` with `unittest.mock.patch` to mock `generate_itinerary` and `fetch_events` — external API calls are never made in tests. The test database uses the same PostgreSQL config from the environment (or SQLite if overridden).
