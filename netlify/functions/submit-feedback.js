// Commit a batch of layout-feedback marks to the repo.
//
// The website POSTs { items: [{ component, verdict, comment, severity }] }. This function
// re-verifies the same signed session cookie the edge auth sets (defence in depth — never
// trust that the edge ran), then writes the submission as a JSON file under
// web/feedback-inbox/ via the GitHub Contents API. A CI workflow folds inbox files into
// FEEDBACK.yaml using the tested Python store, so no feedback schema logic is duplicated here.
//
// Required Netlify env vars:
//   SITE_PASSWORD  – same secret the edge auth uses (to verify the session cookie)
//   GITHUB_TOKEN   – a token with contents:write on the repo (fine-grained PAT recommended)
//   GITHUB_REPO    – "owner/name" (e.g. "victor-palacios/slaides")
//   GITHUB_BRANCH  – optional, defaults to "main"

const crypto = require("node:crypto");

const COOKIE = "sk_session";
const MSG = "slaides-v1";
// "add-before" / "add-after" are deck-review requests to insert a NEW slide at that
// position; the comment describes the wanted slide. They are inherently slide-scoped.
const VERDICTS = new Set(["good", "bad", "note", "add-before", "add-after"]);
const ADD_VERDICTS = new Set(["add-before", "add-after"]);
const SEVERITIES = new Set(["low", "med", "high"]);
const SCOPES = new Set(["layout", "slide"]);
const MAX_ITEMS = 200; // deck review can mark many slides of a large deck in one batch
const MAX_COMMENT = 2000;
const MAX_DECK = 120;

function sessionToken(secret) {
  return crypto
    .createHmac("sha256", secret)
    .update(MSG)
    .digest("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function readCookie(header, name) {
  for (const part of (header || "").split(/;\s*/)) {
    const i = part.indexOf("=");
    if (i > -1 && part.slice(0, i) === name) return part.slice(i + 1);
  }
  return null;
}

function safeEqual(a, b) {
  const ab = Buffer.from(String(a));
  const bb = Buffer.from(String(b));
  return ab.length === bb.length && crypto.timingSafeEqual(ab, bb);
}

function json(statusCode, body) {
  return { statusCode, headers: { "content-type": "application/json" }, body: JSON.stringify(body) };
}

exports.handler = async function (event) {
  if (event.httpMethod !== "POST") return json(405, { error: "method not allowed" });

  const secret = process.env.SITE_PASSWORD;
  const token = process.env.GITHUB_TOKEN;
  const repo = process.env.GITHUB_REPO;
  const branch = process.env.GITHUB_BRANCH || "main";
  if (!secret || !token || !repo) {
    return json(500, { error: "server not configured (SITE_PASSWORD / GITHUB_TOKEN / GITHUB_REPO)" });
  }

  // Verify the session cookie independently of the edge.
  const cookie = readCookie(event.headers.cookie || event.headers.Cookie, COOKIE);
  if (!safeEqual(cookie || "", sessionToken(secret))) return json(401, { error: "unauthorized" });

  // Parse + validate the submission.
  let payload;
  try {
    payload = JSON.parse(event.body || "{}");
  } catch {
    return json(400, { error: "invalid JSON" });
  }
  const rawItems = Array.isArray(payload.items) ? payload.items : [];
  if (!rawItems.length) return json(400, { error: "no items" });
  if (rawItems.length > MAX_ITEMS) return json(400, { error: "too many items" });

  const items = [];
  for (const it of rawItems) {
    const component = typeof it.component === "string" ? it.component.slice(0, 80) : "";
    const verdict = VERDICTS.has(it.verdict) ? it.verdict : "note";
    const severity = SEVERITIES.has(it.severity) ? it.severity : "med";
    const comment = typeof it.comment === "string" ? it.comment.slice(0, MAX_COMMENT) : "";
    if (!component) continue;
    // Scope: "layout" (default) vs "slide" (a deck-review mark). Slide-scoped marks carry
    // the deck stem + a 1-based slide index; anything malformed falls back to layout scope
    // so a bad payload can never smuggle deck coordinates onto a layout comment.
    // "add-before"/"add-after" reference a position in a specific deck, so they are
    // always slide-scoped regardless of the submitted scope.
    let scope = ADD_VERDICTS.has(verdict) ? "slide" : (SCOPES.has(it.scope) ? it.scope : "layout");
    const item = { component, verdict, comment, severity, scope };
    if (scope === "slide") {
      const deck = typeof it.deck === "string" ? it.deck.slice(0, MAX_DECK) : "";
      const slide = Number.isInteger(it.slide) ? it.slide : parseInt(it.slide, 10);
      if (deck && Number.isInteger(slide) && slide >= 1) {
        item.deck = deck;
        item.slide = slide;
      } else {
        // Missing/invalid coordinates → treat as layout feedback. An "add slide"
        // request with no position is meaningless, so downgrade it to a plain note.
        item.scope = "layout";
        if (ADD_VERDICTS.has(verdict)) item.verdict = "note";
      }
    }
    items.push(item);
  }
  if (!items.length) return json(400, { error: "no valid items" });

  const submittedAt = new Date().toISOString();
  const record = { submitted_at: submittedAt, source: "web", items };

  // Unique inbox filename: timestamp + short random suffix.
  const stamp = submittedAt.replace(/[:.]/g, "-");
  const suffix = crypto.randomBytes(3).toString("hex");
  const path = `web/feedback-inbox/${stamp}-${suffix}.json`;
  const content = Buffer.from(JSON.stringify(record, null, 2) + "\n", "utf-8").toString("base64");

  const apiUrl = `https://api.github.com/repos/${repo}/contents/${encodeURIComponent(path).replace(/%2F/g, "/")}`;
  const commitMsg = `feedback: ${items.length} mark(s) from web (${submittedAt})`;

  let res;
  try {
    res = await fetch(apiUrl, {
      method: "PUT",
      headers: {
        authorization: `Bearer ${token}`,
        accept: "application/vnd.github+json",
        "content-type": "application/json",
        "user-agent": "slidekit-feedback",
        "x-github-api-version": "2022-11-28",
      },
      body: JSON.stringify({ message: commitMsg, content, branch }),
    });
  } catch (err) {
    return json(502, { error: "github request failed: " + err.message });
  }

  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    return json(502, { error: `github ${res.status}`, detail: detail.slice(0, 300) });
  }
  const body = await res.json().catch(() => ({}));
  return json(200, {
    ok: true,
    saved: items.length,
    path,
    commit: body.commit && body.commit.sha,
  });
};
