# News Application — Capstone Project

A Django news platform where independent journalists and curated
publications publish articles, editors review and approve them, and
readers subscribe to publishers and/or individual journalists to receive
newsletters and article notifications.

## Contents

- [Design](#design)
- [Roles & permissions](#roles--permissions)
- [Article approval workflow](#article-approval-workflow)
- [Setup](#setup)
- [Running tests](#running-tests)
- [REST API reference](#rest-api-reference)

## Design

### Functional requirements

- Readers can view approved articles and newsletters, and can subscribe to
  publishers and/or individual journalists.
- Journalists can create, view, update, and delete their own articles and
  newsletters.
- Editors can view, update, delete, and **approve** articles and
  newsletters (including ones they didn't write).
- When an editor approves an article, subscribers are emailed and the
  approval is logged to an internal REST endpoint (`/api/approved/`),
  simulating external syndication.
- A RESTful API exposes the same functionality to third-party clients,
  gated by token authentication and role-based authorization.

### Non-functional requirements

- Code follows PEP 8, is modular (views/serializers/permissions/signals
  are separated by concern), and uses defensive coding (form/serializer
  validation, `get_object_or_404`, try/except around external calls such
  as email and the outbound API POST so a network hiccup never breaks the
  approval flow).
- Data is normalised: `Article` and `Newsletter` each store a single
  `author` FK; many-to-many tables (`Publisher.editors`,
  `Publisher.journalists`, `Newsletter.articles`, subscription tables) are
  Django-managed join tables rather than duplicated columns.
- Runs on MariaDB in production/submission; a SQLite toggle
  (`USE_SQLITE=True`) is available for fast local iteration.

### Data model (ERD summary)

```
CustomUser (role: reader | editor | journalist)
 ├─ subscriptions_publishers  M2M──> Publisher      (reader only)
 └─ subscriptions_journalists M2M──> CustomUser      (reader only, self-referential)

Publisher
 ├─ editors      M2M──> CustomUser
 └─ journalists  M2M──> CustomUser

Article
 ├─ author     FK──> CustomUser (role=journalist)
 └─ publisher  FK──> Publisher (nullable — independent article if blank)

Newsletter
 ├─ author    FK──> CustomUser
 └─ articles  M2M──> Article

ApprovedArticleLog
 └─ article  FK──> Article   (one row per approval, POSTed by the signal)
```

## Roles & permissions

Groups and their model permissions on `Article`/`Newsletter` are created
automatically (via a signal + `permissions_utils.get_or_create_role_groups`)
the first time a user is saved, and can also be created up front:

```bash
python manage.py create_groups
```

| Role       | Articles & Newsletters permissions        |
|------------|--------------------------------------------|
| Reader     | view only                                   |
| Editor     | view, change, delete                        |
| Journalist | add, view, change, delete                   |

A user's `role` field automatically places them in the matching Django
`Group`. Reader-only subscription fields (`subscriptions_publishers`,
`subscriptions_journalists`) are cleared whenever a user's role is not
`reader`, per the brief.

## Article approval workflow

Implemented with **Option 1 — Django Signals** (`news/signals.py`):

1. A `pre_save` receiver stashes the article's previous `approved` value.
2. A `post_save` receiver fires only on the `False → True` transition and:
   - emails every reader subscribed to the article's journalist and/or
     publisher (`django.core.mail.send_mail`), and
   - `POST`s the article to this project's own `/api/approved/` endpoint
     using `requests`, which stores an `ApprovedArticleLog` row.

Both the template-based editor approval view (`approve_article`) and the
API's `PATCH /api/articles/<id>/approve/` action simply set
`article.approved = True` and call `.save()` — the signal does the rest,
so the notification logic lives in exactly one place.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then edit .env with real DB/email values

# Create the MariaDB database first, e.g.:
#   CREATE DATABASE news_db CHARACTER SET utf8mb4;
#   CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'news_password';
#   GRANT ALL PRIVILEGES ON news_db.* TO 'news_user'@'localhost';

python manage.py migrate
python manage.py create_groups
python manage.py createsuperuser
python manage.py runserver
```

> **Note on migrations:** `news/migrations/0001_initial.py` was written by
> hand (this sandbox has no network access to install Django and run
> `makemigrations`). It mirrors `news/models.py` exactly, but if your
> Django version's `auth` app migration graph doesn't match the
> `dependencies` entry at the top of that file, delete it and regenerate
> with `python manage.py makemigrations news` before running `migrate`.

To iterate locally without MariaDB installed, set `USE_SQLITE=True` in
`.env` (or the environment) before running `migrate`/`test`.

## Running tests

```bash
python manage.py test
```

Tests live in `news/tests/` and cover:

- `test_models.py` — role → group assignment, subscription field clearing,
  and the approval signal (mocked email/API calls, including a
  regression test that re-saving an already-approved article does not
  refire the notification).
- `test_api.py` — authenticated access per role, the reader
  "subscribed only" endpoint, journalist article creation, editor
  approve/delete, the `/api/approved/` log endpoint, newsletters, and
  token authentication — with both successful and expected-failure
  (403/401/400) cases.

## REST API reference

All endpoints below require `Authorization: Token <token>` unless noted.

| Method | Endpoint                        | Who                     | Notes |
|--------|----------------------------------|--------------------------|-------|
| POST   | `/api/token/`                    | anyone                   | Obtain an auth token |
| GET    | `/api/articles/`                 | any authenticated user   | Approved articles only |
| GET    | `/api/articles/subscribed/`      | readers only             | Approved articles from the reader's subscriptions |
| GET    | `/api/articles/<id>/`            | varies                   | Unapproved articles are only visible to their author or an editor |
| POST   | `/api/articles/`                 | journalists only         | Article is created unapproved |
| PUT/PATCH | `/api/articles/<id>/`         | author-journalist, editor|  |
| DELETE | `/api/articles/<id>/`            | author-journalist, editor|  |
| PATCH  | `/api/articles/<id>/approve/`    | editors only             | Triggers the approval signal |
| GET/POST/PUT/DELETE | `/api/newsletters/` | view: anyone; write: journalist/editor | |
| GET    | `/api/publishers/`               | any authenticated user   | Read-only |
| POST   | `/api/approved/`                 | internal (no auth)       | Called by the approval signal |
| GET    | `/api/approved/`                 | any authenticated user   | View the approval log |

Manual testing with Postman is welcome during development, but the
authoritative test suite is the automated one under `news/tests/`.
