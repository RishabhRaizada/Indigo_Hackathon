# AI Creative Studio — CLAUDE.md

## Project Overview

AI Creative Studio is an AI-powered content creation platform that helps marketing teams,
startups, and content creators generate social media content, marketing copy, and AI banners
using simple prompts. Goal: reduce marketing asset creation from hours to seconds.

## Repository Structure

```
Hackathon_Indigo/
├── ai-studio-pro/          # Frontend (React + Vite + TypeScript + Tailwind + shadcn/ui)
├── backend/                # Backend (FastAPI + Python)
├── venv/                   # Shared Python virtual environment (backend)
├── .env                    # Shared secrets — read by backend/app/config.py
├── test_api.py             # API connectivity smoke test (OpenAI + Gemini)
└── docs/
    ├── tasks.md            # Master task list
    ├── backend.md          # Backend architecture spec
    └── product.md          # Full PRD / engineering reference
```

---

## Asset Storage — Where Images Are Saved

### Current (MVP — browser localStorage)

All generated assets are stored **in the browser only**. Nothing is written to disk or a server.

| What | Where |
|------|-------|
| Asset records (metadata + image data) | `localStorage` key: **`acs_assets`** |
| Format | JSON array of `Asset` objects |
| Image data | Stored as **base64 data URLs** (`data:image/png;base64,...`) directly inside each asset record |
| Seed/fallback images | Regular `https://picsum.photos/...` URLs |

#### How to inspect in the browser
```
Chrome / Edge DevTools:
  Application → Storage → Local Storage → http://localhost:8080
  Key: acs_assets
  Value: JSON array (expand to see individual assets)
```

#### Practical limits
- Each AI-generated image (Imagen 4 / Gemini) is approximately **1–2 MB** as a base64 string
- `localStorage` limit per origin is **~5 MB** in most browsers
- At ~1.5 MB per image, the store can hold roughly **3–4 real AI images** before hitting the limit
- Seed images (URLs only) cost almost nothing
- When the limit is hit, the `localStorage.setItem` call in `AssetStoreProvider` silently fails (caught with `try/catch`) and the in-session state still works — only persistence is lost

#### localStorage size warning
This is a known MVP limitation. The production fix is to store images in object storage (Cloudflare R2 / S3) and only persist the CDN URL in `acs_assets`. That work is tracked in `docs/tasks.md` Phase 3.

### Context provider location
`AssetStoreProvider` lives in `src/routes/__root.tsx` (root layout) — wraps the entire app as a single instance. All pages share one store and one localStorage sync. Do NOT move it back inside `AppShell`.

### localStorage keys reference

| Key | Contents | Format |
|-----|----------|--------|
| `acs_assets` | All generated assets (images + metadata) | `Asset[]` JSON |
| `acs_auth` | Auth session (to be added) | `{ token, user }` JSON |
| `acs_projects` | Project list (to be added) | `Project[]` JSON |

---

## Frontend — ai-studio-pro

### Tech Stack
- React 19, TypeScript, Vite 7
- TanStack Router (file-based routing)
- TanStack Query (server state)
- Tailwind CSS 4 + shadcn/ui (Radix primitives)
- Lucide React (icons), Sonner (toasts), Recharts (charts)
- Hosted via Lovable / Cloudflare

### Run Frontend
```bash
cd ai-studio-pro
npm install
npm run dev       # http://localhost:5173 (or 8080 if Lovable hosted)
npm run build
npm run lint
```

### Key Frontend Files
| File | Purpose |
|------|---------|
| `src/routes/__root.tsx` | Root layout — wraps app with QueryClientProvider + **AssetStoreProvider** |
| `src/routes/index.tsx` | Redirects / → /projects/demo |
| `src/routes/projects.$projectId.tsx` | Project workspace (5 tabs: Social, Copy, Banner, Edit, Image Gen) |
| `src/routes/explore.tsx` | Asset gallery — reads from AssetStoreContext |
| `src/routes/analytics.tsx` | Stats + charts |
| `src/components/layout/AppShell.tsx` | Page chrome (Topbar + max-width container + Toaster) — no providers |
| `src/components/layout/Topbar.tsx` | Sticky header with nav links |
| `src/components/workspace/tabs.tsx` | All 5 generator tab UIs — calls addAsset() after every generation |
| `src/components/providers/AssetStoreProvider.tsx` | Single-instance store — localStorage read/write |
| `src/lib/asset-store.ts` | Asset interface, AssetStore interface, context, useAssetStore() hook |
| `src/lib/api.ts` | All backend API calls (generateSocial, generateCopy, generateBanner, generateImage) |
| `src/styles.css` | Design tokens (Oklch colors, Inter font) |

### Asset Store Methods
```ts
addAsset(a)             // saves to state + localStorage instantly
removeAsset(id)         // deletes from state + localStorage
toggleFavorite(id)      // flips favorite flag
clearAssets()           // wipes all assets
getAssetsByProject(id)  // filtered view
getAssetsByType(type)   // filtered view
```

### Frontend Conventions
- Design tokens live in `src/styles.css` — do not hardcode colors
- All shadcn components are in `src/components/ui/`
- Page routes are in `src/routes/` using TanStack file-based routing
- Asset type: `"social" | "banner" | "image-gen" | "image-edit"`
- Project category: `"social" | "copywriter" | "banner"`
- API base URL: `import.meta.env.VITE_API_BASE_URL` (defaults to `http://localhost:8000`)
- `AssetStoreProvider` must stay in `__root.tsx` — never inside `AppShell`

### Design System
- Primary color: indigo (`oklch(0.585 0.22 277)`)
- Font: Inter (Google Fonts)
- Card style: `rounded-xl border border-border bg-card shadow-[0_1px_2px_rgba(16,24,40,0.04)]`
- Hover lift: `hover:-translate-y-0.5 hover:shadow-[0_8px_20px_rgba(16,24,40,0.08)]`
- Badge colors: Social=blue, Banner=orange, Copywriter=purple

---

## Backend — backend/

### Tech Stack
- Python 3.11+, FastAPI 0.115, Uvicorn
- **Azure OpenAI** (NOT standard OpenAI) — deployment: `gpt-5-mini1` (reasoning model)
- **Google Gemini** — `imagen-4.0-generate-001` (primary), `gemini-2.5-flash-image` (fallback)
- Pydantic v2, python-dotenv

### Critical: Azure OpenAI is a Reasoning Model
The deployment `gpt-5-mini1` is a reasoning model (o-series style). This means:
- ❌ Do NOT set `temperature` — unsupported, raises 400
- ❌ Do NOT set `max_tokens` — use `max_completion_tokens` instead
- ❌ Do NOT set small `max_completion_tokens` — reasoning tokens consume the budget first, leaving nothing for output. **Omit the parameter entirely** for reliable results.
- ✅ Works perfectly without temperature/token overrides

### Available Gemini Image Models (confirmed working on this API key)
| Model | API method | Notes |
|-------|-----------|-------|
| `imagen-4.0-generate-001` | `client.models.generate_images()` | Primary — highest quality |
| `imagen-4.0-fast-generate-001` | `client.models.generate_images()` | Faster, lower quality |
| `imagen-4.0-ultra-generate-001` | `client.models.generate_images()` | Highest quality |
| `gemini-2.5-flash-image` | `client.models.generate_content()` with `response_modalities=["IMAGE","TEXT"]` | Fallback |
| `gemini-3-pro-image-preview` | `client.models.generate_content()` | Available |
| `gemini-3.1-flash-image-preview` | `client.models.generate_content()` | Available |
| ~~`imagen-3.0-generate-002`~~ | — | ❌ NOT available on this key |
| ~~`gemini-2.0-flash-exp-image-generation`~~ | — | ❌ NOT available on this key |

### Run Backend
```bash
# From Hackathon_Indigo/ root (where venv/ lives)
./backend/run.sh

# Or manually:
source venv/bin/activate
PYTHONPATH=backend uvicorn app.main:app --app-dir backend --reload --port 8000
```

### .env location
The `.env` file lives at the **project root** (`Hackathon_Indigo/.env`).
`backend/app/config.py` resolves it via `Path(__file__).parent.parent.parent / ".env"`.
Do NOT create a separate `backend/.env` — use the root one.

### Environment Variables (root .env)
```
OPENAI_API_KEY=         # Azure OpenAI key
AZURE_ENDPOINT=         # https://openai-lab37-hackathon.openai.azure.com
AZURE_API_VERSION=      # 2024-02-15-preview
AZURE_DEPLOYMENT=       # gpt-5-mini1
GEMINI_API_KEY=         # Google Gemini key
```

### CORS Allowed Origins (config.py)
```
http://localhost:5173
http://localhost:4173
http://localhost:8080
http://localhost:3000
http://127.0.0.1:5173
http://127.0.0.1:8080
http://127.0.0.1:3000
```
Add new ports here when needed. `allow_credentials` must be `True` (bool) — not `["*"]`.

---

## API Endpoints

Base: `http://localhost:8000`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/generate/health` | Generation router health |
| POST | `/api/v1/generate/social` | Social content + image per platform |
| POST | `/api/v1/generate/copy` | 3 copy variants (Short/Medium/Long) |
| POST | `/api/v1/generate/banner` | Enhanced prompt + AI banner image |
| POST | `/api/v1/generate/image` | Text-to-image generation |

Swagger UI: `http://localhost:8000/docs`

### Image response format
All image endpoints return `imageUrl` as a **base64 data URL**:
```json
{ "imageUrl": "data:image/png;base64,/9j/4AAQ...", "enhancedPrompt": "..." }
```
The frontend stores this string directly in `acs_assets` localStorage. No CDN, no file upload in MVP.

---

## Generation Flow (end-to-end)

```
User clicks Generate
  → tabs.tsx calls api.ts function (generateSocial / generateCopy / generateBanner / generateImage)
  → fetch() POST to http://localhost:8000/api/v1/generate/*
  → FastAPI router (routers/generate.py)
  → openai_service.py: Azure OpenAI text generation (parallel per platform for social)
  → gemini_service.py: Imagen 4 image generation → base64 data URL
  → Response JSON returned to frontend
  → tabs.tsx calls addAsset({ url: imageUrl, type, title, prompt, metadata })
  → AssetStoreProvider saves to React state + localStorage[acs_assets]
  → Explore page re-renders instantly (same Context)
```

---

## Git Workflow

- Branch: feature branches off `main`
- Commits: conventional commits (`feat:`, `fix:`, `chore:`)
- Frontend changes: `cd ai-studio-pro` first
- Backend changes: activate venv first (`source venv/bin/activate`)
