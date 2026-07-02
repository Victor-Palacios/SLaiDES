// Single-password gate for the whole site (the operator is the only user).
//
// Runs at the edge on every request. If the request carries a valid session cookie it
// falls through to the site; otherwise it serves a minimal password page. Submitting the
// correct SITE_PASSWORD sets a signed, HttpOnly cookie (an HMAC of a constant keyed by the
// password — no session store needed) and redirects in. This is intentionally simpler than
// Supabase/OAuth: one person, one secret, zero third-party auth service.
//
// The session token is HMAC-SHA256(key=SITE_PASSWORD, msg="slaides-v1"), base64url. The
// submit function recomputes the same token to authorise writes, so the two stay in lockstep.

const COOKIE = "sk_session";
const MSG = "slaides-v1";
const MAX_AGE = 60 * 60 * 24 * 30; // 30 days

async function sessionToken(secret) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(MSG));
  let bin = "";
  for (const b of new Uint8Array(sig)) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function readCookie(req, name) {
  const raw = req.headers.get("cookie") || "";
  for (const part of raw.split(/;\s*/)) {
    const i = part.indexOf("=");
    if (i > -1 && part.slice(0, i) === name) return part.slice(i + 1);
  }
  return null;
}

function safeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function loginPage(error) {
  return new Response(
    `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark"><title>slidekit · sign in</title>
<style>
  :root{color-scheme:light dark}
  body{margin:0;min-height:100vh;display:grid;place-items:center;
       font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
       background:#0f1214;color:#e6edf3}
  form{background:#181c1f;border:1px solid #2a3036;border-radius:14px;padding:28px 24px;
       width:min(360px,90vw);box-shadow:0 8px 30px rgba(0,0,0,.5)}
  h1{font-size:18px;margin:0 0 4px} p{margin:0 0 18px;color:#9aa4ad;font-size:13px}
  input{width:100%;box-sizing:border-box;padding:12px;border-radius:10px;border:1px solid #2a3036;
        background:#0f1214;color:#e6edf3;font-size:16px}
  button{width:100%;margin-top:12px;padding:12px;border:0;border-radius:10px;background:#3fb37f;
         color:#fff;font-size:16px;font-weight:600;cursor:pointer}
  .err{color:#e5675a;font-size:13px;margin:10px 0 0}
</style></head><body>
<form method="POST" action="/__auth">
  <h1>slidekit layout feedback</h1>
  <p>Enter the site password to continue.</p>
  <input type="password" name="password" autocomplete="current-password" autofocus placeholder="Password">
  <button type="submit">Sign in</button>
  ${error ? `<p class="err">${error}</p>` : ""}
</form></body></html>`,
    { status: error ? 401 : 200, headers: { "content-type": "text/html; charset=utf-8" } },
  );
}

export default async function (request, context) {
  const secret = Netlify.env.get("SITE_PASSWORD");
  if (!secret) {
    return new Response(
      "SITE_PASSWORD is not configured. Set it in the Netlify site environment variables.",
      { status: 500, headers: { "content-type": "text/plain" } },
    );
  }

  const expected = await sessionToken(secret);
  const url = new URL(request.url);

  // Login submission.
  if (request.method === "POST" && url.pathname === "/__auth") {
    const form = await request.formData();
    const submitted = String(form.get("password") || "");
    if (!safeEqual(submitted, secret)) return loginPage("Incorrect password.");
    const cookie =
      `${COOKIE}=${expected}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=${MAX_AGE}`;
    return new Response("", { status: 303, headers: { location: "/", "set-cookie": cookie } });
  }

  // Already authenticated → let the request through to the site/functions.
  if (safeEqual(readCookie(request, COOKIE) || "", expected)) {
    return context.next();
  }

  // Unauthenticated: an API call gets a clean 401; a page gets the password form.
  if (url.pathname.startsWith("/.netlify/functions/")) {
    return new Response(JSON.stringify({ error: "unauthorized" }), {
      status: 401,
      headers: { "content-type": "application/json" },
    });
  }
  return loginPage(null);
}

export const config = { path: "/*" };
