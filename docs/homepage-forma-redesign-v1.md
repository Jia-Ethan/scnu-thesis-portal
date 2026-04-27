# Forma homepage redesign v1

## Current findings

- Frontend stack: React 18, Vite, TypeScript, plain CSS imports under `web/src/styles.css`.
- Routing: no router dependency. Current app renders one shell and clears legacy hash routes.
- Core homepage files: `web/src/app/AppShell.tsx`, `web/src/components/minimal/MinimalHome.tsx`, `HomeComposer.tsx`, `PrecheckResultPanel.tsx`, `web/src/styles/features.css`.
- Core flow hook: `web/src/app/useMinimalExportFlow.ts`, preserving public `.docx` precheck and export job APIs.
- Deployment: `vercel.json` builds through `scripts/build_web_public.py` into static `public`; Vite dev proxies `/api` to `127.0.0.1:8000`.
- Guide/help page: no dedicated frontend Guide page found. Add lightweight `#/guide` route without introducing a router package.

## Change path

- Rename frontend positioning from SCNU Thesis Portal to Forma.
- Reduce homepage copy and remove tutorial-like step cards from the home view.
- Move support/usage/privacy guidance to a new Guide page.
- Keep `.docx` upload, precheck, placeholder fix, and export flow intact.
