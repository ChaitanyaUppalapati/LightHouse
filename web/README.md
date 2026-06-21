# Lighthouse — web/ (family dashboard & screens)

The front-end of Lighthouse: what the family and the protected person see.

## Run it

```bash
cd web
npm install
npm run dev      # http://localhost:5173
```

Build for production:

```bash
npm run build
npm run preview
```

## What's here so far

- **S1 — Family dashboard** (`/`): the guardian's home screen.
  - **Needs your decision** — pending high-stakes approvals with big Approve / Deny buttons.
  - **What I've handled** — safe, reversible actions Lighthouse did on its own.
- **S2 — History timeline** — everything Lighthouse did for Margaret, newest first.

Designed for an older person's family: 18px+ text, high contrast, large buttons,
icon **and** word on every action (never color alone), calm and trustworthy.

## Data

All screens currently run on **fake data** in [`src/data/fakeData.js`](src/data/fakeData.js).
The shapes mirror the backend contract (approvals, action results, ledger events) so that
**S6** can swap in live calls to the data service with minimal changes.

## Stack

Vite + React + React Router + Tailwind CSS v4.
