# NEXUS GRID Frontend

This package contains the Next.js dashboard for the NEXUS GRID experience. It renders the district twin, charts, telemetry panels, and operator controls that connect to the backend simulation stream.

## Commands

```bash
npm install
npm run dev
```

## Available Scripts

- `npm run dev` starts the local development server
- `npm run build` creates a production build
- `npm run start` serves the production build
- `npm run lint` runs ESLint

## Notes

- The dashboard expects the FastAPI backend to be running locally.
- Main application code lives under `src/app`, `src/components`, and `src/hooks`.
