// Runs in the page's MAIN world — can intercept fetch directly.
// Communicates back to content.js (ISOLATED world) via window.postMessage.
(function () {
  const _fetch = window.fetch;
  const seen   = new Set();
  const kw     = ['usage','billing','plan','limit','quota',
                  'subscription','entitlement','rate','account'];

  window.fetch = async function (...args) {
    const res = await _fetch.apply(this, args);
    const url = (typeof args[0] === 'string' ? args[0] : args[0]?.url) || '';

    if (kw.some(k => url.includes(k)) && !seen.has(url)) {
      seen.add(url);
      res.clone().json().then(data => {
        window.postMessage({ __claudeWidget: true, url, data }, '*');
      }).catch(() => {});
    }
    return res;
  };
})();
