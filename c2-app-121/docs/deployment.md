# Deployment Guide - Gate G3 Muc 1

Muc tieu cua muc 1 la co production URL chay duoc. Kien truc khuyen dung:

- Backend + MCP Clinical Server: Railway, build bang Dockerfile o root repo.
- Database: Railway PostgreSQL.
- Frontend React/Vite: Vercel, root directory la `c2-app-121-frontend`.

## 1. Chuan bi truoc khi deploy

Dam bao code da duoc push len GitHub:

```bash
git status
git add .
git commit -m "Prepare production deployment"
git push
```

Khong commit file `.env`. Cac secret nhu `OPENAI_API_KEY`, `SECRET_KEY`, `DATABASE_URL` phai set tren dashboard Railway/Vercel.

## 2. Deploy backend len Railway

1. Vao Railway va tao project moi.
2. Chon **Deploy from GitHub repo**.
3. Chon repo `C2-App-121`.
4. Railway se doc `railway.toml` va build bang `Dockerfile`.
5. Sau khi service duoc tao, vao tab **Variables** cua backend service.
6. Them cac bien moi truong sau:

```env
APP_ENV=production
LOG_LEVEL=INFO

LLM_PROVIDER=openai
OPENAI_API_KEY=<your-openai-api-key>
MODEL_NAME=gpt-4o-mini
LLM_TEMPERATURE=0.2

SECRET_KEY=<random-long-secret>
MAX_AUDIO_UPLOAD_MB=20
MAX_TRANSCRIPT_CHARS=12000

MCP_PORT=8001
MCP_CLINICAL_URL=http://127.0.0.1:8001/mcp

CORS_ORIGINS=http://localhost:5173
```

Neu dung Gemini thay OpenAI thi doi:

```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=<your-google-api-key>
GEMINI_MODEL_NAME=gemini-2.0-flash
```

## 3. Them PostgreSQL tren Railway

1. Trong cung Railway project, bam **+ New**.
2. Chon **Database** -> **PostgreSQL**.
3. Quay lai backend service -> **Variables**.
4. Them bien:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

Neu ten service PostgreSQL tren Railway khong phai `Postgres`, dung autocomplete cua Railway de chon dung bien `DATABASE_URL` cua service database.

## 4. Tao public backend URL

1. Vao backend service -> **Settings** -> **Networking**.
2. Bam **Generate Domain**.
3. Copy URL dang:

```text
https://<your-backend>.up.railway.app
```

Kiem tra backend:

```bash
curl https://<your-backend>.up.railway.app/health
```

Ket qua mong doi:

```json
{"status":"ok","env":"production"}
```

Swagger UI:

```text
https://<your-backend>.up.railway.app/docs
```

## 5. Deploy frontend len Vercel

1. Vao Vercel va tao project moi.
2. Import cung GitHub repo `C2-App-121`.
3. O muc **Root Directory**, chon:

```text
c2-app-121-frontend
```

4. Vercel se tu nhan Vite. Neu can dien thu cong:

```text
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

5. Them Environment Variable tren Vercel:

```env
VITE_API_BASE_URL=https://<your-backend>.up.railway.app
```

6. Bam **Deploy**.
7. Copy frontend URL dang:

```text
https://<your-frontend>.vercel.app
```

## 6. Cap nhat CORS sau khi co frontend URL

Quay lai Railway backend service -> **Variables**, sua:

```env
CORS_ORIGINS=http://localhost:5173,https://<your-frontend>.vercel.app
```

Sau do redeploy/restart backend service.

## 7. Checklist nop muc 1

- Backend health URL chay duoc:

```text
https://<your-backend>.up.railway.app/health
```

- Backend docs URL mo duoc:

```text
https://<your-backend>.up.railway.app/docs
```

- Frontend production URL mo duoc:

```text
https://<your-frontend>.vercel.app
```

- Dang ky/dang nhap tren frontend thanh cong.
- Goi API tu frontend khong bi CORS error.
- Upload audio nho de tao SOAP note thanh cong.

Production URL nen nop cho Gate G3 la frontend URL tren Vercel. Co the ghi kem backend URL de giang vien verify API.

## 8. Loi thuong gap

- **CORS error:** cap nhat `CORS_ORIGINS` tren Railway dung chinh xac frontend URL Vercel.
- **Frontend goi nham localhost:** kiem tra `VITE_API_BASE_URL` tren Vercel va redeploy frontend.
- **Backend khong healthy:** xem Railway logs, dam bao `OPENAI_API_KEY`, `DATABASE_URL`, `SECRET_KEY` da set.
- **Upload audio cham lan dau:** model `vinai/PhoWhisper-small` co the can tai/cache lan dau va ton RAM. Neu Railway bi out-of-memory, tang memory/plan hoac demo bang file audio ngan.

## Tai lieu tham khao

- Railway Dockerfiles: https://docs.railway.com/builds/dockerfiles
- Railway FastAPI: https://docs.railway.com/guides/fastapi
- Railway Variables: https://docs.railway.com/variables
- Vercel Vite: https://vercel.com/docs/frameworks/frontend/vite
