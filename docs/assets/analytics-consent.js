(function () {
  "use strict";

  const measurementId = "G-BMKYWEPNHB";
  const consentKey = "sandroAnalyticsConsentV1";
  const productionHost = "sandro-abashishvili.de";
  document.documentElement.dataset.analyticsConsentMode = "basic";
  let banner = null;
  let analyticsLoaded = false;

  function readConsent() {
    try { return localStorage.getItem(consentKey); } catch (_) { return null; }
  }

  function setConsent(value) {
    if (typeof window.gtag !== "function") return;
    window.gtag("consent", "update", {
      analytics_storage: value,
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
    });
  }

  function loadAnalytics() {
    if (analyticsLoaded || location.hostname !== productionHost) return;
    analyticsLoaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    window.gtag("consent", "default", {
      analytics_storage: "denied",
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
    });
    setConsent("granted");
    window.gtag("js", new Date());
    window.gtag("config", measurementId, {
      allow_google_signals: false,
      allow_ad_personalization_signals: false,
    });
    const script = document.createElement("script");
    script.async = true;
    script.dataset.analyticsId = measurementId;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`;
    document.head.appendChild(script);
  }

  function removeAnalyticsCookies() {
    document.cookie.split(";").forEach((part) => {
      const name = part.split("=")[0].trim();
      if (!/^_ga(?:_|$)/.test(name)) return;
      const expired = "expires=Thu, 01 Jan 1970 00:00:00 GMT";
      document.cookie = `${name}=;${expired};path=/;SameSite=Lax`;
      document.cookie = `${name}=;${expired};path=/;domain=${location.hostname};SameSite=Lax`;
      document.cookie = `${name}=;${expired};path=/;domain=.${location.hostname};SameSite=Lax`;
    });
  }

  function saveConsent(value) {
    try { localStorage.setItem(consentKey, value); } catch (_) {}
    if (value === "granted") loadAnalytics();
    else {
      setConsent("denied");
      removeAnalyticsCookies();
    }
    banner?.remove();
    banner = null;
  }

  function showBanner() {
    banner?.remove();
    banner = document.createElement("aside");
    banner.className = "consent-banner";
    banner.setAttribute("role", "dialog");
    banner.setAttribute("aria-modal", "true");
    banner.setAttribute("aria-labelledby", "consent-title");
    banner.innerHTML = `
      <div>
        <strong id="consent-title">Optionale Statistik</strong>
        <p>Mit Ihrer Einwilligung verwenden wir Google Analytics für die Nutzungsanalyse. Der Google-Tag wird erst nach Ihrer Zustimmung geladen. <a href="/datenschutz/">Mehr erfahren</a></p>
      </div>
      <div class="consent-actions">
        <button type="button" class="consent-button" data-consent="denied">Ablehnen</button>
        <button type="button" class="consent-button consent-accept" data-consent="granted">Statistik erlauben</button>
      </div>`;
    banner.addEventListener("click", (event) => {
      const button = event.target.closest("[data-consent]");
      if (button) saveConsent(button.dataset.consent);
    });
    document.body.appendChild(banner);
    banner.querySelector('[data-consent="denied"]')?.focus();
  }

  const consent = readConsent();
  if (consent === "granted") loadAnalytics();
  if (consent !== "granted" && consent !== "denied") showBanner();
  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-consent-settings]")) return;
    event.preventDefault();
    showBanner();
  });
})();
