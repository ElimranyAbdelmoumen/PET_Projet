// Initialise le watermark et l'identité utilisateur dans l'extension BSS.
// uid et username sont injectés par Jinja2 dans chaque template.
import { initBSSAuth } from "./auth_bridge.js";

if (typeof BSS_USER_ID !== "undefined" && BSS_USER_ID) {
  initBSSAuth({ uid: String(BSS_USER_ID), displayName: BSS_USERNAME || null });
}
