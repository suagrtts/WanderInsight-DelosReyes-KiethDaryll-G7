# WanderInsight

**A Personalized Cultural Heritage Analytics and Information Management Platform**
CSIT327 – Information Management 2 · Section G7 · Proponent: Kieth Daryll Delos Reyes

Full-stack Django 6 (server-rendered Django templates + Bootstrap 5 + Chart.js + Three.js) backed by **PostgreSQL on Supabase**.

---

## Project Development 2 – Core Feature (Vertical Slice)

### Cultural Heritage Site Registry & Daily Visitation Logging (`heritage` app · SDD F-02 & F-03)

WanderInsight's core vertical slice enables heritage custodians to register Cebu's cultural landmarks, classify them across normalized geographic districts and heritage categories, attach conservation designations, and record validated daily visitor attendance with live SQL analytics across role-specific dashboards.

| Capability | Implementation |
|---|---|
| **Relational Schema (PostgreSQL / Supabase)** | `District` (`1:N`), `HeritageCategory` (`1:N`), `PreservationTag` (`M:N`), `HeritageSite` (`FK` to `District`, `HeritageCategory`, `accounts.User`), and `VisitationLog` (`FK` to `HeritageSite`, `accounts.User`) |
| **Full CRUD in UI** | Heritage Sites (`/heritage/sites/`, `/heritage/sites/new/`, `/heritage/sites/<slug>/`, `/edit/`, `/delete/`), Daily Visitation Logs (`/heritage/logs/`, `/heritage/logs/new/`, `/edit/`, `/delete/`), and Admin Taxonomy (`/heritage/taxonomy/`) |
| **Validation & Business Rules** | **BR-01** (`local + domestic + foreign == total_visitors`), **BR-04** (unique `(site, visit_date)` daily log), **BR-10** (Curator ownership isolation & Admin governance), Cebu GPS coordinate bounds (`9.3°N–11.6°N`, `123.2°E–124.7°E`), historical year (`1500–present`), and non-future log dates |
| **Role-Based Dashboards** | Live PostgreSQL `SUM()`, `AVG()`, `COUNT()`, and `TruncMonth()` aggregations powering interactive Chart.js visitation trend lines and demographic origin doughnuts on Administrator, Curator, and Viewer dashboards |

---

## Project Development 1 – Standard Account Features

| Requirement | Implementation |
|---|---|
| **Registration** | `/accounts/register/`: required fields, valid email, case-insensitive unique username & email, password confirmation, PBKDF2 hashing |
| **Login / Logout** | `/accounts/login/` (clear error on invalid credentials), `/accounts/logout/` (CSRF-protected `POST`) |
| **Role-Based Access Control** | `@login_required` + `@role_required` decorators for **Administrator**, **Curator**, and **Viewer** roles |
| **User Profile** | `/accounts/profile/`, `/accounts/profile/edit/`, and `/accounts/profile/password/` scoped strictly to `request.user` |

---

## Setup Instructions

```bash
git clone https://github.com/suagrtts/WanderInsight-DelosReyes-KiethDaryll-G7.git
cd WanderInsight-DelosReyes-KiethDaryll-G7
python -m venv venv
venv\Scripts\activate          # Windows (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # Fill in SECRET_KEY and your Supabase PostgreSQL DATABASE_URL
python manage.py migrate
python manage.py seed_heritage_data   # Seeds Cebu districts, categories, landmarks, logs, and PD2 test accounts
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

### Environment Variables (`.env`, excluded via `.gitignore`)

| Key | Description |
|---|---|
| `SECRET_KEY` | Django cryptographic secret key |
| `DEBUG` | `True` for local development, `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hostnames (e.g., `127.0.0.1,localhost`) |
| `DATABASE_URL` | Supabase Session Pooler PostgreSQL URI (`postgresql://postgres.<ref>:<password>@aws-1-<region>.pooler.supabase.com:5432/postgres`) |

---

## Test Accounts (Seeded via `python manage.py seed_heritage_data`)

| Role | Username | Email | Password |
|---|---|---|---|
| **Administrator** | `admin_pd2` | `admin.pd2@wanderinsight.ph` | `WanderAdmin#2026` |
| **Curator** | `curator_pd2` | `curator.pd2@wanderinsight.ph` | `WanderCurator#2026` |
| **Viewer** | `viewer_pd2` | `viewer.pd2@wanderinsight.ph` | `WanderViewer#2026` |

---

## Running Automated Tests

```bash
python manage.py test
```
