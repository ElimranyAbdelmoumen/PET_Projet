# Brave Security Shield v2.0.0 — Usage Guide

Complete documentation for installing, configuring, and integrating Brave Security Shield into your environment.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [User Identity Integration](#user-identity-integration)
5. [Protection Features](#protection-features)
6. [Admin Dashboard (Popup)](#admin-dashboard-popup)
7. [Violation Logging & Audit](#violation-logging--audit)
8. [Advanced Options](#advanced-options)
9. [Troubleshooting](#troubleshooting)
10. [Architecture](#architecture)

---

## Quick Start

### For End Users

1. **Install the extension**
   - Open `brave://extensions`
   - Enable "Developer mode" (top right corner)
   - Click "Load unpacked"
   - Select the `brave-security-extension/` folder
   - Copy the Extension ID from the extension card

2. **Let your IT team know your Extension ID**
   - They'll use it to integrate user identity via `auth_bridge.js`

3. **Access the admin panel**
   - Click the 🔒 icon in Brave's toolbar
   - You'll see protection toggles, watermark settings, and violation logs

### For Developers / IT Teams

1. **Get the Extension ID**
   - From step 1 above

2. **Update `auth_bridge.js`**
   - Replace `__YOUR_EXTENSION_ID__` with the actual ID
   - Include it in your web application

3. **Integrate user login**
   - After authentication, call `initBSSAuth({ uid, email })`
   - See [User Identity Integration](#user-identity-integration)

---

## Installation

### Manual Installation (Development)

```bash
# 1. Clone or download this extension
git clone <repo-url> brave-security-extension
cd brave-security-extension

# 2. Open Brave and navigate to extensions
brave://extensions

# 3. Enable Developer Mode (toggle top-right)

# 4. Click "Load unpacked"

# 5. Select the brave-security-extension/ folder

# 6. Copy the Extension ID (visible on the extension card)
#    Format: abcdefghijklmnopabcdefghijklmnop
```

### Distribution via Policy (Enterprise)

Deploy to managed Brave instances using Brave Policy:

```json
// Windows: C:\ProgramData\BraveHQ\Policies\Policies.json
// macOS:   /Library/Application Support/BraveHQ/Policies/policies.json
// Linux:   /etc/brave/policies/managed/policies.json

{
  "ExtensionInstallForcelist": [
    "YOUR_EXTENSION_ID;https://your-update-server/updates.xml"
  ],
  "ExtensionSettings": {
    "YOUR_EXTENSION_ID": {
      "installation_mode": "force_installed",
      "update_url": "https://your-update-server/updates.xml",
      "allowed_permissions": [
        "activeTab",
        "scripting",
        "storage",
        "contentSettings"
      ]
    }
  }
}
```

### Verify Installation

- 🔒 icon appears in Brave toolbar
- Watermark text appears on any page (usually very faint)
- Right-click context menu is disabled globally
- F12 / DevTools opens trigger a warning overlay

---

## Configuration

### Default Configuration

On first install, the extension creates this default config in `chrome.storage.sync`:

```javascript
{
  blockCopyPaste:   true,
  blockScreenshot:  true,
  blockScreenShare: true,
  blockDevTools:    true,
  allowedOrigins:   [],    // whitelist URLs to bypass protection
  notifyUser:       true,  // show toast notifications
  logViolations:    true,  // record events locally
  
  watermark: {
    enabled:  true,
    uid:      null,        // set by auth_bridge.js
    label:    "CONFIDENTIEL",
    showDate: true,
    opacity:  0.06,        // 0.0 – 1.0
    color:    "#ff0000",   // hex color
    fontSize: 18,          // px
    angle:    -35,         // degrees
    spacing:  200,         // px between tiles
  }
}
```

### Modify Configuration Programmatically

```javascript
// From your extension code or background script
chrome.storage.sync.set({
  bssConfig: {
    blockCopyPaste:   true,
    blockScreenshot:  true,
    blockScreenShare: true,
    blockDevTools:    true,
    allowedOrigins:   [
      "https://internal-tools.company.com",
      "https://admin-panel.company.com"
    ],
    notifyUser:       true,
    logViolations:    true,
    watermark: {
      enabled:  true,
      opacity:  0.12,   // slightly more visible
      color:    "#ef4444",
      fontSize: 20,
      angle:    -30,
      spacing:  180,
    }
  }
}, () => {
  console.log("Config updated");
});
```

### Whitelist Origins (Bypass Protection)

```javascript
chrome.storage.sync.get("bssConfig", ({ bssConfig = {} }) => {
  // Add trusted origins that should NOT be protected
  bssConfig.allowedOrigins = bssConfig.allowedOrigins || [];
  bssConfig.allowedOrigins.push("https://docs.yourcompany.com");
  
  chrome.storage.sync.set({ bssConfig });
});
```

If an origin is whitelisted, the content script returns early and no protection is applied.

---

## User Identity Integration

### Overview

User identity (UID, email, name) is passed from your web application to the extension via `auth_bridge.js`. This identity is then:
- Burned into the watermark on every page
- Burned into the capture-blocking overlay
- Associated with every violation log entry
- Sent to your audit endpoint (if configured)

### Step 1: Get Your Extension ID

```
brave://extensions → locate the extension → copy the ID
```

### Step 2: Update `auth_bridge.js`

Replace the placeholder at the top:

```javascript
// Before:
const BSS_EXTENSION_ID = "__YOUR_EXTENSION_ID__";

// After:
const BSS_EXTENSION_ID = "abcdefghijklmnopabcdefghijklmnop";
```

### Step 3: Include `auth_bridge.js` in Your App

```html
<!-- In your HTML, before any auth code runs -->
<script type="module">
  import { initBSSAuth, clearBSSAuth } from "./auth_bridge.js";
  
  // Make it globally available if needed
  window.initBSSAuth = initBSSAuth;
  window.clearBSSAuth = clearBSSAuth;
</script>
```

### Step 4: Call `initBSSAuth()` After Login

#### Firebase Authentication

```javascript
import { initBSSAuth, clearBSSAuth } from "./auth_bridge.js";
import { getAuth, onAuthStateChanged } from "firebase/auth";

const auth = getAuth();

onAuthStateChanged(auth, user => {
  if (user) {
    initBSSAuth({
      uid:         user.uid,
      email:       user.email,
      displayName: user.displayName,
      avatarUrl:   user.photoURL,
    });
  } else {
    clearBSSAuth();
  }
});
```

#### Auth0

```javascript
import { initBSSAuth, clearBSSAuth } from "./auth_bridge.js";

const auth0Client = await auth0.createAuth0Client({
  domain:      "your-domain.auth0.com",
  client_id:   "YOUR_CLIENT_ID",
});

const user = await auth0Client.getUser();
if (user) {
  initBSSAuth({
    uid:         user.sub,            // e.g. "google-oauth2|..."
    email:       user.email,
    displayName: user.name,
  });
} else {
  clearBSSAuth();
}
```

#### Keycloak

```javascript
import { initBSSAuth, clearBSSAuth } from "./auth_bridge.js";

const keycloak = new Keycloak({
  url:           "https://keycloak.company.com/auth",
  realm:         "my-realm",
  clientId:      "my-client",
});

keycloak.onAuthSuccess = () => {
  initBSSAuth({
    uid:   keycloak.subject,
    email: keycloak.tokenParsed.email,
    displayName: keycloak.tokenParsed.name,
  });
};

keycloak.onAuthLogout = () => {
  clearBSSAuth();
};
```

#### Manual / Custom JWT

```javascript
import { initBSSAuth } from "./auth_bridge.js";

// After verifying your JWT server-side
initBSSAuth({
  uid:         "USR-00123",
  email:       "alice@company.com",
  displayName: "Alice Chen",
});
```

### Step 5: Verify Integration

1. Open your app and log in
2. Click the 🔒 extension icon
3. You should see your user card with initials, email, and UID
4. Watermark should now show your email instead of "CONFIDENTIEL"
5. Try to take a screenshot — the overlay will burn your UID

---

## Protection Features

### 1. Copy / Paste Blocking

**What it blocks:**
- Ctrl/Cmd + C / X / V
- DOM `copy`, `cut`, `paste` events
- Clipboard API (`navigator.clipboard.readText()`, `.writeText()`)
- Drag-and-drop data exfiltration

**Result:**
- Toast notification: "Copier/Coller désactivé sur cette page"
- Violation logged: `Clipboard API blocked: readText`

**Cannot block:**
- Native OS clipboard (copy happens at OS level — only C++ patch can block that)
- Keyboard shortcuts in extensions or other privileged contexts

### 2. Screenshot Blocking

**What it blocks:**
- PrintScreen key
- Page visibility state (tab blur/focus)
- CSS `@media print` attempts
- Text selection (CSS layer)

**Result:**
- On PrintScreen: "Capture neutralisée" + black overlay for 1.8s
- On tab blur: black overlay shows until tab is refocused
- On print: "Ce contenu est protégé — impression désactivée."
- Violation logged: `PrintScreen detected — clipboard cleared`

**Cannot block:**
- External screen capture tools (OBS, Snagit, Win+Shift+S)
  - Only the C++ patch with `OnIsBeingCapturedChanged` can react to those
- Screenshots taken within the OS (hardware-level capture)

### 3. Screen Sharing Blocking

**What it blocks:**
- `navigator.mediaDevices.getDisplayMedia()` (modern APIs)
- Legacy `getUserMedia()` with `mediaSource` constraints
- Any attempt to capture the display for WebRTC or streaming

**Result:**
- `Promise.reject(DOMException: "Screen sharing disabled")`
- Page cannot access screen stream
- Violation logged: `getDisplayMedia blocked`

**Works on:**
- Google Meet, Zoom, Teams, Discord, OBS browser plugin
- Any web app using the standard Permissions API

### 4. DevTools / Inspection Blocking

**7 techniques combined:**

| Technique | Detection | Result |
|-----------|-----------|--------|
| **A. Keyboard shortcuts** | F12, Ctrl+Shift+I/J/C/K, Ctrl+U, Ctrl+S, Ctrl+P | Prevented + logged |
| **B. Context menu** | Right-click "Inspect" | Entirely disabled |
| **C. Window-size delta** | Docked DevTools shrinks inner window | Wall overlay shows |
| **D. Debugger heartbeat** | `debugger;` every 100ms makes DevTools unusable | DevTools becomes frozen when open |
| **E. Console poisoning** | All `console.*` methods replaced with noop | Console becomes silent |
| **F. toString timing** | Native function timing differs when DevTools paused | Timing anomaly detected |
| **G. Wall overlay** | Any of above triggered | Full-screen "ACCÈS REFUSÉ" with UID + timestamp |

**Result:**
- Full-screen dark overlay with lock icon
- Shows user UID, timestamp, and hostname
- Auto-dismisses when DevTools closes
- Violation logged: `DevTools detected via: size-delta`

**Note:** Can be circumvented by:
- Disabling breakpoints in DevTools → Sources
- Using headless browser automation
- Undocking DevTools far from window (requires user action)

Pair with server-side validation for maximum security.

### 5. Watermark Overlay

**What it does:**
- Repeats a tiled SVG pattern across the entire page
- Shows: label (email or custom) + UID + date
- Subtle by default (opacity 0.06) but configurable

**Configuration:**
- **opacity**: 0.0 (invisible) to 1.0 (opaque) — default 0.06
- **color**: hex code — default `#ff0000` (red)
- **angle**: rotation in degrees — default `-35°`
- **spacing**: distance between tiles in px — default `200px`
- **fontSize**: label size in px — default `18px`

**Visual result:**
```
                    CONFIDENTIEL
                    USR-00123
                    2026-04-19
              (repeated diagonally across page)
```

---

## Admin Dashboard (Popup)

Click the 🔒 icon in the Brave toolbar to open the popup.

### Sections

#### 1. **Utilisateur connecté** (User Card)
- Shows logged-in user (email + UID)
- Initials avatar with color background
- "Déconnecter" button clears stored identity

#### 2. **Protections** (Toggle Switches)
- **Bloquer Copier / Coller** — disables copy/paste/cut
- **Bloquer les Captures d'écran** — blocks PrintScreen
- **Bloquer le Partage d'écran** — blocks getDisplayMedia
- **Bloquer l'Inspection (DevTools)** — blocks F12, DevTools shortcuts, DevTools opening
- **Notifications toast** — show/hide toast messages when violations occur

All toggles sync to `bssConfig` in `chrome.storage.sync` immediately.

#### 3. **Watermark UID** (Sliders & Color Picker)
- **Activer le watermark** — toggle on/off
- **Opacité** — 1% to 30% (displayed as percentage)
- **Angle** — -60° to 0° (displayed in degrees)
- **Couleur** — color picker (hex value)

Changes sync in real-time. Page reloads to see changes.

#### 4. **Journal** (Violation Log)
- Shows up to 40 most recent violations
- Each entry displays:
  - Origin (domain name)
  - User UID (if authenticated)
  - Violation detail (e.g. "Clipboard shortcut blocked: C")
  - Timestamp (local time)
- **Effacer le journal** button clears all logs

Log is stored in `chrome.storage.local` (not synced across devices).

---

## Violation Logging & Audit

### Local Storage

All violations are stored locally in `chrome.storage.local.violationLog` (max 200 entries):

```javascript
{
  detail:  "PrintScreen detected — clipboard cleared",
  origin:  "https://app.company.com",
  tab:     "https://app.company.com/documents",
  uid:     "USR-00123",
  email:   "alice@company.com",
  ts:      1713534727000  // milliseconds since epoch
}
```

View in popup → Journal tab.

### Remote Audit Endpoint (Optional)

To forward violations to your server in real-time:

#### 1. Set the endpoint in `background.js`

```javascript
// Line ~10, replace null with your endpoint
const AUDIT_ENDPOINT = "https://api.company.com/security/violations";
```

#### 2. Expected Request Format

```http
POST /security/violations HTTP/1.1
Host: api.company.com
Content-Type: application/json

{
  "uid":     "USR-00123",
  "detail":  "DevTools detected via: size-delta",
  "origin":  "https://app.company.com",
  "tab":     "https://app.company.com/dashboard",
  "ts":      1713534727000
}
```

#### 3. Server Response

Any HTTP 200-299 is considered success. Failures are logged in browser console but do not halt the extension.

#### 4. Example Server Endpoint (Node.js Express)

```javascript
const express = require("express");
const app = express();
app.use(express.json());

app.post("/security/violations", async (req, res) => {
  const { uid, detail, origin, tab, ts } = req.body;
  
  console.log(`[VIOLATION] UID: ${uid} | ${detail} | ${origin}`);
  
  // Store in database
  await db.violations.insertOne({
    uid, detail, origin, tab, ts,
    receivedAt: new Date(),
    ipAddress: req.ip,
  });
  
  // Optional: alert security team if severity threshold met
  if (detail.includes("DevTools detected")) {
    await alertSecurityTeam(uid, detail);
  }
  
  res.json({ ok: true });
});

app.listen(3000);
```

---

## Advanced Options

### Aggressive Mode: Redirect on DevTools Detect

In `content_script.js`, line ~320, uncomment:

```javascript
function onDetected(via) {
  logViolation("DevTools detected via: " + via);
  notify("⚠ Inspection détectée — session enregistrée");
  showWall();

  // Uncomment to redirect to blank page (prevents any interaction)
  // window.location.replace("about:blank");
  
  // Or redirect to login/logout:
  // window.location.replace("https://company.com/logout");
}
```

**Effect:** User is immediately redirected when DevTools opens. Cannot be undone by closing DevTools.

### Disable Notifications

Toggle off in popup → **Notifications toast**, or programmatically:

```javascript
chrome.storage.sync.get("bssConfig", ({ bssConfig = {} }) => {
  bssConfig.notifyUser = false;
  chrome.storage.sync.set({ bssConfig });
});
```

### Disable Logging

Toggle stays in popup, but to disable server reporting:

```javascript
// In background.js, line ~10
const AUDIT_ENDPOINT = null; // disables remote reporting
```

Local logging still happens (popup journal will fill). To disable that, toggle in popup.

### Multiple Extension Instances

Install the extension in multiple Brave profiles:

```
Profile 1: Extension ID = abc...xyz (Development)
Profile 2: Extension ID = def...uvw (Production)
```

Each has its own storage and configuration. Use the correct ID in `auth_bridge.js` for each environment.

### Stealth Mode: Hide Extension Icon

Hide the 🔒 icon while keeping protection active:

```javascript
// In manifest.json, line ~37, comment out the action section:
// "action": {
//   "default_popup": "popup.html",
//   "default_title": "Brave Security Shield"
// },
```

Repack and install. Icon won't show, but protection still runs.

---

## Troubleshooting

### Issue: Extension doesn't load / "Manifest invalid"

**Fix:**
1. Verify `manifest.json` is valid JSON: `node -e "require('./manifest.json')"`
2. Check `manifest_version: 3` (MV2 deprecated)
3. Ensure `minimum_chrome_version: 109` or higher

### Issue: Watermark not showing

**Debug:**
1. Open popup → ensure "Activer le watermark" is ON
2. Check `opacity` is > 0 (default 0.06)
3. Try raising opacity to 0.2 temporarily to verify
4. Check console for errors: press `Ctrl+Shift+J` → no red errors?
5. Page might have `pointer-events: none` or layering that hides it

**Fix:**
```javascript
// In content_script.js, check buildWatermark() is called:
if (CONFIG.watermark.enabled) buildWatermark();
```

### Issue: Copy/paste still works

**Cause:** Extension is not injected into this frame (e.g., sandboxed iframe)

**Fix:**
1. Ensure `"all_frames": true` in manifest.json
2. Check page doesn't have strict CSP blocking script injection
3. Page might be whitelisted — check popup for `allowedOrigins`

### Issue: DevTools opens without wall overlay

**Causes:**
1. Window not resized much (delta < 160px threshold)
2. DevTools is detached and placed on a separate monitor
3. Console is not open (timing attack won't trigger)

**Fix:**
1. Try F12 to dock DevTools (should trigger size-delta)
2. Try Ctrl+Shift+J to open console (triggers heartbeat)
3. Check browser console for logged violations: `chrome.storage.local.get("violationLog")`

### Issue: Auth not working / UID not shown in watermark

**Check:**
1. Extension ID in `auth_bridge.js` matches extension ID from `brave://extensions`
2. After login, click popup — do you see user card?
3. If not, check browser console: `initBSSAuth()` called?

**Debug:**
```javascript
// In your app, after calling initBSSAuth()
setTimeout(() => {
  getBSSUser().then(user => console.log("Current user:", user));
}, 1000);
```

### Issue: Violations not reaching audit server

**Check:**
1. Is `AUDIT_ENDPOINT` set in `background.js` (not null)?
2. Is endpoint HTTPS (not HTTP)?
3. Can you curl the endpoint from your machine?
   ```bash
   curl -X POST https://api.company.com/security/violations \
     -H "Content-Type: application/json" \
     -d '{"uid":"test","detail":"test"}'
   ```
4. Server logs — is request reaching it?
5. CORS headers OK? (Brave makes fetch with `keepalive: true`)

**Fix:**
```javascript
// In background.js, temporarily add debugging:
async function reportToAudit(entry) {
  if (!AUDIT_ENDPOINT) return;
  console.warn("[BSS] Sending audit:", entry); // debug line
  try {
    const res = await fetch(AUDIT_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry),
      keepalive: true,
    });
    console.warn("[BSS] Audit response:", res.status); // debug line
  } catch (e) {
    console.error("[BSS] Audit failed:", e.message);
  }
}
```

Then open browser console (`Ctrl+Shift+J`) and trigger a violation (try to copy something) — you'll see the debug logs.

---

## Architecture

### Data Flow

```
┌─────────────────────┐
│ content_script.js   │  Runs at document_start in every frame
│ (isolated world)    │  • Blocks copy/paste/screenshot/devtools
└──────────┬──────────┘  • Injects watermark SVG
           │             • Reports violations to background
           │
      chrome.runtime.sendMessage
           │
           ▼
┌─────────────────────┐
│ background.js       │  Service Worker (persistent)
│ (extension context) │  • Stores violations in chrome.storage.local
└──────────┬──────────┘  • Manages user identity (bssUser)
           │             • Forwards to audit endpoint
           │
    chrome.storage
           │
           ▼
┌─────────────────────┐
│ popup.html/js       │  UI only when user clicks icon
│ (extension context) │  • Displays toggles, watermark settings
└─────────────────────┘  • Shows violation log & user card

┌─────────────────────────────────────────┐
│ Your Web App                            │
│  ─────────────────────────────────────  │
│ auth_bridge.js                          │  Import in your app
│  • initBSSAuth({ uid, email })      │  • Call after login
│  • clearBSSAuth()                  │  • Call after logout
└─────────────────────────────────────────┘
         ▲
         │ chrome.runtime.sendMessage
         │
    ┌────┴──────────────────┐
    │ BSS Extension         │
    │ (via auth_bridge.js)  │
    └───────────────────────┘
```

### Storage Schema

#### `chrome.storage.sync` (synced across user's devices)

```javascript
{
  bssConfig: {
    blockCopyPaste:   boolean,
    blockScreenshot:  boolean,
    blockScreenShare: boolean,
    blockDevTools:    boolean,
    allowedOrigins:   string[],
    notifyUser:       boolean,
    logViolations:    boolean,
    watermark: {
      enabled:  boolean,
      uid:      string | null,
      label:    string,
      showDate: boolean,
      opacity:  number (0.0–1.0),
      color:    string (hex),
      fontSize: number,
      angle:    number,
      spacing:  number,
    }
  },
  
  bssUser: {
    uid:         string,
    email:       string | null,
    displayName: string | null,
    avatarUrl:   string | null,
    ts:          number (timestamp)
  }
}
```

#### `chrome.storage.local` (device-only, not synced)

```javascript
{
  violationLog: [
    {
      detail:  string,
      origin:  string (URL origin),
      tab:     string (full URL) | null,
      uid:     string,
      email:   string | null,
      ts:      number (milliseconds)
    },
    // ... up to 200 entries
  ]
}
```

### Security Model

**In-scope:**
- Web-based threats (copy/paste, screenshots within browser, DevTools inspection, screen sharing)
- Session-level logging and audit trail

**Out-of-scope:**
- OS-level clipboard access (requires system-level DLP software)
- External capture tools (OBS, Snagit, Windows Clipart Tool)
  - Requires OS permissions API or C++ patch integration
- Compromised OS or malware
- Browser extensions installed with higher privileges

**Paired Controls Recommended:**
- Server-side validation of all sensitive data operations
- Network inspection (DLP appliance) for outbound data
- MDM/Intune device policy enforcement
- OS-level DLP agents (Windows Information Protection, macOS data classification)
- Privileged Access Management (PAM) for admin sessions

---

## Support & Contribution

### Reporting Issues

Open an issue on GitHub or contact your IT team with:
1. Browser version: `brave://version`
2. Extension version: `brave://extensions` → BSS card
3. Steps to reproduce
4. Browser console logs: `Ctrl+Shift+J`
5. Recent violations: popup → Journal

### Custom Builds

Modify `manifest.json`, `content_script.js`, or `background.js` as needed. Repack:

```bash
# Create .crx for distribution (requires private key)
brave --pack-extension=/path/to/brave-security-extension \
      --pack-extension-key=/path/to/key.pem

# For testing: just load unpacked from brave://extensions
```

### License

Brave Security Shield is provided as-is. Customize and deploy freely within your organization.

---

**Version:** 2.0.0  
**Last Updated:** April 2026  
**Minimum Brave Version:** 109+