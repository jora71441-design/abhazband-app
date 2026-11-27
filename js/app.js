function _activateTabByKey(tabKey) {
  const rawTab = (tabKey || '').toLowerCase().trim();
  if (!rawTab || rawTab === 'overview') return false;

  const candidateMap = {
    rides: ['rides', 'rides-tab', 'calendar', 'calendar-tab'],
    calendar: ['calendar', 'calendar-tab', 'rides', 'rides-tab'],
    camps: ['camps', 'camps-tab'],
    'my-camp': ['my-camp', 'my-camp-tab', 'mycamp', 'mycamp-tab'],
    shop: ['shop', 'shop-tab', 'velouyut', 'velouyut-tab'],
    features: ['tools-tab', 'tools', 'features', 'features-tab', 'fitchi', 'fitchi-tab']
  };

  const candidates = candidateMap[rawTab] || [rawTab, `${rawTab}-tab`];
  let targetId = null;

  for (const id of candidates) {
    if (document.getElementById(id)) {
      targetId = id;
      break;
    }
  }

  const navItems = Array.from(document.querySelectorAll('.tab-item'));
  let matchedNav = navItems.find((el) => {
    const handler = el.getAttribute('onclick') || '';
    return candidates.some((id) => handler.includes(`'${id}'`) || handler.includes(`"${id}"`));
  });

  if (!matchedNav && (rawTab === 'rides' || rawTab === 'calendar')) {
    matchedNav = navItems.find((el) => /календар|заезд/i.test(el.textContent || ''));
  } else if (!matchedNav && rawTab === 'camps') {
    matchedNav = navItems.find((el) => /^[\s⛺🏕]*кэмп/i.test((el.textContent || '').trim()));
  } else if (!matchedNav && rawTab === 'my-camp') {
    matchedNav = navItems.find((el) => /мой\s*кэмп/i.test(el.textContent || ''));
  } else if (!matchedNav && rawTab === 'shop') {
    matchedNav = navItems.find((el) => /магазин|велоуют/i.test(el.textContent || ''));
  } else if (!matchedNav && rawTab === 'features') {
    matchedNav = navItems.find((el) => /фитч|фич|полезн/i.test(el.textContent || ''));
  }

  if (!targetId && matchedNav) {
    const handler = matchedNav.getAttribute('onclick') || '';
    const m = handler.match(/switchTab\(\s*['"]([^'"]+)['"]/);
    if (m && m[1]) targetId = m[1];
  }

  if (!targetId) return false;

  if (typeof switchTab === 'function') {
    switchTab(targetId, matchedNav || null);
    return true;
  }
  return false;
}

function openInitialTabFromUrl() {
  try {
    const params = new URLSearchParams(window.location.search);
    const rawParam = (
      params.get('startapp') ||
      params.get('tab') ||
      window.Telegram?.WebApp?.initDataUnsafe?.start_param ||
      ''
    ).trim();

    if (!rawParam || rawParam.toLowerCase() === 'overview') return;

    // 1. Прямое открытие карточки заезда: startapp=ride_<ride_id>
    if (rawParam.startsWith('ride_')) {
      const rideId = decodeURIComponent(rawParam.slice(5)).trim();
      _activateTabByKey('calendar');
      if (typeof rides !== 'undefined' && Array.isArray(rides)) {
        const foundRide = rides.find((r) => r.id === rideId);
        if (foundRide && foundRide.dates && foundRide.dates[0]) {
          const [yStr, mStr] = foundRide.dates[0].split('-');
          const yNum = parseInt(yStr, 10);
          const mNum = parseInt(mStr, 10) - 1;
          if (!Number.isNaN(yNum) && !Number.isNaN(mNum)) {
            calendarCurrentYear = yNum;
            calendarCurrentMonth = mNum;
            if (typeof renderRides === 'function') renderRides();
          }
        }
      }
      if (typeof openRideModal === 'function') {
        setTimeout(() => openRideModal(rideId), 80);
      }
      return;
    }

    // 2. Прямое открытие карточки кэмпа: startapp=camp_<camp_id>
    if (rawParam.startsWith('camp_')) {
      const campId = decodeURIComponent(rawParam.slice(5)).trim();
      _activateTabByKey('camps');
      if (typeof openCampModal === 'function') {
        setTimeout(() => openCampModal(campId), 80);
      }
      return;
    }

    // 3. Обычное открытие вкладки (?tab=calendar / camps / my-camp / features / shop)
    _activateTabByKey(rawParam);
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
