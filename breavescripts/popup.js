/**
 * Brave Security Shield  —  popup.js  v2.0.0
 */

// ── Helpers ───────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const esc = s => { const d = document.createElement("div"); d.textContent = String(s||""); return d.innerHTML; };

// ── Toggle keys that map 1-to-1 with bssConfig booleans ──────────────────────
const TOGGLE_KEYS = ["blockCopyPaste","blockScreenshot","blockScreenShare","blockDevTools","notifyUser"];

// ── Load saved config and user on popup open ──────────────────────────────────
chrome.storage.sync.get(["bssConfig","bssUser"], ({ bssConfig = {}, bssUser }) => {

  // Toggles
  TOGGLE_KEYS.forEach(k => {
    const el = $(k);
    if (el) el.checked = bssConfig[k] !== false; // default true
  });

  // Watermark sliders
  const wm = bssConfig.watermark || {};
  const opacity = Math.round((wm.opacity ?? 0.06) * 100);
  const angle   = wm.angle ?? -35;
  const color   = wm.color || "#ff0000";

  if ($("wmEnabled")) $("wmEnabled").checked = wm.enabled !== false;
  if ($("wmOpacity")) { $("wmOpacity").value = opacity; $("opacityVal").textContent = opacity + "%"; }
  if ($("wmAngle"))   { $("wmAngle").value   = angle;   $("angleVal").textContent   = angle  + "°"; }
  if ($("wmColor"))   $("wmColor").value = color;

  renderUserCard(bssUser);
});

// ── Save on toggle change ─────────────────────────────────────────────────────
TOGGLE_KEYS.forEach(k => {
  const el = $(k);
  if (!el) return;
  el.addEventListener("change", () => {
    chrome.storage.sync.get("bssConfig", ({ bssConfig = {} }) => {
      bssConfig[k] = el.checked;
      chrome.storage.sync.set({ bssConfig });
    });
  });
});

// ── Save watermark settings on change ────────────────────────────────────────
function saveWatermark() {
  const enabled = $("wmEnabled")?.checked ?? true;
  const opacity = (parseInt($("wmOpacity")?.value) || 6) / 100;
  const angle   = parseInt($("wmAngle")?.value) ?? -35;
  const color   = $("wmColor")?.value || "#ff0000";

  $("opacityVal").textContent = Math.round(opacity * 100) + "%";
  $("angleVal").textContent   = angle + "°";

  chrome.storage.sync.get("bssConfig", ({ bssConfig = {} }) => {
    if (!bssConfig.watermark) bssConfig.watermark = {};
    Object.assign(bssConfig.watermark, { enabled, opacity, angle, color });
    chrome.storage.sync.set({ bssConfig });
  });
}

["wmEnabled","wmOpacity","wmAngle","wmColor"].forEach(id => {
  $( id)?.addEventListener("input",  saveWatermark);
  $(id)?.addEventListener("change", saveWatermark);
});

// ── User identity card ────────────────────────────────────────────────────────
function renderUserCard(user) {
  const card = $("user-card");
  if (!card) return;

  if (!user) {
    card.innerHTML =
      '<p style="font-size:11px;color:#475569;line-height:1.5">' +
      'Aucun utilisateur connecté.<br>' +
      'Appelez <code style="color:#f97316">initBSSAuth({uid, email})</code><br>' +
      'depuis votre application web.</p>';
    return;
  }

  const initials = ((user.displayName || user.email || user.uid || "?")
    .split(/[\s@._\-]+/).slice(0, 2)
    .map(p => (p[0] || "").toUpperCase()).join("")) || "?";

  card.innerHTML =
    '<div style="display:flex;align-items:center;gap:10px">' +
      '<div style="width:34px;height:34px;border-radius:50%;background:#f9731620;' +
        'border:1px solid #f9731640;display:flex;align-items:center;justify-content:center;' +
        'font-size:12px;font-weight:600;color:#f97316;flex-shrink:0">' + esc(initials) + '</div>' +
      '<div style="min-width:0">' +
        '<div style="font-size:12px;font-weight:600;color:#e2e8f0;white-space:nowrap;' +
          'overflow:hidden;text-overflow:ellipsis">' +
          esc(user.displayName || user.email || user.uid) + '</div>' +
        '<div style="font-size:10px;color:#f97316;font-family:monospace;margin-top:2px">' +
          esc(user.uid) + '</div>' +
        (user.email
          ? '<div style="font-size:10px;color:#64748b;margin-top:1px">' + esc(user.email) + '</div>'
          : '') +
      '</div>' +
    '</div>';
}

$("logout-btn")?.addEventListener("click", () => {
  chrome.storage.sync.remove("bssUser", () => {
    renderUserCard(null);
    // Clear UID from watermark config too
    chrome.storage.sync.get("bssConfig", ({ bssConfig = {} }) => {
      if (bssConfig.watermark) {
        bssConfig.watermark.uid   = null;
        bssConfig.watermark.label = "CONFIDENTIEL";
      }
      chrome.storage.sync.set({ bssConfig });
    });
  });
});

// ── Violation log ─────────────────────────────────────────────────────────────
function loadLog() {
  chrome.storage.local.get({ violationLog: [] }, ({ violationLog }) => {
    $("log-count").textContent = "(" + violationLog.length + ")";
    const list = $("log-list");

    if (!violationLog.length) {
      list.innerHTML = '<p style="font-size:11px;color:#334155">Aucune violation détectée.</p>';
      return;
    }

    list.innerHTML = violationLog.slice(0, 40).map(v => {
      let host = v.origin;
      try { host = new URL(v.origin).hostname; } catch (_) {}
      const uid = v.uid && v.uid !== "anonymous"
        ? '<span class="log-uid">[' + esc(v.uid) + ']</span>' : "";
      return '<div class="log-entry">' +
        '<span class="log-origin">' + esc(host) + '</span>' + uid +
        ' — ' + esc(v.detail) + '<br>' +
        '<span style="font-size:10px;color:#475569">' +
          new Date(v.ts).toLocaleTimeString() +
        '</span></div>';
    }).join("");
  });
}

loadLog();
$("clear-log")?.addEventListener("click", () =>
  chrome.storage.local.set({ violationLog: [] }, loadLog)
);
