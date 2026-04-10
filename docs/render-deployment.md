# NexusGrid Render Deployment

This repo is prepared for a two-service Render deployment:

- `gridwala-nexusgrid-backend`
  - FastAPI backend
  - WebSocket runtime
  - health check: `/status`

- `gridwala-nexusgrid-frontend`
  - Next.js frontend
  - talks to the backend through `NEXT_PUBLIC_NEXUS_API_URL`

## Files Added For Render

- [render.yaml](C:\Users\saury\Desktop\devpost\render.yaml)
- [nexus-grid/frontend/.env.example](C:\Users\saury\Desktop\devpost\nexus-grid\frontend\.env.example)
- [nexus-grid/backend/.env.example](C:\Users\saury\Desktop\devpost\nexus-grid\backend\.env.example)

## Required Secrets On Render

Backend:

- `NEXUS_ELECTRICITYMAPS_API_KEY`
- `NEXUS_OPENEI_API_KEY`
- `NEXUS_NOMINATIM_EMAIL`

Frontend:

- `NEXT_PUBLIC_NEXUS_API_URL`
  - should match the public Render backend URL

Optional frontend map config:

- `NEXT_PUBLIC_NEXUS_MAP_STYLE_URL`
- `NEXT_PUBLIC_NEXUS_PMTILES_URL`

## Important Notes

- NexusGrid uses a live FastAPI WebSocket simulation endpoint at `/ws/simulate`.
- This is why Render is a better fit than Vercel for the current architecture.
- If you rename either Render service, update:
  - `NEXT_PUBLIC_NEXUS_API_URL`
  - `NEXUS_ALLOWED_ORIGINS`

## Recommended Deploy Order

1. Deploy backend first.
2. Copy its public URL.
3. Set frontend `NEXT_PUBLIC_NEXUS_API_URL` to that backend URL.
4. Update backend `NEXUS_ALLOWED_ORIGINS` with the frontend Render URL.
5. Redeploy both services once after envs are correct.
