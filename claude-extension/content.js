// Runs in ISOLATED world — relays postMessage from injected.js to background.
(function () {
  'use strict';

  const apiData = {};

  // Receive intercepted fetch responses from injected.js (MAIN world)
  window.addEventListener('message', e => {
    if (e.source === window && e.data?.__claudeWidget) {
      apiData[e.data.url] = e.data.data;
      console.log('[claude-widget] captured:', e.data.url);
    }
  });

  // DOM parser — matches the actual claude.ai/settings/usage layout
  function parseDOM() {
    const text = document.body?.innerText || '';
    const out  = {};

    // 5-hour rolling window %  e.g. "5-hour rolling window ... 43%"
    // Also handles old "Current session" label as fallback
    const fiveHrPct = text.match(/5.hour[\s\S]{0,150}?(\d+)%/i)
                   || text.match(/Current session[\s\S]{0,80}?(\d+)%/i);
    if (fiveHrPct) out['5-hr Used'] = fiveHrPct[1] + '%';

    // 5-hour reset — capture full text e.g. "Resets in 2 hr 46 min"
    const fiveHrReset = text.match(/([Rr]esets?\s+in\s+[\d]+\s*hr[^\n]*)/i);
    if (fiveHrReset) out['5-hr Resets'] = fiveHrReset[1].trim();

    // Weekly usage %  e.g. "weekly ... 67%"
    const weeklyPct = text.match(/week(?:ly)?[\s\S]{0,150}?(\d+)%/i);
    if (weeklyPct) out['Weekly Used'] = weeklyPct[1] + '%';

    // Weekly reset — capture full text e.g. "Resets Mon 10:00 PM"
    const weeklyReset = text.match(/([Rr]esets?\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+[\d:]+\s*[AP]M)/i);
    if (weeklyReset) out['Weekly Resets'] = weeklyReset[1].trim();

    // Plan (added Max for Claude Max plan)
    const plan = text.match(/\b(Pro|Max|Free|Team|Enterprise)\b/i);
    if (plan) out['Plan'] = plan[1];

    return out;
  }

  // Wait for React + XHR to finish, then send data
  setTimeout(() => {
    if (!location.href.includes('/settings/usage')) return;

    chrome.runtime.sendMessage({
      type: 'CLAUDE_USAGE',
      data: { api: apiData, dom: parseDOM() }
    });
  }, 4000);
})();
