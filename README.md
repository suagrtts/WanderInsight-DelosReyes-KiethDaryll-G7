# WanderInsight

**A Personalized Cultural Heritage Analytics and Information Management Platform**
CSIT327 – Information Management 2 · Proponent: Kieth Daryll Delos Reyes

Full-stack Django (Django templates) + PostgreSQL (Supabase).

## Phase 1 – Account Feature

| Requirement | Implementation |
|---|---|
| Registration | `accounts/register/`: required fields, valid email, unique username & email (case-insensitive), password confirmation, Django password validators |
| Password hashing | Django built-in auth (`create_user` / `UserCreationForm`, PBKDF2) |
| Login / Logout | `accounts/login/` (error on invalid credentials), `accounts/logout/` (POST, ends session) |
| Protected pages | `@login_required` + custom `@role_required` decorator; anonymous users go to the login page |
| Roles | **Administrator**, **Curator**, **Viewer** (from SDD F-01 / BR-10) |
| Role dashboards | `/accounts/dashboard/` sends each user to their role's dashboard; other roles' URLs redirect back with an error |
| Profile | `accounts/profile/` (view), `accounts/profile/edit/` (name, email, contact number, organization, bio, photo), `accounts/profile/password/`. Always the logged-in user's own record, with no user id in the URL |

Viewers and Curators can self-register. Administrator accounts are created with `python manage.py createsuperuser` or promoted by an admin. Users with the Admin role get Django admin (staff) access for managing users.

## Setup

```bash
git clone <repo-url>
cd <repo>
python -m venv venv
venv\Scripts\activate          # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # then edit .env with your SECRET_KEY and Supabase DATABASE_URL
python manage.py migrate
python manage.py createsuperuser   # creates an Administrator
python manage.py runserver
```

Open http://127.0.0.1:8000/

### Environment variables (`.env`, never committed)

| Key | Example |
|---|---|
| `SECRET_KEY` | long random string |
| `DEBUG` | `True` |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` |
| `DATABASE_URL` | `postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres` (optional for now; if unset, a local `db.sqlite3` is used during development) |

## Tests

```bash
python manage.py test accounts
```
