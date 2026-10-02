# News Application — Django Capstone Project

A role-based Django news platform that supports independent journalists, curated publishers, editors, newsletters, reader subscriptions, article approval, email notifications, and a REST API.

The project is designed around three user roles:

- **Reader** — reads approved content and manages subscriptions.
- **Journalist** — creates and manages their own articles and newsletters.
- **Editor** — reviews and approves articles, manages publishers/staff, and can manage content created by other users.

The application can run locally with SQLite for development/testing and is configured to use MariaDB/MySQL for the production/submission environment. It can also be run in Docker.

---

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [User Roles and Permissions](#user-roles-and-permissions)
- [Article Approval Workflow](#article-approval-workflow)
- [Data Model](#data-model)
- [Web Application URLs](#web-application-urls)
- [REST API](#rest-api)
- [Authentication](#authentication)
- [Email and Approval Notifications](#email-and-approval-notifications)
- [Environment Configuration](#environment-configuration)
- [Local Installation](#local-installation)
- [Running with SQLite](#running-with-sqlite)
- [Running with MariaDB](#running-with-mariadb)
- [Running with Docker](#running-with-docker)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [Development Notes](#development-notes)

---

## Features

### User management

- Custom Django user model.
- Three application roles:
  - Reader
  - Journalist
  - Editor
- Automatic role-based Django group assignment.
- Reader subscription support for:
  - Publishers
  - Individual journalists
- Reader subscription fields are cleared when a user's role changes away from Reader.
- Django authentication and session login support.
- Public Reader registration through the signup page in the improved version.

### Articles

- Journalists can create articles.
- Articles are initially unapproved.
- Journalists can update and delete their own articles.
- Editors can view, update, delete, and approve articles.
- Readers can view approved articles.
- Journalists can view their own unapproved articles.
- Editors can view unapproved articles while they are being reviewed.
- Articles can optionally belong to a Publisher.
- Independent articles can be created without a Publisher.

### Article approval

- Editors approve articles through the web interface or REST API.
- Approval triggers the application's post-save workflow.
- Subscribers can be notified by email.
- Approved articles are sent to the internal `/api/approved/` endpoint to simulate external syndication.
- Approval events are recorded in `ApprovedArticleLog`.
- The notification workflow is protected against failures from email or HTTP requests.

### Newsletters

- Journalists and Editors can create newsletters.
- Newsletters contain a title, description, author, and a many-to-many collection of articles.
- Journalists can manage their own newsletters.
- Editors can manage newsletters created by any author.
- Readers can view newsletters.

### Publishers

- Editors can create and manage publishers.
- Editors can associate journalists and editors with publishers.
- Publishers can have many journalists and editors.
- Readers can subscribe to publishers.

### REST API

The application includes a Django REST Framework API with:

- Token authentication.
- Session authentication.
- Role-based permissions.
- Article CRUD operations.
- Article approval endpoint.
- Reader-specific subscribed-article endpoint.
- Newsletter endpoints.
- Read-only Publisher endpoint.
- Approved-article logging endpoint.
- Pagination.

---

## Technology Stack

| Technology | Version / Purpose |
|---|---|
| Python | 3.12 in Docker |
| Django | 4.2.30 |
| Django REST Framework | 3.17.2 |
| MariaDB/MySQL | Production/submission database |
| SQLite | Local development/testing option |
| mysqlclient | MariaDB/MySQL database driver |
| Requests | Internal HTTP integration |
| python-dotenv | Environment variable loading |
| Docker | Containerised development/runtime |
| Sphinx | Project documentation |

---

## Project Structure

```text
news_application/
│
├── manage.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .env.example
├── README.md
│
├── news_project/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── news/
│   ├── admin.py
│   ├── api_permissions.py
│   ├── api_urls.py
│   ├── api_views.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── permissions_utils.py
│   ├── serializers.py
│   ├── signals.py
│   ├── urls.py
│   ├── views.py
│   │
│   ├── management/
│   │   └── commands/
│   │       └── create_groups.py
│   │
│   ├── migrations/
│   │   └── 0001_initial.py
│   │
│   ├── templates/
│   │   ├── news/
│   │   └── registration/
│   │
│   └── tests/
│       ├── test_models.py
│       └── test_api.py
│
└── docs/
    └── Sphinx documentation
```

> The local `venv/`, `.git/`, generated Python cache files, database file, environment file, and generated documentation build output should not be included in the Docker image.

---

# User Roles and Permissions

## Reader

Readers can:

- Log in.
- View approved articles.
- View newsletters.
- Subscribe to publishers.
- Subscribe to individual journalists.
- Retrieve articles matching their subscriptions through the API.

Readers cannot:

- Create articles.
- Edit articles.
- Delete articles.
- Approve articles.
- Create newsletters.
- Manage publishers.

---

## Journalist

Journalists can:

- Create articles.
- View their own unapproved articles.
- View approved articles.
- Edit their own articles.
- Delete their own articles.
- Create newsletters.
- Edit their own newsletters.
- Delete their own newsletters.

Journalists cannot:

- Approve articles.
- Edit another journalist's articles.
- Delete another journalist's articles.
- Manage publishers.

---

## Editor

Editors can:

- View all articles, including pending articles.
- Edit articles.
- Delete articles.
- Approve articles.
- Create and manage newsletters.
- Manage publishers.
- Associate journalists and editors with publishers.
- View the approval log.

Editors cannot create articles through the REST API; article creation is restricted to journalists by the API permission rules.

---

# Article Approval Workflow

The application uses Django signals to centralise the approval workflow.

### Workflow

```text
Journalist creates article
          │
          ▼
     approved=False
          │
          ▼
   Article awaits review
          │
          ▼
       Editor
          │
          ▼
   approved=True
          │
          ▼
      post_save signal
       /          \
      /            \
     ▼              ▼
Email subscribers   POST /api/approved/
                    │
                    ▼
             ApprovedArticleLog
```

### Signal behaviour

When an article changes from:

```text
approved=False
```

to:

```text
approved=True
```

the signal:

1. Finds relevant readers.
2. Sends notification emails.
3. Posts the approved article information to `/api/approved/`.
4. Records the approval event in `ApprovedArticleLog`.

The approval workflow is designed so that an email or HTTP failure does not prevent the article from being approved.

Re-saving an article that is already approved does not re-trigger the approval notification.

---

# Data Model

The core models are:

```text
CustomUser
│
├── role
├── subscriptions_publishers ──────► Publisher
└── subscriptions_journalists ─────► CustomUser

Publisher
├── editors ────────────────────────► CustomUser
└── journalists ────────────────────► CustomUser

Article
├── author ─────────────────────────► CustomUser
├── publisher ──────────────────────► Publisher
└── approved

Newsletter
├── author ─────────────────────────► CustomUser
└── articles ───────────────────────► Article

ApprovedArticleLog
└── article ────────────────────────► Article
```

### Normalisation

The application uses Django relationships instead of duplicating relationship data.

Examples:

- `Publisher.editors` is a many-to-many relationship.
- `Publisher.journalists` is a many-to-many relationship.
- `Newsletter.articles` is a many-to-many relationship.
- Reader subscriptions use many-to-many relationships.
- `Article.author` is a foreign key.
- `Newsletter.author` is a foreign key.

---

# Web Application URLs

| URL | Purpose |
|---|---|
| `/` | Article list |
| `/articles/new/` | Create article |
| `/articles/<id>/` | Article detail |
| `/articles/<id>/edit/` | Edit article |
| `/articles/<id>/delete/` | Delete article |
| `/articles/<id>/approve/` | Editor article approval |
| `/newsletters/` | Newsletter list |
| `/newsletters/new/` | Create newsletter |
| `/newsletters/<id>/` | Newsletter detail |
| `/newsletters/<id>/edit/` | Edit newsletter |
| `/newsletters/<id>/delete/` | Delete newsletter |
| `/publishers/manage/` | Editor publisher management |
| `/accounts/login/` | Login |
| `/accounts/logout/` | Logout |
| `/signup/` | Reader registration |
| `/admin/` | Django admin |

### Signup

Public registration should create a user with:

```text
role = reader
```

Users should not be able to select the Editor or Journalist role from public registration.

---

# REST API

The API is available under:

```text
/api/
```

## Authentication

### Obtain token

```http
POST /api/token/
```

Example:

```json
{
    "username": "reader",
    "password": "your-password"
}
```

Successful response:

```json
{
    "token": "your-token"
}
```

Use the token in subsequent requests:

```http
Authorization: Token your-token
```

---

## Article API

### List approved articles

```http
GET /api/articles/
```

Requires authentication.

Returns approved articles.

---

### Retrieve an article

```http
GET /api/articles/<id>/
```

Readers can retrieve approved articles.

Journalists can retrieve their own unapproved articles.

Editors can retrieve unapproved articles for review.

---

### Create an article

```http
POST /api/articles/
```

Journalists only.

Example:

```json
{
    "title": "New News Story",
    "content": "Article content goes here."
}
```

New articles are created with:

```json
{
    "approved": false
}
```

---

### Update an article

```http
PUT /api/articles/<id>/
```

or:

```http
PATCH /api/articles/<id>/
```

Journalists can update their own articles.

Editors can update any article.

---

### Delete an article

```http
DELETE /api/articles/<id>/
```

Journalists can delete their own articles.

Editors can delete any article.

---

### Approve an article

```http
PATCH /api/articles/<id>/approve/
```

Editors only.

Approval triggers the notification and internal syndication workflow.

---

## Reader subscriptions API

```http
GET /api/articles/subscribed/
```

Readers only.

Returns approved articles written by journalists or published by publishers to which the reader is subscribed.

---

## Newsletter API

```http
GET /api/newsletters/
```

Authenticated users can view newsletters.

Journalists and Editors can create, update, and delete newsletters according to ownership/role permissions.

### Create newsletter

```http
POST /api/newsletters/
```

Example:

```json
{
    "title": "Weekly Roundup",
    "description": "This week's top stories.",
    "articles": [1, 2, 3]
}
```

---

## Publisher API

```http
GET /api/publishers/
```

Authenticated users can view publishers.

Publisher API access is read-only.

Publisher management is handled through the editor web interface.

---

## Approved Article Log API

### Internal POST

```http
POST /api/approved/
```

This endpoint receives the approval payload generated by the approval signal.

### View approval logs

```http
GET /api/approved/
```

Requires authentication.

---

# Authentication

The application uses Django authentication together with Django REST Framework authentication.

Configured authentication methods:

```python
TokenAuthentication
SessionAuthentication
```

The normal web interface uses Django sessions.

API clients can use:

```http
Authorization: Token <token>
```

---

# Email and Approval Notifications

During development, email is configured to use Django's console backend by default:

```text
django.core.mail.backends.console.EmailBackend
```

This means email content appears in the terminal instead of being sent to real email addresses.

For production, configure SMTP values through environment variables.

Example:

```env
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=news@example.com
```

---

# Environment Configuration

Copy:

```text
.env.example
```

to:

```text
.env
```

Example:

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*

USE_SQLITE=True

DB_NAME=news_db
DB_USER=news_user
DB_PASSWORD=news_password
DB_HOST=127.0.0.1
DB_PORT=3306

DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=news@example.com

INTERNAL_API_BASE_URL=http://127.0.0.1:8000
```

Never commit a real `.env` file or production secret values to Git.

---

# Local Installation

## 1. Create a virtual environment

### Windows PowerShell

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configure the environment

For a quick local setup, use SQLite:

```env
USE_SQLITE=True
```

---

## 4. Apply migrations

```bash
python manage.py migrate
```

---

## 5. Create application groups

```bash
python manage.py create_groups
```

This creates:

```text
Reader
Editor
Journalist
```

---

## 6. Create an administrator

```bash
python manage.py createsuperuser
```

---

## 7. Start Django

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

# Running with SQLite

SQLite is useful for:

- Local development
- Automated tests
- Quick demonstrations
- Environments where MariaDB is not available

Set:

```env
USE_SQLITE=True
```

Then:

```bash
python manage.py migrate
python manage.py create_groups
python manage.py runserver
```

---

# Running with MariaDB

For the intended production/submission configuration, use MariaDB/MySQL.

Create a database, for example:

```sql
CREATE DATABASE news_db CHARACTER SET utf8mb4;
```

Create a user:

```sql
CREATE USER 'news_user'@'localhost'
IDENTIFIED BY 'news_password';
```

Grant access:

```sql
GRANT ALL PRIVILEGES ON news_db.*
TO 'news_user'@'localhost';
```

Then configure:

```env
USE_SQLITE=False
DB_NAME=news_db
DB_USER=news_user
DB_PASSWORD=news_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

Run:

```bash
python manage.py migrate
python manage.py create_groups
python manage.py createsuperuser
python manage.py runserver
```

---

# Running with Docker

The project includes a Dockerfile based on:

```text
python:3.12-slim
```

The image installs the dependencies from `requirements.txt`, copies the project into `/app`, runs migrations, creates the role groups, and starts Django on port `8000`.

## Build the image

From the project directory:

```powershell
docker build -t news_application .
```

## Run the container

```powershell
docker run -p 8000:8000 news_application
```

Open:

```text
http://localhost:8000/
```

The Docker configuration defaults to SQLite so the application can start without a separate MariaDB container.

---

## Docker development cycle

Whenever Python/Django source files are changed:

```powershell
docker build -t news_application .
```

Then stop the old container and run the new image:

```powershell
docker run -p 8000:8000 news_application
```

### Recommended named-container workflow

Using a name makes it easier to stop and restart the application:

```powershell
docker run --name news_application_container -p 8000:8000 news_application
```

Stop it:

```powershell
docker stop news_application_container
```

Remove it:

```powershell
docker rm news_application_container
```

Then start a new container:

```powershell
docker run --name news_application_container -p 8000:8000 news_application
```

---

# Testing

Run the complete test suite:

```bash
python manage.py test
```

The test suite is located in:

```text
news/tests/
```

## Model tests

`test_models.py` covers areas including:

- Role assignment.
- Django group assignment.
- Reader subscription handling.
- Clearing reader-only subscription fields.
- Article approval behaviour.
- Approval notification behaviour.
- Regression coverage to ensure an already-approved article does not repeatedly trigger approval notifications.

## API tests

`test_api.py` covers:

- Authentication.
- Token creation.
- Invalid authentication.
- Approved article listing.
- Reader subscription filtering.
- Article creation.
- Article update/delete permissions.
- Article approval.
- Reader access restrictions.
- Journalist access restrictions.
- Editor access.
- Newsletter access.
- Publisher access.
- Approved article logging.
- Expected `401`, `403`, and `400` responses.

---

# Troubleshooting

## `NoReverseMatch: Reverse for 'signup' not found`

If the homepage produces:

```text
django.urls.exceptions.NoReverseMatch:
Reverse for 'signup' not found.
```

the template is trying to use:

```django
{% url 'signup' %}
```

but Django cannot find a URL named `signup`.

Make sure the improved signup implementation contains:

```python
path('signup/', views.signup, name='signup')
```

and that `views.py` contains a matching `signup()` view.

The signup form should also be imported into `views.py`.

---

## `port is already allocated`

If Docker reports:

```text
Bind for 0.0.0.0:8000 failed:
port is already allocated
```

another container or application is already using port `8000`.

Check running containers:

```powershell
docker ps
```

Stop the container using the port:

```powershell
docker stop <CONTAINER_ID>
```

Then run:

```powershell
docker run -p 8000:8000 news_application
```

Alternatively, use another host port:

```powershell
docker run -p 8001:8000 news_application
```

Then open:

```text
http://localhost:8001/
```

---

## Check all Docker containers

Running containers:

```powershell
docker ps
```

All containers, including stopped containers:

```powershell
docker ps -a
```

---

## Docker image changes are not appearing

If your source code changed but the container still behaves as before, rebuild the image:

```powershell
docker build -t news_application .
```

Then create a new container:

```powershell
docker run -p 8000:8000 news_application
```

---

## Migration problems

Run:

```bash
python manage.py makemigrations
python manage.py migrate
```

Check migration status:

```bash
python manage.py showmigrations
```

The project includes an initial migration for the `news` application.

---

## Django system check

Before running the server, check the project:

```bash
python manage.py check
```

A healthy configuration should report:

```text
System check identified no issues
```

---

# Important Code Improvements

The latest development fixes include the following areas.

## Signup URL and view

The navigation references:

```django
{% url 'signup' %}
```

so the project must provide a matching:

```python
path('signup/', views.signup, name='signup')
```

The public signup flow should create Reader accounts only.

---

## Article list response

The article list view must always return an HTTP response.

The final rendering should occur outside the role-specific conditional branches:

```python
return render(
    request,
    'news/article_list.html',
    {'articles': articles}
)
```

This prevents the view from returning `None` for Editors and Journalists.

---

## Article form

`ArticleForm` must use the `Article` model:

```python
class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
```

It must not accidentally use the `Publisher` model.

---

# Code Quality

The application follows a modular Django structure:

- `models.py` — database models.
- `views.py` — web views.
- `forms.py` — HTML forms.
- `serializers.py` — REST API serialization.
- `api_views.py` — REST API endpoints.
- `api_permissions.py` — API permissions.
- `permissions_utils.py` — role/group utilities.
- `signals.py` — approval notifications and integration.
- `tests/` — automated tests.
- `management/commands/` — application management commands.

The application also uses:

- `get_object_or_404()`
- Django login protection.
- DRF permission classes.
- Form and serializer validation.
- Role-based access control.
- Defensive handling around external email/HTTP operations.

---

# Development Notes

## Create groups manually

```bash
python manage.py create_groups
```

## Create a superuser

```bash
python manage.py createsuperuser
```

## Check Django configuration

```bash
python manage.py check
```

## Run migrations

```bash
python manage.py migrate
```

## Run tests

```bash
python manage.py test
```

## Start development server

```bash
python manage.py runserver
```

---

# Admin Interface

The Django admin interface is available at:

```text
/admin/
```

A superuser can use the admin interface to manage:

- Users
- Groups
- Articles
- Publishers
- Newsletters
- Approval logs

---

# API Testing with Postman

The API can be tested with Postman or another REST client.

A typical workflow is:

1. Create or use a test user.
2. Request a token:

```http
POST /api/token/
```

3. Copy the returned token.
4. Add the header:

```http
Authorization: Token <token>
```

5. Test the endpoints according to the user's role.
6. Verify expected success and permission-denied responses.

The automated Django test suite remains the authoritative regression test.

---

# Deployment Considerations

Before production deployment:

- Set `DJANGO_DEBUG=False`.
- Generate a strong `DJANGO_SECRET_KEY`.
- Restrict `DJANGO_ALLOWED_HOSTS`.
- Use MariaDB/MySQL rather than SQLite.
- Configure a real SMTP email provider.
- Store secrets in environment variables.
- Use HTTPS.
- Do not expose development-only settings.
- Review API permissions.
- Run the complete test suite.
- Run:

```bash
python manage.py check --deploy
```

---

# License

This project was created as a Django capstone/learning project.

Add an appropriate open-source license here if the project is intended for public distribution.
