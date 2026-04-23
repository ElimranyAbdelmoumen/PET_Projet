/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  Brave Security Shield  —  auth_bridge.js  v2.0.0
 *
 *  Include this file in YOUR web application (not in the extension).
 *  It passes the authenticated user's identity to the BSS extension so the
 *  watermark and violation logs carry the real UID.
 *
 *  ── Quick start ─────────────────────────────────────────────────────────
 *
 *  Step 1 — Replace the extension ID below with your own:
 *    brave://extensions → enable Developer mode → copy the ID
 *
 *  Step 2 — Call initBSSAuth() after your auth flow resolves:
 *
 *    // Firebase
 *    import { initBSSAuth } from "./auth_bridge.js";
 *    onAuthStateChanged(auth, user => {
 *      if (user) initBSSAuth({ uid: user.uid, email: user.email });
 *      else      clearBSSAuth();
 *    });
 *
 *    // Auth0
 *    const user = await auth0.getUser();
 *    initBSSAuth({ uid: user.sub, email: user.email, displayName: user.name });
 *
 *    // Keycloak
 *    initBSSAuth({ uid: keycloak.subject, email: keycloak.tokenParsed.email });
 *
 *    // Manual / custom JWT
 *    initBSSAuth({ uid: "USR-00123", email: "alice@company.com" });
 *
 * ═══════════════════════════════════════════════════════════════════════════
 */

// ▶  Replace with your actual extension ID from brave://extensions
const BSS_EXTENSION_ID = "dikpdjlignemlnikaegcblghblbejfjd";

/**
 * Send the authenticated user's identity to the BSS extension.
 *
 * @param {{ uid: string, email?: string, displayName?: string, avatarUrl?: string }} user
 */
export async function initBSSAuth(user) {
  if (!user?.uid) {
    console.warn("[BSS] initBSSAuth: uid is required — call ignored.");
    return;
  }

  const payload = {
    uid:         String(user.uid).slice(0, 128),
    email:       user.email       ? String(user.email).slice(0, 256)       : null,
    displayName: user.displayName ? String(user.displayName).slice(0, 128) : null,
    avatarUrl:   user.avatarUrl   ? String(user.avatarUrl).slice(0, 512)   : null,
  };

  // Method A — direct chrome.runtime IPC (preferred, works when extension is installed)
  if (typeof chrome !== "undefined" && chrome.runtime?.sendMessage) {
    try {
      await sendMessage({ type: "SET_USER", user: payload });
      console.info("[BSS] User identity registered:", payload.uid);
      return;
    } catch (e) {
      console.warn("[BSS] sendMessage failed:", e.message);
    }
  }

  // Method B — postMessage fallback (caught by a content-script bridge if needed)
  window.postMessage({ __bss_set_user__: true, user: payload }, location.origin);
}

/**
 * Clear the stored user identity (call on logout).
 */
export async function clearBSSAuth() {
  if (typeof chrome !== "undefined" && chrome.runtime?.sendMessage) {
    try { await sendMessage({ type: "CLEAR_USER" }); } catch (_) {}
  }
  window.postMessage({ __bss_clear_user__: true }, location.origin);
}

/**
 * Get the currently stored user identity from the extension.
 * @returns {Promise<object|null>}
 */
export async function getBSSUser() {
  if (typeof chrome !== "undefined" && chrome.runtime?.sendMessage) {
    try {
      const res = await sendMessage({ type: "GET_USER" });
      return res?.user || null;
    } catch (_) {}
  }
  return null;
}

// ── Internal helper ───────────────────────────────────────────────────────────
function sendMessage(payload) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(BSS_EXTENSION_ID, payload, res => {
      if (chrome.runtime.lastError) reject(new Error(chrome.runtime.lastError.message));
      else resolve(res);
    });
  });
}
