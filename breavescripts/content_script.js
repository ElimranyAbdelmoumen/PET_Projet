/**
 * ═══════════════════════════════════════════════════════════════════════════
 *  Brave Security Shield  —  content_script.js  v2.0.0
 *  Runs at document_start in every frame (main + all iframes).
 *
 *  Protections
 *  ──────────────────────────────────────────────────────────────────────────
 *  1. Copy / Paste / Cut      — DOM events + Clipboard API + keyboard
 *  2. Screenshots             — CSS layer + PrintScreen key + visibility hook
 *  3. Screen Sharing          — getDisplayMedia override (main-world injection)
 *  4. DevTools / Inspection   — F12, shortcuts, size-delta, debugger heartbeat,
 *                               console poisoning, toString timing
 *  5. Watermark               — repeated SVG tile with user UID burned in
 * ═══════════════════════════════════════════════════════════════════════════
 */

(function BraveSecurityShield() {
  "use strict";

  // ── Default configuration (merged from chrome.storage.sync at init) ──────
  const CONFIG = {
    blockCopyPaste:   true,
    blockScreenshot:  true,
    blockScreenShare: true,
    blockDevTools:    true,
    allowedOrigins:   [],     // e.g. ["https://intranet.example.com"]
    notifyUser:       true,
    logViolations:    true,

    watermark: {
      enabled:  true,
      uid:      null,          // injected by auth_bridge.js via chrome.storage
      label:    "CONFIDENTIEL",
      showDate: true,
      opacity:  0.06,          // 0.0 – 1.0  (0.06 subtle, 0.15 visible)
      color:    "#ff0000",
      fontSize: 18,
      angle:    -35,
      spacing:  200,
    },
  };

  // ── Whitelist check ──────────────────────────────────────────────────────
  const ORIGIN = location.origin;
  if (CONFIG.allowedOrigins.includes(ORIGIN)) return;


  // ═══════════════════════════════════════════════════════════════════════
  // 1.  BLOCK COPY / PASTE / CUT
  // ═══════════════════════════════════════════════════════════════════════
  function blockClipboard() {

    // — DOM events (capture phase beats any page handler) —
    ["copy", "cut", "paste"].forEach(evt =>
      document.addEventListener(evt, stopAndLog, { capture: true, passive: false })
    );

    // — Clipboard API prototype override —
    if (navigator.clipboard) {
      const proto = Object.getPrototypeOf(navigator.clipboard);
      const deny  = (name) => function () {
        logViolation("Clipboard API blocked: " + name);
        return Promise.reject(new DOMException("Not allowed", "NotAllowedError"));
      };
      proto.readText  = deny("readText");
      proto.writeText = deny("writeText");
      proto.read      = deny("read");
      proto.write     = deny("write");
    }

    // — Keyboard shortcuts: Ctrl/Cmd + C / X / V / A —
    document.addEventListener("keydown", e => {
      const ctrl = e.ctrlKey || e.metaKey;
      if (ctrl && ["c","x","v","a"].includes(e.key.toLowerCase())) {
        e.preventDefault();
        e.stopImmediatePropagation();
        logViolation("Clipboard shortcut blocked: Ctrl+" + e.key.toUpperCase());
        notify("Copier/Coller désactivé sur cette page");
      }
    }, { capture: true });

    // — Drag-and-drop exfiltration —
    document.addEventListener("dragstart", stopAndLog, { capture: true, passive: false });
  }

  function stopAndLog(e) {
    e.preventDefault();
    e.stopImmediatePropagation();
    logViolation(e.type + " blocked");
    notify("Action \"" + e.type + "\" bloquée");
  }


  // ═══════════════════════════════════════════════════════════════════════
  // 2.  BLOCK SCREENSHOTS
  // ═══════════════════════════════════════════════════════════════════════
  function blockScreenshots() {

    // — Programmatic CSS (catches late-injected iframes missed by screen_block.css) —
    const style = document.createElement("style");
    style.textContent =
      "* { -webkit-user-select:none!important; user-select:none!important; }" +
      "@media print { body *{display:none!important} " +
      "body::after{content:'Contenu protégé';display:block!important;" +
      "position:fixed;inset:0;background:#000;color:#fff;" +
      "font:20px system-ui;text-align:center;padding-top:40vh} }";
    (document.head || document.documentElement).appendChild(style);

    // — Black overlay element (reused by watermark module for UID burn-in) —
    const overlay = document.createElement("div");
    overlay.id = "__bss_overlay__";
    overlay.style.cssText =
      "display:none;position:fixed;inset:0;z-index:2147483647;" +
      "background:#0a0a0a;color:#fff;font-size:20px;" +
      "align-items:center;justify-content:center;" +
      "flex-direction:column;gap:12px;font-family:system-ui,sans-serif;";
    overlay.textContent = "Contenu protégé — capture désactivée";
    const mountOverlay = () => document.body && document.body.appendChild(overlay);
    if (document.body) mountOverlay();
    else document.addEventListener("DOMContentLoaded", mountOverlay);

    // — PrintScreen key: clear clipboard + show overlay briefly —
    document.addEventListener("keyup", e => {
      if (e.key !== "PrintScreen") return;
      try { navigator.clipboard.writeText(""); } catch (_) {}
      showOverlay(1800);
      logViolation("PrintScreen detected — clipboard cleared");
      notify("Capture neutralisée");
    }, { capture: true });

    // — Visibility change: hide content when tab is backgrounded —
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) showOverlay(0);
      else hideOverlay();
    });
  }

  function showOverlay(ms) {
    const el = document.getElementById("__bss_overlay__");
    if (!el) return;
    el.style.display = "flex";
    if (ms > 0) setTimeout(hideOverlay, ms);
  }

  function hideOverlay() {
    const el = document.getElementById("__bss_overlay__");
    if (el) el.style.display = "none";
  }


  // ═══════════════════════════════════════════════════════════════════════
  // 3.  BLOCK SCREEN SHARING
  // ═══════════════════════════════════════════════════════════════════════
  function blockScreenSharing() {

    // Must run in the page's main world (not extension isolated world)
    // so that the page's own JS sees the override.
    const code = `(function(){
      "use strict";
      if (!navigator.mediaDevices) return;
      Object.defineProperty(navigator.mediaDevices, "getDisplayMedia", {
        value: function() {
          window.dispatchEvent(new CustomEvent("__bss_screenshare__"));
          return Promise.reject(new DOMException("Screen sharing disabled","NotAllowedError"));
        },
        configurable: false, writable: false
      });
      const _legacy = navigator.getUserMedia || navigator.webkitGetUserMedia;
      if (_legacy) {
        navigator.getUserMedia = function(c, ok, err) {
          if (c && c.video && c.video.mediaSource) {
            if (err) err(new DOMException("Blocked","NotAllowedError"));
            return;
          }
          _legacy.call(navigator, c, ok, err);
        };
      }
      try { Object.freeze(navigator.mediaDevices); } catch(_) {}
    })();`;

    const s = document.createElement("script");
    s.textContent = code;
    (document.head || document.documentElement).prepend(s);
    s.remove();

    window.addEventListener("__bss_screenshare__", () => {
      logViolation("getDisplayMedia blocked");
      notify("Partage d'écran bloqué");
    });
  }


  // ═══════════════════════════════════════════════════════════════════════
  // 4.  BLOCK DEVTOOLS / PAGE INSPECTION
  // ═══════════════════════════════════════════════════════════════════════
  function blockDevTools() {

    const THRESHOLD = 160; // px — docked DevTools panel minimum width/height
    let dtOpen = false;

    // ── A. Keyboard shortcuts ──
    document.addEventListener("keydown", e => {
      const ctrl  = e.ctrlKey || e.metaKey;
      const shift = e.shiftKey;
      const k     = e.key;
      const blocked =
        k === "F12" ||
        (ctrl && shift && ["i","I","j","J","c","C","k","K"].includes(k)) ||
        (ctrl && ["u","U","s","S","p","P"].includes(k));

      if (blocked) {
        e.preventDefault();
        e.stopImmediatePropagation();
        logViolation("DevTools shortcut blocked: " + k);
        notify("Inspection désactivée sur cette page");
      }
    }, { capture: true });

    // ── B. Context menu ──
    document.addEventListener("contextmenu", e => {
      e.preventDefault();
      e.stopImmediatePropagation();
      logViolation("Context menu blocked");
    }, { capture: true });

    // ── C. Window-size delta (docked DevTools shrinks innerWidth/Height) ──
    const checkSize = () => {
      const open =
        (window.outerWidth  - window.innerWidth)  > THRESHOLD ||
        (window.outerHeight - window.innerHeight) > THRESHOLD;
      if (open && !dtOpen)  { dtOpen = true;  onDetected("size-delta"); }
      if (!open && dtOpen)  { dtOpen = false; dismissWall(); }
    };
    setInterval(checkSize, 500);
    window.addEventListener("resize", checkSize);

    // ── D. Debugger heartbeat (main-world injection) ──
    const dbgScript = document.createElement("script");
    dbgScript.textContent =
      "(function(){setTimeout(function(){setInterval(function(){debugger;},100);},2000);})();";
    (document.head || document.documentElement).appendChild(dbgScript);
    dbgScript.remove();

    // ── E. Console poisoning (main-world injection) ──
    const cslScript = document.createElement("script");
    cslScript.textContent = `(function(){
      var noop=function(){};
      ["log","warn","error","info","debug","table","dir","group","groupEnd",
       "time","timeEnd","assert","profile","count"].forEach(function(m){
        try{console[m]=noop;}catch(e){}
      });
      try{Object.defineProperty(window,"console",{
        get:function(){return console;},
        set:function(){window.dispatchEvent(new CustomEvent("__bss_dt_console__"));},
        configurable:false
      });}catch(e){}
    })();`;
    (document.head || document.documentElement).appendChild(cslScript);
    cslScript.remove();

    window.addEventListener("__bss_dt_console__", () => {
      logViolation("Console re-assignment attempt detected");
      onDetected("console-override");
    });

    // ── F. toString timing fingerprint ──
    (function () {
      const t0 = performance.now();
      const re = /./;
      re.toString = function () {
        if (performance.now() - t0 > 100) {
          logViolation("DevTools toString timing detected");
          onDetected("timing");
        }
      };
      console.log(re); // triggers toString if DevTools console is open
    })();

    // ── Response ──
    function onDetected(via) {
      logViolation("DevTools detected via: " + via);
      notify("⚠ Inspection détectée — session enregistrée");
      showWall();
    }

    function showWall() {
      if (document.getElementById("__bss_dt_wall__")) return;
      const uid = (CONFIG.watermark && CONFIG.watermark.uid)
        ? CONFIG.watermark.uid
        : ("SESSION-" + Date.now());

      const wall = document.createElement("div");
      wall.id = "__bss_dt_wall__";
      wall.style.cssText =
        "position:fixed;inset:0;z-index:2147483647;" +
        "background:#0a0a0a;display:flex;flex-direction:column;" +
        "align-items:center;justify-content:center;gap:14px;" +
        "font-family:system-ui,monospace,sans-serif;" +
        "color:#f1f5f9;text-align:center;padding:40px;";
      wall.innerHTML =
        "<div style='font-size:48px;line-height:1'>&#128274;</div>" +
        "<div style='font-size:22px;font-weight:700;color:#ef4444;letter-spacing:1px'>ACCÈS REFUSÉ</div>" +
        "<div style='font-size:14px;color:#94a3b8;max-width:340px;line-height:1.6'>" +
          "L&rsquo;inspection de cette page est désactivée.<br>Cette tentative a été enregistrée." +
        "</div>" +
        "<div style='font-family:monospace;font-size:13px;color:#f97316;" +
          "border:1px solid #f9731630;background:#f9731610;" +
          "padding:8px 22px;border-radius:6px'>" +
          "UID&#160;: " + escapeHtml(uid) +
        "</div>" +
        "<div style='font-size:11px;color:#1e293b;margin-top:4px'>" +
          new Date().toISOString() + " &middot; " + escapeHtml(location.hostname) +
        "</div>" +
        "<div style='font-size:11px;color:#334155;margin-top:8px'>" +
          "Fermez les outils de développement pour continuer." +
        "</div>";

      const mount = () => document.body && document.body.appendChild(wall);
      if (document.body) mount();
      else document.addEventListener("DOMContentLoaded", mount);
    }

    function dismissWall() {
      const w = document.getElementById("__bss_dt_wall__");
      if (w) w.remove();
    }
  }


  // ═══════════════════════════════════════════════════════════════════════
  // 5.  WATERMARK OVERLAY  (SVG tile repeated via background-image)
  // ═══════════════════════════════════════════════════════════════════════
  function buildWatermark() {
    const wm = CONFIG.watermark;
    if (!wm.enabled) return;

    const uid      = wm.uid   || "UID-UNKNOWN";
    const dateStr  = wm.showDate ? new Date().toISOString().slice(0, 10) : "";
    const lines    = [wm.label, uid, dateStr].filter(Boolean);
    const S        = wm.spacing;
    const lh       = wm.fontSize + 6;

    const tspans = lines.map((ln, i) =>
      '<tspan x="' + (S / 2) + '" dy="' + (i === 0 ? -(((lines.length - 1) * lh) / 2) : lh) + '">'
      + escapeXml(ln) + "</tspan>"
    ).join("");

    const svg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="' + S + '" height="' + S + '">' +
        '<text transform="translate(' + (S/2) + ',' + (S/2) + ') rotate(' + wm.angle + ')"' +
          ' text-anchor="middle" dominant-baseline="central"' +
          ' font-family="system-ui,monospace" font-size="' + wm.fontSize + '"' +
          ' font-weight="600" letter-spacing="1"' +
          ' fill="' + wm.color + '" opacity="' + wm.opacity + '">' +
        tspans + "</text></svg>";

    const uri = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svg)));

    const div = document.createElement("div");
    div.id = "__bss_watermark__";
    div.style.cssText =
      "position:fixed;inset:0;z-index:2147483640;pointer-events:none;" +
      "background-image:url(\"" + uri + "\");" +
      "background-repeat:repeat;" +
      "background-size:" + S + "px " + S + "px;" +
      "mix-blend-mode:multiply;";

    const inject = () => {
      if (!document.getElementById("__bss_watermark__") && document.body)
        document.body.appendChild(div);
    };
    if (document.body) inject();
    else document.addEventListener("DOMContentLoaded", inject);

    // MutationObserver keeps the watermark alive in SPAs
    const guard = new MutationObserver(inject);
    const arm = () => guard.observe(document.body, { childList: true });
    if (document.body) arm();
    else document.addEventListener("DOMContentLoaded", arm);

    // Enrich the screenshot-blocking overlay with the UID
    const patchOverlay = () => {
      const ol = document.getElementById("__bss_overlay__");
      if (!ol) return;
      ol.innerHTML =
        "<div style='font-family:monospace;font-size:12px;color:#ef4444;" +
          "letter-spacing:2px;text-transform:uppercase;opacity:.8'>" +
          escapeHtml(wm.label) + "</div>" +
        "<div style='font-size:20px;font-weight:600;color:#f1f5f9'>Contenu protégé</div>" +
        "<div style='font-family:monospace;font-size:14px;color:#f97316;" +
          "border:1px solid #f9731633;background:#f9731610;" +
          "padding:8px 20px;border-radius:6px'>UID&#160;: " + escapeHtml(uid) + "</div>" +
        "<div style='font-family:monospace;font-size:11px;color:#475569;margin-top:4px'>" +
          escapeHtml(new Date().toISOString()) + " &middot; " + escapeHtml(location.hostname) +
        "</div>" +
        "<div style='font-size:11px;color:#334155;margin-top:8px;max-width:320px;line-height:1.5'>" +
          "Toute capture d&rsquo;écran a été enregistrée et associée à votre identifiant." +
        "</div>";
    };
    if (document.body) patchOverlay();
    else document.addEventListener("DOMContentLoaded", patchOverlay);
  }


  // ═══════════════════════════════════════════════════════════════════════
  // UTILITIES
  // ═══════════════════════════════════════════════════════════════════════
  function notify(msg) {
    if (!CONFIG.notifyUser) return;
    const show = () => {
      if (!document.body) return;
      const t = document.createElement("div");
      t.style.cssText =
        "position:fixed;bottom:24px;right:24px;z-index:2147483646;" +
        "background:#1a1a2e;color:#e2e8f0;padding:11px 18px;" +
        "border-radius:8px;font-family:system-ui,sans-serif;font-size:13px;" +
        "border-left:3px solid #f97316;max-width:320px;" +
        "line-height:1.4;transition:opacity .3s;";
      t.textContent = "\uD83D\uDD12 " + msg;
      document.body.appendChild(t);
      setTimeout(() => { t.style.opacity = "0"; }, 2500);
      setTimeout(() => t.remove(), 2800);
    };
    if (document.body) show();
    else document.addEventListener("DOMContentLoaded", show);
  }

  function logViolation(detail) {
    if (!CONFIG.logViolations) return;
    try {
      chrome.runtime.sendMessage({
        type: "VIOLATION_LOG",
        detail,
        origin: ORIGIN,
        ts: Date.now(),
      });
    } catch (_) {}
  }

  function escapeXml(s) {
    return String(s)
      .replace(/&/g,"&amp;").replace(/</g,"&lt;")
      .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = String(s);
    return d.innerHTML;
  }


  // ═══════════════════════════════════════════════════════════════════════
  // INIT  —  load config + user identity, then arm all modules
  // ═══════════════════════════════════════════════════════════════════════
  function arm() {
    if (CONFIG.blockCopyPaste)   blockClipboard();
    if (CONFIG.blockScreenshot)  blockScreenshots();
    if (CONFIG.blockScreenShare) blockScreenSharing();
    if (CONFIG.blockDevTools)    blockDevTools();
    if (CONFIG.watermark.enabled) buildWatermark();
  }

  try {
    chrome.storage.sync.get(["bssConfig", "bssUser"], ({ bssConfig, bssUser }) => {
      if (bssConfig) {
        // Deep-merge watermark sub-object
        const wm = bssConfig.watermark;
        Object.assign(CONFIG, bssConfig);
        if (wm) Object.assign(CONFIG.watermark, wm);
      }
      if (bssUser) {
        CONFIG.watermark.uid = bssUser.uid || CONFIG.watermark.uid;
        if (bssUser.email) CONFIG.watermark.label = bssUser.email;
      }
      arm();
    });
  } catch (_) {
    // Isolated frame with no extension context — arm with defaults
    arm();
  }

})();
