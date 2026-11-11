// ==================== РЕНДЕР КЭМПОВ ====================
function renderCamps() {
  const container = document.getElementById('camps-list');
  if (!container) return;
  container.innerHTML = camps.map(camp => `
    <div class="card" id="${camp.id}">
      <img src="${camp.image}" alt="${camp.title}">
      <div class="card-body">
        <span class="badge">${camp.dates}</span>
        <h3 class="card-title">${camp.title}</h3>
        <div class="meta-line">📍 ${camp.location}</div>
        ${camp.specs ? `<div class="meta-line">🚴 ${camp.specs}</div>` : ''}
        <div class="meta-line" style="color:#4cd964; font-weight:bold; margin-top:6px;">💰 ${camp.price}</div>
        <p style="font-size:13px; color:var(--hint-color); margin: 8px 0;">${camp.description}</p>
        <a href="${camp.link}" class="btn" target="_blank">Подробнее и запись</a>
      </div>
    </div>
  `).join('');
}

// ==================== ИНТЕРАКТИВНЫЙ КАЛЕНДАРЬ ЗАЕЗДОВ ====================
const CALENDAR_MONTH_NAMES = [
  "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
];

function renderRides() {
  const container = document.getElementById('rides-list');
  if (!container) return;

  const year = calendarCurrentYear;
  const month = calendarCurrentMonth;

  // Расчет дней в месяце и первого дня недели (Пн = 0, Вс = 6)
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayWeekIndex = (new Date(year, month, 1).getDay() + 6) % 7;

  let daysHtml = '';

  // Пустые ячейки до 1-го числа
  for (let i = 0; i < firstDayWeekIndex; i++) {
    daysHtml += `<div class="calendar-day-cell empty"></div>`;
  }

  // Генерация ячеек дней
  for (let day = 1; day <= daysInMonth; day++) {
    const monthStr = String(month + 1).padStart(2, '0');
    const dayStr = String(day).padStart(2, '0');
    const dateKey = `${year}-${monthStr}-${dayStr}`;

    const ride = rides.find(r => r.dates && r.dates.includes(dateKey));

    if (ride) {
      const eventClass = ride.type === 'weekend' ? 'event-weekend' : 'event-social';
      daysHtml += `
        <div class="calendar-day-cell ${eventClass}" onclick="openRideModal('${ride.id}')">
          <span>${day}</span>
          <div class="calendar-day-dot"></div>
        </div>
      `;
    } else {
      daysHtml += `
        <div class="calendar-day-cell">
          <span>${day}</span>
        </div>
      `;
    }
  }

  container.innerHTML = `
    <!-- Инфо-плашка параметров -->
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 12px; padding: 10px 12px; margin-bottom: 14px; display: flex; justify-content: space-around; text-align: center; font-size: 11px; color: #94a3b8; font-weight: 600;">
      <div>⚡ Темп: <span style="color:#fff;">27–30 км/ч</span></div>
      <div>🚗 <span style="color:#fff;">Техничка & багаж</span></div>
      <div>☕ <span style="color:#fff;">Кофе & фотосет</span></div>
    </div>

    <!-- Основной блок календаря -->
    <div class="calendar-card">
      <div class="calendar-nav-header">
        <button class="calendar-nav-btn" onclick="changeCalendarMonth(-1)">‹</button>
        <div class="calendar-month-title">${CALENDAR_MONTH_NAMES[month].toUpperCase()} ${year}</div>
        <button class="calendar-nav-btn" onclick="changeCalendarMonth(1)">›</button>
      </div>

      <!-- Дни недели -->
      <div class="calendar-weekdays-grid">
        <div class="calendar-weekday-item">ПН</div>
        <div class="calendar-weekday-item">ВТ</div>
        <div class="calendar-weekday-item">СР</div>
        <div class="calendar-weekday-item">ЧТ</div>
        <div class="calendar-weekday-item">ПТ</div>
        <div class="calendar-weekday-item" style="color: #38bdf8;">СБ</div>
        <div class="calendar-weekday-item" style="color: #ef4444;">ВС</div>
      </div>

      <!-- Сетка чисел -->
      <div class="calendar-days-grid">
        ${daysHtml}
      </div>

      <!-- Легенда -->
      <div class="calendar-legend-box">
        <div class="legend-item">
          <span class="legend-color-dot" style="background: #ef4444; box-shadow: 0 0 6px rgba(239, 68, 68, 0.8);"></span>
          <span>Weekend Camp (2 дня)</span>
        </div>
        <div class="legend-item">
          <span class="legend-color-dot" style="background: #10b981; box-shadow: 0 0 6px rgba(16, 185, 129, 0.8);"></span>
          <span>Social Ride (1 день)</span>
        </div>
      </div>
    </div>

    <!-- Карточка Band Pass для Сочи и Адлера -->
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 14px; padding: 14px; margin-top: 14px; display: flex; justify-content: space-between; align-items: center; gap: 10px;">
      <div>
        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 3px;">
          <span style="font-size: 14px;">🎟️</span>
          <strong style="font-size: 12px; color: #fff; text-transform: uppercase; letter-spacing: 0.5px;">BAND PASS ДЛЯ СОЧИ И АДЛЕРА</strong>
        </div>
        <div style="font-size: 11px; color: #94a3b8; line-height: 1.3;">
          Абонементы на 2 Social Rides или 2 Weekends • 1 перенос при непогоде
        </div>
      </div>
      <a href="https://t.me/Piti4?text=${encodeURIComponent('Привет! Расскажи подробнее про условия и абонемент BAND PASS для Сочи/Адлера')}" target="_blank" class="btn" style="width: auto; padding: 8px 12px; font-size: 11px; font-weight: bold; white-space: nowrap; flex-shrink: 0; background: #ef4444; color: #fff; text-decoration: none;">
        Связь: @Piti4
      </a>
    </div>

    <!-- Контейнер всплывающего окна (Bottom Sheet) -->
    <div id="ride-sheet-overlay" class="bottom-sheet-overlay" onclick="closeRideModal(event)">
      <div class="bottom-sheet-modal" id="ride-sheet-modal" onclick="event.stopPropagation()"></div>
    </div>
  `;
}

// Переключение месяца календаря
function changeCalendarMonth(delta) {
  calendarCurrentMonth += delta;
  if (calendarCurrentMonth < 0) {
    calendarCurrentMonth = 11;
    calendarCurrentYear--;
  } else if (calendarCurrentMonth > 11) {
    calendarCurrentMonth = 0;
    calendarCurrentYear++;
  }
  if (window.Telegram?.WebApp?.HapticFeedback) {
    window.Telegram.WebApp.HapticFeedback.selectionChanged();
  }
  renderRides();
}

// Открытие всплывающего окна с условиями заезда
function openRideModal(rideId) {
  const ride = rides.find(r => r.id === rideId);
  if (!ride) return;

  const modal = document.getElementById('ride-sheet-modal');
  const overlay = document.getElementById('ride-sheet-overlay');
  if (!modal || !overlay) return;

  if (window.Telegram?.WebApp?.HapticFeedback) {
    window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
  }

  modal.innerHTML = `
    <div class="bottom-sheet-handle"></div>
    
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
      <span class="sheet-badge" style="background: ${ride.badgeColor}22; color: ${ride.badgeColor}; border: 1px solid ${ride.badgeColor};">
        ${ride.typeLabel} • ${ride.durationLabel}
      </span>
      <span style="font-size: 11px; color: #94a3b8; font-weight: bold;">📅 ${ride.dateDisplay}</span>
    </div>

    <h3 class="sheet-title">${ride.title}</h3>
    <div class="sheet-subtitle">${ride.subtitle}</div>

    <!-- Метрики заезда -->
    <div class="sheet-metrics-grid">
      <div class="sheet-metric-box">
        <span class="sheet-metric-label">🛣️ Дистанция</span>
        <span class="sheet-metric-val">${ride.stats.distance}</span>
      </div>
      <div class="sheet-metric-box">
        <span class="sheet-metric-label">⛰️ Набор высоты</span>
        <span class="sheet-metric-val">${ride.stats.elevation}</span>
      </div>
      <div class="sheet-metric-box">
        <span class="sheet-metric-label">⚡ Темп пачки</span>
        <span class="sheet-metric-val">${ride.stats.pace}</span>
      </div>
      <div class="sheet-metric-box">
        <span class="sheet-metric-label">🛤️ Покрытие</span>
        <span class="sheet-metric-val">${ride.stats.surface}</span>
      </div>
    </div>

    <!-- Тайминг дня и логистика -->
    <div class="sheet-section-title">⏰ Логистика и тайминг</div>
    <div style="margin-bottom: 14px;">
      ${ride.timing.map(item => `
        <div class="sheet-timing-item">
          <span class="sheet-time-tag">${item.time}</span>
          <span class="sheet-timing-desc">${item.text}</span>
        </div>
      `).join('')}
    </div>

    <!-- Что входит в слот -->
    <div class="sheet-section-title">🎒 Включено в слот</div>
    <div style="margin-bottom: 18px;">
      ${ride.included.map(inc => `
        <div class="sheet-included-item">
          <span class="sheet-included-icon">✓</span>
          <span>${inc}</span>
        </div>
      `).join('')}
    </div>

    <!-- Кнопки действий -->
    <div style="display: flex; gap: 8px;">
      <a href="https://t.me/Piti4?text=${encodeURIComponent('Привет! Хочу забронировать участие в заезде: ' + ride.title + ' (' + ride.dateDisplay + ')')}" 
         target="_blank" 
         class="btn" 
         style="flex: 2; padding: 12px 0; font-size: 13px; text-align: center; text-decoration: none;">
        🚴 Забронировать участие
      </a>
      <button onclick="shareRide('${ride.title.replace(/'/g, "\\'")}', '${ride.dateDisplay.replace(/'/g, "\\'")}')" 
              class="btn btn-secondary" 
              style="flex: 1; padding: 12px 0; font-size: 13px; display: flex; align-items: center; justify-content: center; gap: 4px;">
        <span>🔗</span> Поделиться
      </button>
    </div>
  `;

  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

// Закрытие окна по клику на фон
function closeRideModal(event) {
  if (event && event.target && event.target.closest('#ride-sheet-modal')) {
    return;
  }
  const overlay = document.getElementById('ride-sheet-overlay');
  if (overlay) {
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// ==================== РЕНДЕР МЕДИА КАНАЛОВ ====================
function renderMedia() {
  const container = document.getElementById('media-list');
  if (!container) return;
  container.innerHTML = mediaChannels.map(item => `
    <div class="card" style="margin-bottom: 14px;">
      <img src="${item.image}" alt="${item.name}">
      <div class="card-body">
        <span class="badge" style="background: #38bdf8; color: #0f172a;">${item.tag}</span>
        <h3 class="card-title">${item.name}</h3>
        <p style="font-size: 13px; color: var(--hint-color); margin: 0 0 12px 0;">${item.desc}</p>
        <a href="${item.link}" target="_blank" class="btn">За красотой 🚀</a>
      </div>
    </div>
  `).join('');
}

// ==================== РЕНДЕР КАТАЛОГА ВЕЛОУЮТ ====================
function renderVelouyutUI() {
  const container = document.getElementById('velouyut-products-list');
  if (!container) return;

  container.innerHTML = VELOUYUT_PRODUCTS_DATA.map(item => `
    <div class="card" style="margin-bottom: 14px; background: #1e293b; padding: 12px; border-radius: 12px; border: 1px solid #334155; overflow: hidden;">
      ${item.image ? `
        <img src="${item.image}" alt="${item.title}" style="width: 100%; height: 230px; object-fit: contain; border-radius: 8px; margin-bottom: 10px; background: #0f172a;" onerror="this.style.display='none'">
      ` : ''}

      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
        <span class="badge" style="background: #10b981; color: #fff; font-size: 10px;">ВЕЛОУЮТ</span>
        <span style="font-size: 11px; color: #94a3b8;">🎨 ${item.colors}</span>
      </div>

      <h4 style="margin: 4px 0 8px 0; color: #fff; font-size: 15px;">${item.title}</h4>

      <div style="display: flex; align-items: center; margin-bottom: 12px;">
        <span style="font-size: 16px; font-weight: bold; color: #38bdf8;">${item.price.toLocaleString()} ₽</span>
      </div>

      <div style="display: flex; gap: 8px;">
        <a href="https://t.me/Piti4?text=${encodeURIComponent('Привет! Хочу заказать из раздела Велоуют: ' + item.title)}" target="_blank" class="btn" style="flex: 2; padding: 9px 0; font-size: 13px; text-align: center;">Заказать 💬</a>
        <button onclick="shareProduct('${item.title.replace(/'/g, "\\'")}', ${item.price})" class="btn" style="flex: 1; padding: 9px 0; font-size: 13px; background: #334155; color: #38bdf8; border: 1px solid #475569; display: flex; align-items: center; justify-content: center; gap: 4px;">
          <span>🔗</span> Поделиться
        </button>
      </div>
    </div>
  `).join('');
}

// ==================== ЛОГИКА КАБИНЕТА «МОЙ КЭМП» ====================
function checkCampAccessOnLoad() {
  try {
    const savedPin = localStorage.getItem('abhaz_camp_pin');
    if (savedPin === CAMP_SECRET_PIN) {
      showUnlockedCamp();
    }
  } catch(e) {
    console.error('Ошибка проверки PIN:', e);
  }
}

function unlockCamp() {
  const pinInput = document.getElementById('camp-pin-input');
  const errorMsg = document.getElementById('pin-error-msg');
  if (!pinInput) return;

  const val = pinInput.value.trim().toUpperCase();

  if (val === CAMP_SECRET_PIN) {
    localStorage.setItem('abhaz_camp_pin', CAMP_SECRET_PIN);
    if (errorMsg) errorMsg.style.display = 'none';
    showUnlockedCamp();
  } else {
    if (errorMsg) errorMsg.style.display = 'block';
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.notificationOccurred('error');
    }
  }
}

function showUnlockedCamp() {
  const lockCard = document.getElementById('my-camp-locked');
  const unlockedDash = document.getElementById('my-camp-unlocked');

  if (lockCard) lockCard.style.display = 'none';
  if (unlockedDash) unlockedDash.style.display = 'block';

  renderTracksList();
  renderChecklistUI();
  renderMemoUI();
}

function updateCampOption(key, val) {
  campState[key] = val;
  if (window.Telegram?.WebApp?.HapticFeedback) {
    window.Telegram.WebApp.HapticFeedback.selectionChanged();
  }
  renderTracksList();
}

function renderTracksList() {
  const container = document.getElementById('gpx-tracks-list');
  if (!container) return;

  let html = `
    <div style="background: #0f172a; padding: 12px; border-radius: 12px; margin-bottom: 16px; border: 1px solid #334155;">
      <div style="font-size: 11px; color: #94a3b8; font-weight: bold; margin-bottom: 8px; text-transform: uppercase;">⚙️ Настройка маршрутной программы</div>
      
      <div style="margin-bottom: 10px;">
        <span style="font-size: 12px; color: #cbd5e1; display: block; margin-bottom: 4px;">🛋️ День отдыха (восстановление):</span>
        <div style="display: flex; gap: 6px;">
          <button onclick="updateCampOption('restDay', 10)" class="sub-tab-btn ${campState.restDay === 10 ? 'active' : ''}" style="flex:1; padding:6px;">10 Октября</button>
          <button onclick="updateCampOption('restDay', 12)" class="sub-tab-btn ${campState.restDay === 12 ? 'active' : ''}" style="flex:1; padding:6px;">12 Октября</button>
        </div>
      </div>

      <div>
        <span style="font-size: 12px; color: #cbd5e1; display: block; margin-bottom: 4px;">🔀 Ветка 13–14 октября:</span>
        <div style="display: flex; gap: 6px;">
          <button onclick="updateCampOption('branch', 'gal')" class="sub-tab-btn ${campState.branch === 'gal' ? 'active' : ''}" style="flex:1; padding:6px;">📍 Ветка Гал (ИнгурГЭС)</button>
          <button onclick="updateCampOption('branch', 'tkuarchal')" class="sub-tab-btn ${campState.branch === 'tkuarchal' ? 'active' : ''}" style="flex:1; padding:6px;">🏔️ Ветка Ткуарчал</button>
        </div>
      </div>
    </div>
  `;

  const schedule = [
    {
      day: "4-5 ОКТЯБРЯ",
      title: "📆 Дни приезда & Сборка велосипедов",
      type: "Оргдень",
      desc: "Встреча участников, совместная сборка байков.<br>🕕 <b>20:00</b> — Вечерний ужин команды.",
      stats: "📍 База AbhazBand",
      km: 0, gain: 0
    },
    {
      day: "6 ОКТЯБРЯ",
      title: "Пицундский маршрут",
      type: "Шоссе & Гравел",
      desc: "Разминочная вкатка. Наслаждение красотами Пицунды, проезд через Реликтовый лес, Золотой берег, небольшие наборы.<br>🕕 11:00 Выезд | 13:00 Кофе в «Амшын» | 16:00 Финиш",
      stats: "🛣️ 70 км &nbsp;|&nbsp; ⛰️ +600 м &nbsp;|&nbsp; Асфальт 100%",
      km: 70, gain: 600,
      links: [
        { label: "🗺️ Шоссе Komoot", url: "https://www.komoot.com/tour/1321206568?ref=aso&share_token=aWG49MO64K7t5GSiGNmAO1VJh65xzwAj6ZUwJvUiWkaopf7otl&t_s=referral&t_cid=route_share" },
        { label: "🗺️ Гравел Komoot", url: "https://www.komoot.com/tour/2920620509?ref=aso&share_token=aTotm7kS6lV8x1pozOTdf6P2gedqgBybX6Gpf6NE1f5rRHTT59&t_s=referral&t_cid=route_share" }
      ]
    },
    {
      day: "7 ОКТЯБРЯ",
      title: "Дорога на Лыхны / Мюссеру (Дополненный)",
      type: "Шоссе & Гравел",
      desc: "Один из любимейших маршрутов в новом исполнении. Дороги с околонулевым трафиком и отличные виды!<br>🕕 10:30 Выезд | 15:00 Обед | 18:00 Финиш",
      stats: "🛣️ 105 км &nbsp;|&nbsp; ⛰️ +1300 м &nbsp;|&nbsp; Асфальт 85%, Грунты 15%",
      km: 105, gain: 1300,
      links: [
        { label: "🗺️ Шоссе Komoot", url: "https://www.komoot.com/tour/3229725192?ref=aso&share_token=a5dp3vGaOcX5tgL0cilnYV8zEH57L34BeFNf0MOvoFGjqvRzzX&t_s=referral&t_cid=route_share" },
        { label: "🗺️ Гравел Komoot", url: "https://www.komoot.com/tour/2666494537?ref=aso&share_token=aVXqttvbkrJIxZkkeeT73LtG1Ly4BilW0gCo6c0BxgokxrRnlT&t_s=referral&t_cid=route_share" }
      ]
    },
    {
      day: "8 ОКТЯБРЯ",
      title: "Ознакомительная по Гагре",
      type: "Шоссе & Гравел",
      desc: "День восстановления. Достопримечательности Гагр, посещение дачи Сталина и знаковых мест.<br>🕕 11:00 Выезд на маршрут.",
      stats: "🛣️ 83 км &nbsp;|&nbsp; ⛰️ +970 м &nbsp;|&nbsp; Асфальт 100%",
      km: 83, gain: 970,
      links: [
        { label: "🗺️ Маршрут Komoot", url: "https://www.komoot.com/tour/2163197173?ref=aso&share_token=a9qpVaqv8hgLSIz40ny0xV3tBKUTth6E8C6uCFmqwhciQBOTAE&t_s=referral&t_cid=route_share" }
      ]
    },
    {
      day: "9 ОКТЯБРЯ",
      title: "Рицинский заповедник",
      type: "Шоссе",
      desc: "Один из самых красивых маршрутов в мире. Пролегает через ущелье с множеством запоминающихся видов.<br>🕕 10:30 Выезд | 15:30 Обед в балагане | 18:00 Финиш",
      stats: "🛣️ 105 км &nbsp;|&nbsp; ⛰️ +1 370 м &nbsp;|&nbsp; Асфальт 100%",
      km: 105, gain: 1370,
      links: [
        { label: "🗺️ Шоссе Komoot", url: "https://www.komoot.com/tour/2163164931?ref=aso&share_token=am16MyeqIuonAwi1Zh2WT8TyeaoCEqAbKODb5gr9ftyqcG1M5u&t_s=referral&t_cid=route_share" }
      ]
    }
  ];

  const is90 = campState.distSukhum === 90;
  const sukhumRouteObj = {
    title: "Окрестности Сухума и Новый Афон",
    type: "Шоссе & Гравел",
    desc: `Маршрут по окрестностям Сухума. Заезд в Черниговку, Беслетку, Каманы.<br>
      <div style="margin-top:6px;">
        Выбор дистанции: 
        <button onclick="updateCampOption('distSukhum', 65)" style="padding:2px 8px; font-size:10px; border-radius:4px; border:none; background:${!is90 ? '#38bdf8' : '#334155'}; color:${!is90 ? '#0f172a' : '#fff'}; font-weight:bold;">65 км</button>
        <button onclick="updateCampOption('distSukhum', 90)" style="padding:2px 8px; font-size:10px; border-radius:4px; border:none; background:${is90 ? '#38bdf8' : '#334155'}; color:${is90 ? '#0f172a' : '#fff'}; font-weight:bold;">90 км</button>
      </div><br>
      🕕 11:00 Выезд | 15:00 Обед | 17:00 Финиш`,
    stats: is90 ? "🛣️ 90 км &nbsp;|&nbsp; ⛰️ +1 200 м &nbsp;|&nbsp; Асфальт 98%" : "🛣️ 65 км &nbsp;|&nbsp; ⛰️ +800 м &nbsp;|&nbsp; Асфальт 98%",
    km: is90 ? 90 : 65,
    gain: is90 ? 1200 : 800,
    links: [
      { label: "🗺️ Komoot 65 км", url: "https://www.komoot.com/tour/2745236293?ref=aso&share_token=afaOF3FwMBq5f4KjNbFpc6OWZQJLjYFaodzeEWwiL0C2lkq22u&t_s=referral&t_cid=route_share" },
      { label: "🗺️ Komoot 90 км", url: "https://www.komoot.com/tour/2941874319?ref=aso&share_token=aTE6ufoRqr9OFvK6bygBTQ7L9d7nUbbagDJCWNmYU76CXqBYUA&t_s=referral&t_cid=route_share" }
    ]
  };

  const transitRouteObj = {
    title: "Транзит: Дорога на Сухум",
    type: "Шоссе / Переезд",
    desc: "День переезда на восточную базу в Сухум. Заезд в Ачандару, Новый Афон и Нижне-Эшерскую дорогу.<br>🕕 09:00 Выезд | 14:00 Обед | 18:00 Финиш",
    stats: "🛣️ 112 км &nbsp;|&nbsp; ⛰️ +1 400 м &nbsp;|&nbsp; Асфальт 80%",
    km: 112, gain: 1400,
    links: [{ label: "🗺️ Маршрут Komoot", url: "https://www.komoot.com" }]
  };

  const restDayObj = {
    title: "🛋️ Выходной & Восстановление",
    type: "Rest Day",
    desc: "День отдыха. Посещение термальных источников / бани, самостоятельное планирование, прогулки и хайкинг.",
    stats: "♨️ Режим восстановления",
    km: 0, gain: 0
  };

  if (campState.restDay === 10) {
    schedule.push({ day: "10 ОКТЯБРЯ", ...restDayObj });
    schedule.push({ day: "11 ОКТЯБРЯ", ...transitRouteObj });
    schedule.push({ day: "12 ОКТЯБРЯ", ...sukhumRouteObj });
  } else {
    schedule.push({ day: "10 ОКТЯБРЯ", ...transitRouteObj });
    schedule.push({ day: "11 ОКТЯБРЯ", ...sukhumRouteObj });
    schedule.push({ day: "12 ОКТЯБРЯ", ...restDayObj });
  }

  if (campState.branch === 'gal') {
    schedule.push({
      day: "13 ОКТЯБРЯ • ВЕТКА ГАЛ",
      title: "Дорога на Гал",
      type: "Шоссе",
      desc: "Посещение и ночёвка в самом удалённом городе Абхазии — г. Гал.<br>🕕 11:00 Выезд | 15:00 Обед в Гал | 17:00 Финиш",
      stats: "🛣 85 км &nbsp;|&nbsp; ⛰️ +320 м &nbsp;|&nbsp; Асфальт 100%",
      km: 85, gain: 320,
      links: [{ label: "🗺️ Маршрут Komoot", url: "https://www.komoot.com/tour/2188906729?ref=aso&share_token=axKRfsfjKifyn6Q5M3Q6G83ptb0Fdga1qggsvNoXKpsaVxPQjC&t_s=referral&t_cid=route_share" }]
    });
    schedule.push({
      day: "14 ОКТЯБРЯ • ВЕТКА ГАЛ",
      title: "Дорога к ИнгурГЭС & Граница",
      type: "Шоссе",
      desc: "Поездка на гидроэлектростанцию ИнгурГЭС и к границе. Возвращение на базу в Сухум.<br>🕕 09:00 Выезд | 15:00 Обед в Гал | 18:00 Финиш",
      stats: "🛣️ 140 км &nbsp;|&nbsp; ⛰️ +1 140 м &nbsp;|&nbsp; Асфальт 98%",
      km: 140, gain: 1140,
      links: [{ label: "🗺️ Маршрут Komoot", url: "https://www.komoot.com/tour/2212290644?ref=aso&share_token=ayB4F6gE56jhOjZ0oKxo5v4SbBecoxVl3f9q6RLZnPz5R2LGv3&t_s=referral&t_cid=route_share" }]
    });
  } else {
    schedule.push({
      day: "13 ОКТЯБРЯ • ВЕТКА ТКУАРЧАЛ",
      title: "Шахтерский Ткуарчал & Водопады",
      type: "Шоссе",
      desc: "Заезд в город-призрак Акармару, посещение водопада Золотоносец.",
      stats: "🛣️ 193 км &nbsp;|&nbsp; ⛰️ +1 300 м",
      km: 193, gain: 1300,
      links: [{ label: "🗺️ Маршрут Komoot", url: "https://www.komoot.com/tour/2944745402?ref=aso&share_token=aDEgMYQN5gSehzvu9MXrsX73uwIgd2bMr5CTW14zi3R53z237T&t_s=referral&t_cid=route_share" }]
    });
    schedule.push({
      day: "14 ОКТЯБРЯ • ВЕТКА ТКУАРЧАЛ",
      title: "Дорога на Гал",
      type: "Шоссе",
      desc: "Посещение города Гал и возвращение на сухумскую базу.",
      stats: "🛣 160 км &nbsp;|&nbsp; ⛰️ +600 м",
      km: 160, gain: 600,
      links: [{ label: "🗺️ Маршрут Komoot", url: "https://www.komoot.com/tour/3322902922?ref=aso&share_token=aJ9YzF0LA27jXUrfKjYfQJAXWH51XLjXjg09YSW00hApxXWMvn&t_s=referral&t_cid=route_share" }]
    });
  }

  schedule.push({
    day: "15 ОКТЯБРЯ",
    title: "🛫 День отъезда & Сборка велосипедов",
    type: "Финал",
    desc: "Утренняя заминка, упаковка велосипедов в чехлы, трансфер и отъезд участников.",
    stats: "👋 До новых встреч!",
    km: 0, gain: 0
  });

  const totalKm = schedule.reduce((sum, item) => sum + item.km, 0);
  const totalGain = schedule.reduce((sum, item) => sum + item.gain, 0);

  html += `
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 12px 14px; border-radius: 12px; margin-bottom: 16px; border: 1px dashed #38bdf8; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <div style="font-size: 11px; color: #94a3b8;">Итоговый суммарный план:</div>
        <div style="font-size: 15px; font-weight: bold; color: #fff; margin-top: 2px;">
          🛣️ ${totalKm} км &nbsp;|&nbsp; ⛰️ +${totalGain.toLocaleString()} м
        </div>
      </div>
      <span style="font-size: 20px;">🔥</span>
    </div>
  `;

  html += schedule.map(item => `
    <div class="card" style="border-left: 4px solid ${item.km > 0 ? '#38bdf8' : '#64748b'}; margin-bottom: 12px; background:#1e293b; padding:12px; border-radius:10px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
        <div style="font-size:10px; color:#38bdf8; font-weight:bold;">${item.day}</div>
        <span style="font-size:9px; background:rgba(255,255,255,0.1); color:#fff; padding:2px 6px; border-radius:4px; font-weight:bold;">${item.type}</span>
      </div>
      <h4 style="margin:2px 0 6px 0; color:#fff; font-size:14px;">${item.title}</h4>
      <p style="font-size:11px; color:#94a3b8; margin:0 0 8px 0; line-height: 1.4;">${item.desc}</p>
      <div style="font-size:11px; color:#cbd5e1; margin-bottom:10px;">${item.stats}</div>
      ${item.links ? `
        <div style="display:flex; gap:6px; flex-wrap:wrap;">
          ${item.links.map(l => `
            <a href="${l.url}" target="_blank" class="btn-primary-camp" style="font-size:10px; padding:5px 10px; text-decoration:none;">${l.label}</a>
          `).join('')}
        </div>
      ` : ''}
    </div>
  `).join('');

  container.innerHTML = html;
}

// ==================== ЧЕК-ЛИСТ УЧАСТНИКА ====================
function renderChecklistUI() {
  const container = document.getElementById('checklist-items');
  if (!container) return;

  const savedState = JSON.parse(localStorage.getItem('abhaz_checklist_state') || '{}');
  let html = '';
  let totalCount = 0;
  let checkedCount = 0;

  CAMP_CHECKLIST_DATA.forEach(cat => {
    html += `<div class="checklist-cat-card"><div class="checklist-cat-title">${cat.category}</div>`;
    
    cat.items.forEach(item => {
      totalCount++;
      const isChecked = !!savedState[item.id];
      if (isChecked) checkedCount++;

      html += `
        <label class="check-item-label ${isChecked ? 'checked' : ''}">
          <input type="checkbox" onchange="toggleCheckItem('${item.id}', this.checked)" ${isChecked ? 'checked' : ''}>
          <span>${item.label}</span>
        </label>
      `;
    });

    html += `</div>`;
  });

  container.innerHTML = html;

  const pct = totalCount > 0 ? Math.round((checkedCount / totalCount) * 100) : 0;
  const pBar = document.getElementById('checklist-progress-bar');
  const pCount = document.getElementById('checklist-count');

  if (pBar) pBar.style.width = pct + '%';
  if (pCount) pCount.innerText = `${checkedCount} / ${totalCount}`;
}

function toggleCheckItem(id, isChecked) {
  const savedState = JSON.parse(localStorage.getItem('abhaz_checklist_state') || '{}');
  savedState[id] = isChecked;
  localStorage.setItem('abhaz_checklist_state', JSON.stringify(savedState));
  renderChecklistUI();
}

// ==================== ПАМЯТКА УЧАСТНИКА ====================
function renderMemoUI() {
  const container = document.getElementById('camp-memo-content');
  if (!container) return;

  const mapLink = (query) => `https://yandex.ru/maps/?text=${encodeURIComponent('Гагра ' + query)}`;

  container.innerHTML = `
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 12px; padding: 14px; margin-bottom: 14px; border: 1px solid #38bdf8;">
      <p style="font-size: 13px; color: #f8fafc; margin: 0; line-height: 1.5;">
        <b>Друзья, памятка для удобства ориентирования в пространстве:</b> где поесть, что посмотреть, куда прогуляться!
      </p>
    </div>

    <div style="background: #1e293b; border-radius: 12px; padding: 14px; margin-bottom: 12px; border: 1px solid #334155;">
      <h4 style="margin: 0 0 10px 0; font-size: 15px; color: #38bdf8;">🍚 ЕДА</h4>
      <div style="font-size: 12px; color: #cbd5e1; line-height: 1.6; display: flex; flex-direction: column; gap: 10px;">
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Столовая LASTORIA</b>
            <a href="${mapLink('Столовая LASTORIA')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Вкусная кухня, разнообразное меню. Невысокий ценник.</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Ресторан "Кафе ПУШКИНЪ"</b>
            <a href="${mapLink('Кафе ПУШКИНЪ')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Отличная кухня. Большой выбор интересных блюд. <span style="color: #10b981; font-weight: bold;">Скидка 10% для велоклуба!</span></div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Ресторан МОККО</b>
            <a href="${mapLink('Ресторан МОККО')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Отличная кухня, большой выбор блюд, умеренный ценник, огромные порции. <span style="color: #ef4444;">Громкая музыка после 20:00!</span></div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Кафе MON CAFE</b>
            <a href="${mapLink('Mon Cafe')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Лучшие хинкали, небольшой выбор дополнительных блюд.</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Ресторан ЧЕГЕМ</b>
            <a href="${mapLink('Ресторан Чегем')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Национальная турецкая кухня. Отличный мангал. Вкусная кухня. Большой выбор блюд.</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Столовая ЕВРОПА</b>
            <a href="${mapLink('Столовая Европа')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Хорошая кухня, низкий чек. Оплата нал/безнал. Открыто с 9:00.</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Кондитерская BRIOCHE</b>
            <a href="${mapLink('Кондитерская Brioche')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Большой выбор кондитерки, шикарные десерты, много разного кофе. Место любимо многими велосипедистами.</div>
        </div>
      </div>
    </div>

    <div style="background: #1e293b; border-radius: 12px; padding: 14px; margin-bottom: 12px; border: 1px solid #334155;">
      <h4 style="margin: 0 0 10px 0; font-size: 15px; color: #38bdf8;">📞 СВЯЗЬ</h4>
      <div style="font-size: 12px; color: #cbd5e1; line-height: 1.6; display: flex; flex-direction: column; gap: 10px;">
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Офис AQUAFON</b>
            <a href="${mapLink('Аквафон')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Оптимальный оператор для западной Абхазии. Лимитированный трафик с безлимитной скоростью.</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪ Офис AMOBILE</b>
            <a href="${mapLink('A-Mobile')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Безлимитный трафик, лимитированная скорость. Оптимален для востока Абхазии.</div>
        </div>
        <div style="background: rgba(15, 23, 42, 0.6); padding: 8px 10px; border-radius: 8px; color: #cbd5e1; font-size: 11px;">
          💡 <i>У каждого оператора можно подключить временную симку на 3 месяца без паспорта или постоянную с паспортом.</i>
        </div>
      </div>
    </div>

    <div style="background: #1e293b; border-radius: 12px; padding: 14px; margin-bottom: 12px; border: 1px solid #334155;">
      <h4 style="margin: 0 0 10px 0; font-size: 15px; color: #38bdf8;">🚶 КУДА ПРОГУЛЯТЬСЯ</h4>
      <div style="font-size: 12px; color: #cbd5e1; line-height: 1.6; display: flex; flex-direction: column; gap: 10px;">
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Пансионат МАЯК</b>
            <a href="${mapLink('Пансионат Маяк')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Заброшка. 5 корпусов бывшего пансионата находятся на возвышении с красивым видом на город. Отличная локация для фото.</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Колесо ОБОЗРЕНИЯ</b>
            <a href="${mapLink('Колесо обозрения')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Рекомендуем прокатиться и встретить закат на нём.</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪ Дворец Принца Ольденбургского</b>
            <a href="${mapLink('Замок принца Ольденбургского')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Колоритный замок принца - основателя курорта Гагра. Вход ~150₽ (зависит от времени).</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Царский ПРИМОРСКИЙ ПАРК</b>
            <a href="${mapLink('Приморский парк')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Парк с 110 видами тропических растений. Начинается от колоннады и заканчивается причалом.</div>
        </div>
      </div>
    </div>

    <div style="background: #1e293b; border-radius: 12px; padding: 14px; margin-bottom: 12px; border: 1px solid #334155;">
      <h4 style="margin: 0 0 10px 0; font-size: 15px; color: #38bdf8;">🏃‍♀️ ЗДОРОВЬЕ</h4>
      <div style="font-size: 12px; color: #cbd5e1; line-height: 1.6; display: flex; flex-direction: column; gap: 10px;">
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪ БАЛЬНЕОЛЕЧЕБНИЦА</b>
            <a href="${mapLink('Бальнеолечебница')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Массаж Шарко, сероводородные ванны, небольшой бассейн и хамам.</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Массажный центр ДЫХАНИЕ ЖИЗНИ</b>
            <a href="${mapLink('Дыхание жизни')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Большой выбор услуг, включая спортивный массаж. <i>Запись через оргов.</i></div>
        </div>
      </div>
    </div>

    <div style="background: #1e293b; border-radius: 12px; padding: 14px; margin-bottom: 12px; border: 1px solid #334155;">
      <h4 style="margin: 0 0 10px 0; font-size: 15px; color: #38bdf8;">🛍 МАГАЗИНЫ</h4>
      <div style="font-size: 12px; color: #cbd5e1; line-height: 1.6; display: flex; flex-direction: column; gap: 10px;">
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Супермаркет АССОРТИ</b>
            <a href="${mapLink('Супермаркет Ассорти')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Неплохой выбор продуктов и хозтоваров. Ценник выше среднего. До 22:00.</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ ОСТРОВ ВКУСА (Продукты & Рыба)</b>
            <a href="${mapLink('Остров вкуса')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Хороший выбор, низкие цены. Всё по продуктам рекомендуем брать здесь. Рядом рыбный магазин. До 21:00.</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Супермаркет ТЦ ГАГРА</b>
            <a href="${mapLink('ТЦ Гагра')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Обширный выбор продуктов и хозтоваров. Ценник выше среднего. До 23:00.</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Магазин ДАУР</b>
            <a href="${mapLink('Магазин Даур')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Ночной магазин продуктов. Работает до 2:00 ночи.</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ Центральный РЫНОК</b>
            <a href="${mapLink('Центральный рынок')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Локальные продукты и сувениры. С 6:00 до 16:00 работает сельскохозяйственный оптово-розничный рынок.</div>
        </div>
      </div>
    </div>

    <div style="background: #1e293b; border-radius: 12px; padding: 14px; margin-bottom: 12px; border: 1px solid #334155;">
      <h4 style="margin: 0 0 10px 0; font-size: 15px; color: #38bdf8;">🏦 БАНКОМАТЫ (ближайшие)</h4>
      <div style="font-size: 12px; color: #cbd5e1; line-height: 1.6; display: flex; flex-direction: column; gap: 10px;">
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ АМРА-БАНК</b>
            <a href="${mapLink('Амра банк банкомат')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Круглосуточно (24/7).</div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="color: #fff;">▪️ ТЦ ГАГРА</b>
            <a href="${mapLink('ТЦ Гагра банкомат')}" target="_blank" style="background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 6px; text-decoration: none; font-size: 10px; font-weight: bold; border: 1px solid #334155;">📍 На карте</a>
          </div>
          <div style="color: #94a3b8; font-size: 11px; margin-top: 2px;">Доступен с 7:00 до 22:00.</div>
        </div>
      </div>
    </div>
  `;
}
