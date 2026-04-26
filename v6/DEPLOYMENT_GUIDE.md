# Deployment Guide — Vercel (Frontend) + Render (Backend) + Supabase (Database)

## Architecture
```
Browser → Vercel (index.html) → Render (FastAPI API) → Supabase (PostgreSQL)
```

---

## STEP 1 — Supabase Database Setup

1. Go to https://supabase.com → Sign up with GitHub
2. Click **New Project**
   - Name: `smart-attendance`
   - Database Password: (choose strong password — SAVE IT)
   - Region: **South Asia (Singapore)** (closest to India)
3. Wait 2 minutes for project to create
4. Go to **Settings → Database**
5. Scroll to **Connection String** → select **URI** tab
6. Copy the connection string — looks like:
   ```
   postgresql://postgres.[ref]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
   ```
   Replace `[PASSWORD]` with your actual password
7. **Save this URL** — needed in Step 2

---

## STEP 2 — Render Backend Setup

1. Go to https://render.com → Login with GitHub
2. **New → Web Service** → Connect your GitHub repo
3. Settings:
   - **Name**: smart-attendance-api
   - **Root Directory**: backend
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables** — Add these:
   ```
   DATABASE_URL = postgresql://postgres.[ref]:[PASSWORD]@...supabase.com:5432/postgres
   SECRET_KEY   = SmartAttendance2025TMU@SecretKey#Sarthak
   FRONTEND_URL = https://your-app.vercel.app  (fill after Step 3)
   ```
5. Click **Create Web Service** → wait for deploy
6. Copy your Render URL: `https://smart-attendance-api.onrender.com`

---

## STEP 3 — Vercel Frontend Setup

1. Go to https://vercel.com → Login with GitHub
2. **New Project** → Import your GitHub repo
3. Settings:
   - **Framework Preset**: Other
   - **Root Directory**: `frontend`  ← IMPORTANT
   - Leave all other settings default
4. **Environment Variables** — Add:
   ```
   (none needed — backend URL is set in index.html)
   ```
5. Click **Deploy**
6. Copy your Vercel URL: `https://your-app.vercel.app`

---

## STEP 4 — Connect Frontend to Backend

After both are deployed, update the backend URL in `frontend/index.html`:

Find this line (around line 1380):
```javascript
const BACKEND_URL = window.__BACKEND_URL__ || '';
```

The frontend auto-detects — but to explicitly point to Render:
Go to **Vercel → your project → Settings → Environment Variables**
(No env vars needed — the frontend uses window.location.host by default)

**But you need to tell the frontend where the backend is.**
In `frontend/index.html`, find and update:
```javascript
const BACKEND_URL = window.__BACKEND_URL__ || '';
```
Change to:
```javascript
const BACKEND_URL = window.__BACKEND_URL__ || 'https://smart-attendance-api.onrender.com';
```
Then push to GitHub → Vercel auto-redeploys.

---

## STEP 5 — Update Render CORS

In Render → Environment Variables, add:
```
FRONTEND_URL = https://your-app.vercel.app
```

---

## Login Credentials (after first deploy)
- **Admin**: `admin1` / `Pass@123`

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Login fails | Check Render logs for database connection errors |
| CORS error | Add your Vercel URL to FRONTEND_URL on Render |
| 500 error | Run the Supabase SQL migration below |
| Blank page | Check browser console for API URL errors |

## Supabase SQL — Run if you get database errors
```sql
-- Tables are created automatically on first deploy
-- If you see errors, run this to check:
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';
```
