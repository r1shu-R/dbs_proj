(function () {
  const storedBase = window.localStorage.getItem("smart_campus_api_base");
  const runtimeOrigin =
    window.location && /^https?:/i.test(window.location.origin)
      ? window.location.origin
      : "http://127.0.0.1:8000";

  const isHostedRuntime = /^https:\/\//i.test(runtimeOrigin);
  const isLocalStoredBase =
    !!storedBase && /localhost|127\.0\.0\.1/i.test(storedBase);

  if (isHostedRuntime && isLocalStoredBase) {
    window.localStorage.removeItem("smart_campus_api_base");
  }

  const baseOrigin = (
    isHostedRuntime && isLocalStoredBase ? runtimeOrigin : (storedBase || runtimeOrigin)
  ).replace(/\/+$/, "");
  window.SMART_CAMPUS_API = `${baseOrigin}/api`;
})();
