# EnerGenAI frontend

React18/TypeScript,Vite8,ReactRouter7,Tailwind4 with PostCSS,Radix/shadcn components,Recharts,Lucide,Framer Motion. Pages use typed backend API responses; no browser-side model or secret API keys.

Node22.12+ required,Node24 tested. From this directory:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1 --port 8080
```

.env contains only VITE_API_URL=http://127.0.0.1:5000. Start backend separately. Open http://localhost:8080. Never use npm .cmd run dev.

The application opens at /login. Create an account or log in to enter /dashboard. All workspace pages require a browser session. /predict is the dual-mode manual-input predictor; /forecast remains the history-based forecast. /chatbot and /queries redirect to Copilot. Shared dataset endpoints remain public on the backend; frontend login does not make that dataset private. See [prediction guide](../PREDICTION_GUIDE.md) for source data, inputs, units, measured limitations and reproducible training.

The circular profile button at the top right opens user details (email and session expiry), browser-local tariff/carbon settings, and Log out. Creating an account automatically logs in. Existing valid sessions survive reload; logout and expiry return users to /login. GET /api/auth/me validates the session with the backend. Settings are not saved to an account database.

Validation: npx.cmd tsc --noEmit -p tsconfig.app.json; npm.cmd run build; npm.cmd run test:e2e. Browser tests use installed Chrome, with both services running. Output/screenshots are ignored in backend/runtime. PLAYWRIGHT_CHANNEL=chromium selects an installed Playwright browser if Chrome unavailable.

Vercel root directory must be energy-frontend,output dist; set HTTPS VITE_API_URL and rebuild. vercel.json rewrites SPA routes. Configure backend WEB_ORIGIN for exact frontend origin.

[Full end-to-end documentation](../PROJECT_GUIDE.md) includes dataset limitations,model evaluation,privacy,config and deployment.
