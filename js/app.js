function openInitialTabFromUrl() {
  try {
    const params = new URLSearchParams(window.location.search);
    const rawTab = (
      params.get('tab') ||
      window.Telegram?.WebApp?.initDataUnsafe?.start_param ||
      ''
    ).toLowerCase().trim();

    if (!rawTab || rawTab === 'overview') return;

    const candidateMap = {
      rides: ['rides', 'rides-tab', 'calendar', 'calendar-tab'],
      calendar: ['calendar', 'calendar-tab', 'rides', 'rides-tab'],
      camps: ['camps', 'camps-tab']
    };

    const candidates = candidateMap[rawTab] || [rawTab, `${rawTab}-tab`];
    let targetId = null;

    for (const id of candidates) {
      if (document.getElementById(id)) {
        targetId = id;
        break;
      }
    }

    if (!targetId) return;

    const navItems = Array.from(document.querySelectorAll('.tab-item'));
    let matchedNav = navItems.find((el) => {
      const handler = el.getAttribute('onclick') || '';
      return candidates.some((id) => handler.includes(`'${id}'`) || handler.includes(`"${id}"`));
    });

    if (!matchedNav && (rawTab === 'rides' || rawTab === 'calendar')) {
      matchedNav = navItems.find((el) => /календар|заезд/i.test(el.textContent || ''));
    } else if (!matchedNav && rawTab === 'camps') {
      matchedNav = navItems.find((el) => /кэмп/i.test(el.textContent || ''));
    }

    if (typeof switchTab === 'function') {
      switchTab(targetId, matchedNav || null);
    }
  } catch (e) {
    console.error('openInitialTabFromUrl:', e);
  }
}

function initApp() {
  try { renderCamps(); } catch (e) { console.error('camps:', e); }
  try { renderRides(); } catch (e) { console.error('rides:', e); }
  try { renderMedia(); } catch (e) { console.error('media:', e); }
  try { calcPressure(); } catch (e) { console.error('pressure:', e); }
  try { initSubscriptionToggle(); } catch (e) { console.error('sub:', e); }
  try { checkAdmin(); } catch (e) { console.error('admin:', e); }
  try { renderVelouyutUI(); } catch (e) { console.error('velouyut:', e); }
  try { checkCampAccessOnLoad(); } catch (e) { console.error('campAccess:', e); }
  openInitialTabFromUrl();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
