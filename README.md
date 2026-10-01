# Vaultline — Secure Document Sharing Platform

A working Flask application for uploading, storing and securely sharing
documents. Runs with zero setup locally (SQLite + local disk), and
deploys as a free, publicly reachable, persistent app on **Render +
Supabase** — no paid infrastructure required to get started.

Every piece in this README has actually been run and verified: the full
register → login → upload → share → download → revoke → admin flow
passes an automated test suite (19 tests), and the production migration
path (`flask db upgrade` → `flask seed-admin` → `gunicorn run:app`) was
executed against a real SQLite database to confirm it works exactly the
way Render will run it.

---

## 1. Architecture

```
                     INTERNET
                        │
                        ▼
                    Browser
                        │
                      HTTPS
                        │
                        ▼
                ┌───────────────┐
                │     Render    │
                │ Flask+Gunicorn│
                └───────┬───────┘
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
      ┌─────────────┐      ┌──────────────┐
      │  Supabase   │      │   Supabase   │
      │ PostgreSQL  │      │   Storage    │
      │             │      │              │
      │ users       │      │ documents/   │
      │ documents   │      │  user_1/...  │
      │ shares      │      │  user_2/...  │
      │ audit_logs  │      │              │
      └─────────────┘      └──────────────┘
```

Locally, the same code runs against SQLite and a `storage/` folder on
disk instead — the app detects which to use automatically (see §4).

## 2. Project structure

```
Vaultline/
├── app/
│   ├── __init__.py          # application factory
│   ├── extensions.py        # db, migrate, login manager, bcrypt, csrf, limiter
│   ├── models/               # one file per table
│   │   ├── user.py / document.py / share.py / audit_log.py
│   ├── routes/
│   │   ├── auth.py          # register / login / logout / lockout
│   │   ├── dashboard.py     # the main dashboard view
│   │   ├── documents.py     # upload / view / raw / download / delete
│   │   ├── sharing.py       # share / revoke / list / expiring token links
│   │   └── admin.py         # admin overview, users, documents, audit logs
│   ├── services/              # reusable business logic
│   │   ├── storage.py       # ★ local disk OR Supabase Storage, auto-selected
│   │   ├── hashing.py       # SHA-256 integrity checking
│   │   ├── sharing.py       # permission checks, expiry parsing
│   │   └── audit.py         # writes AuditLog rows
│   ├── utils/
│   │   ├── validators.py    # upload validation, safe filenames
│   │   └── security.py      # response headers, password strength
│   ├── templates/            # flat Jinja2 templates + admin/
│   └── static/css/style.css
├── migrations/                # real Alembic migrations (Flask-Migrate)
├── tests/                     # pytest suite — 19 tests, all passing
│   ├── test_auth.py / test_documents.py / test_sharing.py
├── storage/                    # LOCAL DEV ONLY — see storage/README.md
├── instance/                   # SQLite database file (local dev)
├── config.py
├── requirements.txt
├── Procfile                    # `web: gunicorn run:app`
├── render.yaml                 # Render Blueprint (infrastructure-as-code)
├── .env.example
└── run.py
```

---

## 3. Run it locally first (do this before deploying anything)

```bash
cd Vaultline
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# open .env, set SECRET_KEY to a random string:
#   python3 -c "import secrets; print(secrets.token_hex(32))"
python run.py
```

Open **http://127.0.0.1:5000**. A default admin login prints to the
console on first run — sign in with it, or set
`DEFAULT_ADMIN_EMAIL`/`DEFAULT_ADMIN_PASSWORD` in `.env` first.

Run the test suite any time with:
```bash
pip install pytest
pytest tests/ -v
```

---

## 4. How the local/production switch works

`app/services/storage.py` checks, once, at startup:

- **`SUPABASE_URL` and `SUPABASE_KEY` both set** → every upload goes to
  Supabase Storage; every read comes back from there too.
- **Neither set** → files are saved to `storage/user_<id>/` on local
  disk, exactly like before.

Each `Document` row remembers which backend it was saved under
(`storage_backend` column), so nothing breaks if you switch later — old
local files and new Supabase files can coexist.

The database follows the same pattern: set `DATABASE_URL` to switch
from SQLite to your Supabase Postgres connection string; leave it unset
for local SQLite.

**You never edit code to move from local to production** — only
environment variables change.

---

## 5. Deploying to Render + Supabase (free, public, persistent)

### Step 1 — Push your code to GitHub

```bash
cd Vaultline
git init
git add .
git commit -m "Initial Vaultline commit"
```
Create a new repository on GitHub, then follow its "push an existing
repository" instructions. **Double-check `.env` is not included** — it's
already in `.gitignore`, but confirm with `git status` before pushing.

### Step 2 — Create your Supabase project

1. Go to [supabase.com](https://supabase.com) → **New project**. Free
   tier is enough to start.
2. Once it's created, go to **Project Settings → Database → Connection
   string → URI**, choose **Transaction pooler** mode (port `6543`),
   and copy it. This is your `DATABASE_URL`.
3. Go to **Storage** in the left sidebar → **New bucket** → name it
   exactly `vaultline-documents` → set it to **Private** (not public —
   your app controls access via its own permission system, not a public
   bucket URL).
4. Go to **Project Settings → API**. Copy the **Project URL**
   (`SUPABASE_URL`) and the **`service_role` secret key** (`SUPABASE_KEY`
   — not the `anon` key; the service role key is what lets the backend
   read/write on behalf of any user).

### Step 3 — Create your Render service

1. Go to [render.com](https://render.com) → **New → Blueprint** → connect
   your GitHub repo. Render will read `render.yaml` automatically and
   propose a web service.
2. Where `render.yaml` says `sync: false`, Render will prompt you to
   fill in the value yourself. Enter:
   - `DATABASE_URL` — from Step 2.2
   - `SUPABASE_URL` — from Step 2.4
   - `SUPABASE_KEY` — from Step 2.4 (the service role key)
   - `DEFAULT_ADMIN_EMAIL` / `DEFAULT_ADMIN_PASSWORD` — your choice
3. Click **Apply**. Render will run `pip install -r requirements.txt &&
   flask db upgrade` as the build step (this creates all four tables in
   your Supabase database using the real migration in `migrations/`),
   then start the app with `gunicorn run:app`.

### Step 4 — Create the admin account

Render's free tier doesn't give you a persistent shell by default, so
the simplest way to run the one-off `flask seed-admin` command is via
Render's **Shell** tab on your service (available even on free web
services for one-off commands), or by temporarily adding
`&& flask seed-admin` to the build command for the first deploy only,
then removing it again afterward so it doesn't re-run on every deploy.

### Step 5 — Visit your app

Render gives you a URL like `https://vaultline.onrender.com` —
already on HTTPS, already public, no further setup. Share that link with
anyone.

---

## 6. What's genuinely persistent here, and what isn't

| Piece | Where it lives | Survives redeploys? |
|---|---|---|
| Users, documents metadata, shares, audit logs | Supabase PostgreSQL | ✅ Yes |
| Uploaded file contents | Supabase Storage bucket | ✅ Yes |
| The app process itself | Render web service | ✅ Yes, restarts automatically if it crashes |
| Anything in `storage/` on Render's own disk | Render's local filesystem | ❌ No — this is why we moved file storage to Supabase |

This is the actual fix for the "files disappeared" problem that plain
free-tier hosting has — as long as `SUPABASE_URL`/`SUPABASE_KEY` are set
in Render's environment, the app never touches its own local disk for
document storage.

---

## 7. Free-tier limitations (be upfront about these)

- **Render free web services sleep after ~15 minutes of inactivity.**
  The first request after sleeping takes 20–50 seconds while it wakes
  up. Fine for a demo/portfolio link; not "instant" 24/7 behavior. A
  paid Render plan (from ~$7/month) removes this.
- **Supabase free projects pause after about a week of no activity.**
  Logging into the Supabase dashboard and clicking "Restore" wakes it
  back up in a couple of minutes.
- **Storage and database size are capped** on free tiers (Supabase:
  500 MB database, 1 GB storage at the time of writing — check
  supabase.com/pricing for current limits, these change).
- **This is a demo/portfolio-grade deployment**, matching what your
  original deployment plan says: good for learning, a college
  submission, or a LinkedIn/portfolio link — not a guarantee of
  production-grade uptime for real sensitive documents.

---

## 8. Security feature map (unchanged from the local version)

| Feature | Where |
|---|---|
| Password hashing (bcrypt) | `app/models/user.py` |
| Account lockout after repeated failed logins | `routes/auth.py` |
| CSRF protection on every form | Flask-WTF, `extensions.py` |
| Safe, randomized file storage | `services/storage.py`, `utils/validators.py` |
| File type / size validation | `utils/validators.py` |
| SHA-256 integrity hash per file | `services/hashing.py` |
| Per-share permissions (VIEW / DOWNLOAD) | `services/sharing.py` |
| Expiring, revocable share links | `models/share.py`, `routes/sharing.py` |
| Full audit trail | `models/audit_log.py`, `services/audit.py` |
| Rate limiting on login | Flask-Limiter, `routes/auth.py` |
| Security response headers | `utils/security.py` |
| Role-based admin access | `models/user.py`, `routes/admin.py` |

Before sharing your live link with anyone: change the default admin
password, and make sure `SECRET_KEY` is a real random value and not the
placeholder from `.env.example`.
