# Beauty Salon Booking System

Full-stack Python project built in the same style as `lesson31-33`:

- `main.py` runs the FastAPI backend.
- `app.py` runs the Streamlit frontend.
- `database.py` creates and seeds SQLite tables.
- `models/` stores Pydantic models.
- `routers/` stores FastAPI route files.
- `auth/` stores authentication and API-key helpers.

## Features

- Sign in and sign up before using the app.
- Dashboard with pandas and Plotly graphs.
- CRUD for services, appointments, customers, staff, and admin users.
- SQLite database with seed data.
- Seeded service images in `assets/services/`.
- Admin API key for protected create, update, and delete actions.

## Install

Open PowerShell in this folder:

```powershell
cd C:\Users\Student\Desktop\Beauty-Salon-Booking-System\Beauty-Salon-Booking-System
```

Install packages:

```powershell
python -m pip install -r requirements.txt
```

If `python` does not work on this computer, use the installed Python path:

```powershell
& "C:\Users\Student\AppData\Local\Programs\Python\Python312\pythonw.exe" -m pip install -r requirements.txt
```

## Environment

The project includes `.env` with development settings:

```text
BASE_URL=http://127.0.0.1:8000/api
SALON_API_KEY=salon-admin-key
SEEDED_ADMIN_USERNAME=admin
SEEDED_ADMIN_PASSWORD=admin123
SEEDED_USER_EMAIL=mira@example.com
SEEDED_USER_PASSWORD=student123
```

## Run Backend

```powershell
uvicorn main:app --reload
```

Backend docs:

```text
http://127.0.0.1:8000/docs
```

## Run Frontend

Open another PowerShell window in the same folder:

```powershell
streamlit run app.py
```

Frontend:

```text
http://127.0.0.1:8501
```

## Run UI Tests

Playwright is used for browser testing.

```powershell
npm.cmd install
npx.cmd playwright install chromium
npm.cmd run test:ui
npm.cmd run test:dashboard
npm.cmd run test:mobile
```

## Seeded Credentials

Normal user login:

```text
Email: mira@example.com
Password: student123
```

Admin API key for protected CRUD:

```text
salon-admin-key
```

Seeded admin account stored in the database:

```text
Username: admin
Password: admin123
```

## Main Files

- `main.py`: creates the FastAPI app and includes routers.
- `app.py`: Streamlit UI with auth gate and pages.
- `database.py`: SQLite connection, table creation, seed data.
- `auth/security.py`: password hashing and API-key validation.
- `models/*.py`: Pydantic models for request and response validation.
- `routers/*.py`: CRUD and auth API endpoints.
- `assets/services/*.png`: seeded service images.
- `PROJECT_CODE_EXPLANATION.docx`: student learning document explaining the code.
