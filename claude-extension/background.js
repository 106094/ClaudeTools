const USAGE_URL  = 'https://claude.ai/settings/usage';
const WIDGET_URL = 'http://localhost:7899/usage';
const ALARM_NAME = 'claudeUsageFetch';

let pendingTabId = null;

// ── Setup ──────────────────────────────────────────────────────────────────
chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create(ALARM_NAME, { periodInMinutes: 5 });
  openUsageTab();
});

chrome.runtime.onStartup.addListener(() => {
  openUsageTab();
});

chrome.alarms.onAlarm.addListener(alarm => {
  if (alarm.name === ALARM_NAME) openUsageTab();
});

// ── Open usage page silently ───────────────────────────────────────────────
async function openUsageTab() {
  try {
    // Reuse existing tab if already open
    const [existing] = await chrome.tabs.query({ url: USAGE_URL + '*' });
    if (existing) {
      pendingTabId = existing.id;
      await chrome.tabs.reload(existing.id);
    } else {
      const tab = await chrome.tabs.create({ url: USAGE_URL, active: false });
      pendingTabId = tab.id;
    }
  } catch (e) {
    console.error('[claude-widget] openUsageTab:', e);
  }
}

// ── Receive data from content script ──────────────────────────────────────
chrome.runtime.onMessage.addListener((msg, sender) => {
  if (msg.type !== 'CLAUDE_USAGE') return;

  const tabId = sender.tab?.id;

  // Close the background tab (only if user isn't actively viewing it)
  if (tabId && tabId === pendingTabId) {
    chrome.tabs.get(tabId, tab => {
      if (chrome.runtime.lastError) return;
      if (!tab.active) {
        setTimeout(() => chrome.tabs.remove(tabId), 500);
      }
    });
  }

  // Cache in storage (widget can poll this too)
  const entry = { ...msg.data, updatedAt: new Date().toISOString() };
  chrome.storage.local.set({ lastUsage: entry });

  // POST to widget
  fetch(WIDGET_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry)
  }).catch(() => {
    // Widget not running — data is still cached in storage
  });
});
