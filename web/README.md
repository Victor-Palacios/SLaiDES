# slidekit layout-feedback site

A private, phone-friendly website for reviewing every slide layout and marking it 👍/👎
with a note. It replaced the GitHub **Layout feedback** issue form (retired 2026-07-02): instead of filing an
issue per layout, you scroll a gallery of all 40 layouts, tap good/needs-work, optionally
comment, and hit **Submit**. Submissions land in `ops/FEEDBACK.yaml` — the same file the
nightly already treats as its actionable feedback queue.

Only you can reach it: the whole site sits behind a single password (Netlify edge
function). No Supabase, no OAuth, no per-user accounts — one operator, one secret.

## How it works

```
 phone browser                Netlify                         GitHub repo
┌───────────────┐   password  ┌──────────────────────┐  API   ┌──────────────────────────┐
│ gallery of 40 │──────────── ▶│ edge auth (SITE_PW)  │        │ web/feedback-inbox/*.json │
│ layouts,👍/👎 │             │  ↓ signed cookie      │        │            │             │
│  + comment    │  POST marks │ submit-feedback fn    │────────▶ commit ────┘             │
└───────────────┘─────────────▶│ (verifies cookie,    │        │            │ push        │
                               │  commits via token)   │        │ web-feedback-intake CI    │
                               └──────────────────────┘        │  → FEEDBACK.yaml + .md     │
                                                                └──────────────────────────┘
```

- **Previews are not screenshots.** Each layout is rendered from the *resolved geometry*
  (the same math that produces the `.pptx`/`.pdf`) into absolute-positioned HTML by
  `scripts/build_web_previews.py` → `web/data/previews.json`. A test keeps that JSON in
  sync with the layout catalog, so the gallery can never silently drift.
- **Auth** is `netlify/edge-functions/auth.js`: it gates every route, shows a password
  page, and on the correct `SITE_PASSWORD` sets a signed `HttpOnly` cookie
  (`HMAC-SHA256(password, "slaides-v1")`).
- **Writes** go through `netlify/functions/submit-feedback.js`: it re-verifies that cookie,
  then commits the batch as one JSON file under `web/feedback-inbox/` via the GitHub API.
- **Fold-in** is `.github/workflows/web-feedback-intake.yml`, which runs
  `scripts/feedback_intake_web.py` to merge inbox files into `ops/FEEDBACK.yaml` (reusing the
  tested `slidekit.feedback.store`), regenerate `FEEDBACK.md`, and delete the processed
  files. A bare 👍 with no comment is counted but not turned into an open task; anything
  else (👎, a note, or any comment) becomes an `open` item the nightly acts on.

## One-time deploy (Netlify)

1. **Create the site.** Netlify → *Add new site* → *Import an existing project* → pick this
   repo. Netlify reads [`netlify.toml`](../netlify.toml): publish dir `web`, functions
   `netlify/functions`, edge function auto-detected from `netlify/edge-functions`, no build.
2. **Set environment variables** (Site configuration → Environment variables):
   | Variable | Value |
   |---|---|
   | `SITE_PASSWORD` | the one password that unlocks the site — pick something long |
   | `GITHUB_TOKEN` | a **fine-grained PAT** scoped to this repo only, with **Contents: Read and write** |
   | `GITHUB_REPO` | `victor-palacios/slaides` |
   | `GITHUB_BRANCH` | `main` (optional; this is the default) |
3. **Deploy.** Trigger a deploy. Open the site URL, enter `SITE_PASSWORD`, and you're in.

To create the fine-grained PAT: GitHub → Settings → Developer settings → Fine-grained
tokens → *Generate new token* → **Only select repositories** → this repo → Repository
permissions → **Contents: Read and write**. Nothing else. That token can only commit to
this one repo, so a leak is contained to feedback files (which the CI fold-in re-validates).

## Using it

Open the site on your phone, scroll the layouts, tap **👍 Good** or **👎 Needs work** (tap
again to clear), add an optional note and severity, then **Submit feedback**. You'll get a
confirmation with the commit hash. Within a minute the intake workflow folds your marks into
`ops/FEEDBACK.yaml`, and the (manually run) nightly picks up the `open` items.

## Maintaining it

- **After changing any layout**, regenerate the previews so the gallery matches:
  `python scripts/build_web_previews.py` (the `test_web` suite fails if it's stale).
- **Local preview:** `npx netlify dev` serves the site with the functions; set the same env
  vars in a `.env` (never commit it) to exercise auth + submit end to end.
- The site is `noindex` and password-gated, but treat the URL as semi-private anyway.
