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

    // Current session % used  e.g. "43% used"
    const sessionPct = text.match(/Current session[\s\S]{0,80}?(\d+)%\s*used/i);
    if (sessionPct) out['Session Used'] = sessionPct[1] + '%';

    // Session reset  e.g. "Resets in 2 hr 46 min"
    const sessionReset = text.match(/Resets in ([\d]+ hr[\s\d\w]*)/i);
    if (sessionReset) out['Session Resets'] = 'in ' + sessionReset[1].trim();

    // Weekly all-models % used (second "% used" occurrence)
    const allPcts = [...text.matchAll(/(\d+)%\s*used/gi)];
    if (allPcts.length >= 2) out['Weekly Used'] = allPcts[1][1] + '%';
    else if (allPcts.length === 1) out['Weekly Used'] = allPcts[0][1] + '%';

    // Weekly reset day  e.g. "Resets Tue 10:00 AM"
    const weeklyReset = text.match(/Resets\s+(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+([\d:]+\s*[AP]M)/i);
    if (weeklyReset) out['Weekly Resets'] = weeklyReset[1] + ' ' + weeklyReset[2];

    // Plan
    const plan = text.match(/\b(Pro|Free|Team|Enterprise)\b/i);
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
