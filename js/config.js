(function () {
  const storedBase = window.localStorage.getItem("smart_campus_api_base");
  const runtimeOrigin =
    window.location && /^https?:/i.test(window.location.origin)
      ? window.location.origin
      : "http://127.0.0.1:8000";

  const baseOrigin = (storedBase || runtimeOrigin).replace(/\/+$/, "");
  window.SMART_CAMPUS_API = `${baseOrigin}/api`;
})();
