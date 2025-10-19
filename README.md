# OncoScan AI - Secure MVP (local)

This workspace contains a professional-grade foundation for a medical imaging AI web app. It includes a Tailwind frontend and a FastAPI backend implementing JWT authentication, protected prediction, pluggable model backends (simulated or PyTorch), DICOM parsing, file persistence, and auditing.

Quick start

1. Create a virtualenv and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. (Optional) Create a `.env` from the example and set a secure secret:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set ONCOSCAN_SECRET_KEY to a secure random string
```

3. Configure model backend (optional):

- Simulated (default): no extra setup.
- PyTorch: set environment variables and provide a model path (TorchScript recommended):

```bash
export ONCOSCAN_MODEL_BACKEND=torch
export ONCOSCAN_MODEL_PATH=/path/to/model.pt
export ONCOSCAN_MODEL_DEVICE=cpu   # or cuda
```

4. Run the FastAPI server:

```bash
uvicorn oncoscan_webapp.backend.main:app --reload --host 127.0.0.1 --port 8000
```

5. Open the frontend in your browser:

Option A: open `oncoscan_webapp/frontend/index.html` directly (file://) — some browsers may restrict fetch from file URIs.

Option B (recommended): serve the frontend directory:

```bash
cd oncoscan_webapp/frontend
python3 -m http.server 8080
# then open http://127.0.0.1:8080
```

Demo credentials

- username: `doc_user`
- password: `securepass`

Security notes

- The default `ONCOSCAN_SECRET_KEY` in `.env.example` is not secure. Use a long random value in production.
- Tokens are signed with HS256 (HMAC); consider asymmetric keys for higher assurance.
- CORS is permissive for the MVP; restrict allowed origins in production.

Database (PostgreSQL recommended)

- Set `ONCOSCAN_DATABASE_URL`, for example:

```bash
export ONCOSCAN_DATABASE_URL=postgresql+psycopg2://oncoscan:password@localhost:5432/oncoscan
```

- The app will auto-create tables on startup. For production, adopt migrations (Alembic).

Admin user creation

```bash
source .venv/bin/activate
python -m oncoscan_webapp.backend.scripts_create_admin admin_user StrongPass123 --full-name "Admin User"
```


Operational endpoints

- `GET /status` — returns model backend status and loaded info.
- `POST /models/reload` — reloads the model (currently requires authentication; lock down to admins when RBAC is added).

