/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  Brave Security Shield  —  background.js  v2.0.0  (Service Worker)
 *
 *  Responsibilities
 *  ──────────────────────────────────────────────────────────────────────────
 *  • Receive and store violation logs from content_script.js
 *  • Manage connected-user identity (SET / GET / CLEAR)
 *  • Optionally forward violations to a remote audit endpoint
 *  • Register default config on first install
 * ═══════════════════════════════════════════════════════════════════════════
 */

// ── Constants ────────────────────────────────────────────────────────────────
const MAX_LOG_ENTRIES = 200;

/**
 * Replace with your server endpoint to receive real-time violation reports.
 * Set to null to disable remote reporting.
 * Expected POST body: { uid, detail, origin, tab, ts }
 */
const AUDIT_ENDPOINT = null; // e.g. "https://api.yourcompany.com/security/violations"

// ── Message router ───────────────────────────────────────────────────────────
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  switch (msg.type) {

    // Content script → log a security event
    case "VIOLATION_LOG":
      handleViolation(msg, sender);
      return false;

    // auth_bridge.js → store authenticated user
    case "SET_USER":
      setUser(msg.user)
        .then(() => sendResponse({ ok: true }))
        .catch(e => sendResponse({ ok: false, error: e.message }));
      return true; // keep channel open for async response

    // Popup → retrieve current user
    case "GET_USER":
      chrome.storage.sync.get("bssUser", ({ bssUser }) =>
        sendResponse({ user: bssUser || null })
      );
      return true;

    // Popup logout button → clear user identity
    case "CLEAR_USER":
      chrome.storage.sync.remove("bssUser", () => sendResponse({ ok: true }));
      return true;
  }
});

// ── Violation handler ────────────────────────────────────────────────────────
async function handleViolation(msg, sender) {
  const { bssUser = null } = await chrome.storage.sync.get("bssUser");
  const { violationLog = [] } = await chrome.storage.local.get("violationLog");

  const entry = {
    detail:    msg.detail,
    origin:    msg.origin,
    tab:       sender.tab?.url || null,
    uid:       bssUser?.uid   || "anonymous",
    email:     bssUser?.email || null,
    ts:        msg.ts || Date.now(),
  };

  violationLog.unshift(entry);
  if (violationLog.length > MAX_LOG_ENTRIES) violationLog.length = MAX_LOG_ENTRIES;

  await chrome.storage.local.set({ violationLog });
  reportToAudit(entry);
}

// ── User identity ────────────────────────────────────────────────────────────
async function setUser(user) {
  if (!user?.uid) throw new Error("user.uid is required");

  const sanitised = {
    uid:         String(user.uid).slice(0, 128),
    email:       user.email       ? String(user.email).slice(0, 256)       : null,
    displayName: user.displayName ? String(user.displayName).slice(0, 128) : null,
    avatarUrl:   user.avatarUrl   ? String(user.avatarUrl).slice(0, 512)   : null,
    ts:          Date.now(),
  };

  await chrome.storage.sync.set({ bssUser: sanitised });

  // Propagate identity into watermark config
  const { bssConfig = {} } = await chrome.storage.sync.get("bssConfig");
  if (!bssConfig.watermark) bssConfig.watermark = {};
  bssConfig.watermark.uid   = sanitised.uid;
  bssConfig.watermark.label = sanitised.email || sanitised.displayName || sanitised.uid;
  await chrome.storage.sync.set({ bssConfig });
}

// ── Remote audit reporting (optional) ────────────────────────────────────────
async function reportToAudit(entry) {
  if (!AUDIT_ENDPOINT) return;
  try {
    await fetch(AUDIT_ENDPOINT, {
      method:    "POST",
      headers:   { "Content-Type": "application/json" },
      body:      JSON.stringify(entry),
      keepalive: true,
    });
  } catch (e) {
    console.warn("[BraveSecurityShield] Audit report failed:", e.message);
  }
}

// ── First-install defaults ────────────────────────────────────────────────────
chrome.runtime.onInstalled.addListener(({ reason }) => {
  if (reason !== "install") return;
  chrome.storage.sync.set({
    bssConfig: {
      blockCopyPaste:   true,
      blockScreenshot:  true,
      blockScreenShare: true,
      blockDevTools:    true,
      allowedOrigins:   [],
      notifyUser:       true,
      logViolations:    true,
      watermark: {
        enabled:  true,
        uid:      null,
        label:    "CONFIDENTIEL",
        showDate: true,
        opacity:  0.06,
        color:    "#ff0000",
        fontSize: 18,
        angle:    -35,
        spacing:  200,
      },
    },
  });
});
