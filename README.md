# CVevo

CVevo is a Django-based resume and recruitment platform designed for job seekers, HR teams, and administrators. It combines resume management, ATS-style analysis, job post management, candidate ranking, notifications, and a custom frontend experience in one application.

## Overview

The platform is built around three main user roles:

- Job seekers can build, upload, parse, review, and analyze resumes.
- HR users can create job posts, upload candidate resumes in bulk, and review candidate rankings.
- Administrators can manage users, jobs, resumes, ATS results, contact messages, and support requests.

The project includes a REST API, server-rendered views, a decoupled frontend template structure, and Tailwind-based asset builds.

## Key Features

- Role-based authentication for job seekers, HR users, and admins
- Email-based sign-in with Google social login support
- Resume upload, parsing, and structured profile storage
- ATS scoring and keyword matching against job requirements
- Quick analysis and general resume analysis workflows
- Resume builder with template selection and DOCX export
- HR job posting and candidate management tools
- Candidate ranking and status updates for applications
- Notification system and support/contact message handling
- Custom Django admin styling with Jazzmin

## Tech Stack

- Backend: Django
- API: Django REST Framework
- Authentication: django-allauth
- Database: PostgreSQL
- Admin UI: Jazzmin
- Frontend: HTML, CSS, JavaScript, Tailwind CSS
- File handling: media uploads for resumes and profile images

## Project Structure

- `cvevo/` - Django project configuration, settings, and root URLs
- `core/` - main application with models, views, API endpoints, serializers, utilities, and migrations
- `frontend/` - templates, pages, partials, assets, and custom frontend scripts/styles
- `ai_nlp/` - resume parsing and scoring helpers used by the analysis pipeline
- `media/` - uploaded files such as resumes and profile images

## Requirements

- Python 3
- Node.js and npm
- PostgreSQL

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Sirson39/CVevo.git
cd CVevo
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Python dependencies

Install the packages required by the Django project:

```bash
pip install django djangorestframework django-cors-headers django-allauth jazzmin psycopg2-binary pillow python-docx
```

If your local environment uses additional packages, install them as needed.

### 4. Install frontend dependencies

```bash
npm install
```

### 5. Configure the database

Update `cvevo/settings.py` with your PostgreSQL credentials, or switch to environment variables for local and production use.

### 6. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

### 8. Start the development server

```bash
python manage.py runserver
```

Open the app in your browser at `http://127.0.0.1:8000/`.

## Tailwind CSS Build

The project includes Tailwind build scripts in `package.json`.

```bash
npm run build:css
```

For continuous development:

```bash
npm run watch:css
```

## Environment Variables

Google sign-in support is enabled through optional environment variables:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_CLIENT_KEY`

If these are not set, Google social login configuration is skipped.

## Main Endpoints

- `/` - public home page
- `/post-login/` - role-based redirect after login
- `/accounts/` - allauth authentication routes
- `/api/` - REST API endpoints
- `/sysadmin/` - Django admin interface

## Notes

- The development settings currently allow media files to be served locally when `DEBUG=True`.
- The API uses session-based authentication and expects authenticated access for most endpoints.
- Resume and profile uploads are stored under `media/`.

## License

This project is currently distributed without an explicit license.

