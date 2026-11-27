// ==================== БРОНИРОВАНИЕ СЛОТА ЧЕРЕЗ БОТА (DEEP LINK) ====================
function bookSlotViaBot(slotId) {
  const safeId = encodeURIComponent(String(slotId || '').trim());
  const botUrl = `https://t.me/AbhazBand_bot?start=book_${safeId}`;
  const tg = window.Telegram && window.Telegram.WebApp;
  if (tg && tg.HapticFeedback) {
    try { tg.HapticFeedback.impactOccurred('medium'); } catch (e) {}
  }
  if (tg && typeof tg.openTelegramLink === 'function') {
    tg.openTelegramLink(botUrl);
    if (typeof tg.close === 'function') {
      setTimeout(() => tg.close(), 150);
    }
    return;
  }
  window.open(botUrl, '_blank');
}

// ==================== РЕНДЕР КЭМПОВ ====================
function renderCamps() {
  const container = document.getElementById('camps-list');
  if (!container) return;
  
  let html = camps.map(camp => `
    <div class="card" id="${camp.id}">
      <img src="${camp.image}" alt="${camp.title}">
      <div class="card-body">
        <span class="badge">${camp.dates}</span>
        <h3 class="card-title">${camp.title}</h3>
        <div class="meta-line">📍 ${camp.location}</div>
        ${camp.specs ? `<div class="meta-line">🚴 ${camp.specs}</div>` : ''}
        <div class="meta-line" style="color:#4cd964; font-weight:bold; margin-top:6px;">💰 ${camp.price}</div>
        <p style="font-size:13px; color:var(--hint-color); margin: 8px 0;">${camp.description}</p>
        <button class="btn" onclick="openCampModal('${camp.id}')">Подробнее</button>
      </div>
    </div>
  `).join('');

  html += `
    <!-- Контейнер всплывающего окна для кэмпов (Bottom Sheet) -->
    <div id="camp-sheet-overlay" class="bottom-sheet-overlay" onclick="closeCampModal(event)">
      <div class="bottom-sheet-modal" id="camp-sheet-modal" onclick="event.stopPropagation()"></div>
    </div>
  `;

  container.innerHTML = html;
}

// Открытие всплывающего окна с подробностями кэмпа
function openCampModal(campId) {
  const camp = camps.find(c => c.id === campId);
  if (!camp) return;

  const modal = document.getElementById('camp-sheet-modal');
  const overlay = document.getElementById('camp-sheet-overlay');
  if (!modal || !overlay) return;

  if (window.Telegram?.WebApp?.HapticFeedback) {
    window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
  }

  // Нативная системная кнопка «Назад» в шапке Telegram
  if (window.Telegram?.WebApp?.BackButton) {
    window.Telegram.WebApp.BackButton.show();
    window.Telegram.WebApp.BackButton.onClick(closeCampModal);
  }

  // Генерация блока "Что включено", если он есть
  let includedHtml = '';
  if (camp.included && camp.included.length > 0) {
    includedHtml = `
      <div class="sheet-section-title" style="margin-top: 20px;">🎒 В стоимость входит:</div>
      <div style="margin-bottom: 24px;">
        ${camp.included.map(inc => `
          <div style="display: flex; align-items: flex-start; gap: 8px; margin-bottom: 8px; font-size: 13px; color: #cbd5e1; line-height: 1.4;">
            <span style="color: #38bdf8; font-weight: bold; flex-shrink: 0;">👉</span>
            <span>${inc}</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  // Генерация блока метрик (с добавлением км и набора, если они есть)
  const metricsHtml = `
    <div class="sheet-metrics-grid" style="margin-bottom:16px;">
      <div class="sheet-metric-box">
        <span class="sheet-metric-label">💰 Стоимость участия</span>
        <span class="sheet-metric-val" style="color:#4cd964; font-size:12px;">${camp.price}</span>
      </div>
      ${camp.specs ? `
      <div class="sheet-metric-box">
        <span class="sheet-metric-label">🚴 Формат</span>
        <span class="sheet-metric-val">${camp.specs}</span>
      </div>
      ` : ''}
      ${camp.totalKm ? `
      <div class="sheet-metric-box">
        <span class="sheet-metric-label">🛣️ Общий пробег</span>
        <span class="sheet-metric-val">${camp.totalKm}</span>
      </div>
      ` : ''}
      ${camp.totalGain ? `
      <div class="sheet-metric-box">
        <span class="sheet-metric-label">⛰️ Общий набор</span>
        <span class="sheet-metric-val">${camp.totalGain}</span>
      </div>
      ` : ''}
    </div>
  `;

  modal.innerHTML = `
    <div class="bottom-sheet-handle"></div>
    
    <!-- Навигация -->
    <div class="sheet-top-nav">
      <button class="sheet-back-btn" onclick="closeCampModal()">
        <span>‹</span> Вернуться в расписание
      </button>
      <button class="sheet-close-btn" onclick="closeCampModal()" title="Закрыть">✕</button>
    </div>

    <!-- Обложка кэмпа (поддержка отдельной картинки imageSheet) -->
    <img src="${camp.imageSheet || camp.image}" alt="${camp.title}" style="width:100%; height:200px; object-fit:cover; border-radius:12px; margin-bottom:12px;">

    <!-- Бейдж и Даты -->
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
      <span class="sheet-badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #38bdf8;">
        📅 ${camp.dates}
      </span>
    </div>

    <!-- Заголовок и локация -->
    <h3 class="sheet-title" style="margin-bottom:4px;">${camp.title}</h3>
    <div class="sheet-subtitle" style="margin-bottom:12px;">📍 ${camp.location}</div>

    ${metricsHtml}

    <!-- Описание кэмпа -->
    <div class="sheet-section-title">ℹ️ О кэмпе</div>
    <div style="font-size:13px; color:#cbd5e1; line-height:1.5; margin-bottom:24px;">
      ${camp.fullDesc || camp.description}
    </div>

    ${includedHtml}

  <!-- Кнопки действий -->
    <div style="display: flex; gap: 8px; position: sticky; bottom: 0; background: #0f172a; padding: 14px 12px 20px 12px; margin-top: 0; border-top: 1px solid rgba(56, 189, 248, 0.15); box-shadow: 0 -8px 16px rgba(15, 23, 42, 0.9); z-index: 10;">
      <button onclick="bookSlotViaBot('${camp.id}')" 
         class="btn" 
         style="flex: 2; padding: 12px 0; font-size: 13px; text-align: center;">
        ⛺ Занять слот в кэмп
      </button>
      <button onclick="shareCamp('${camp.title.replace(/'/g, "\\'")}', '${camp.dates.replace(/'/g, "\\'")}', '${camp.location.replace(/'/g, "\\'")}', '${camp.price.split('(')[0].trim().replace(/'/g, "\\'")}', '${camp.id}')" 
              class="btn btn-secondary" 
              style="flex: 1; padding: 12px 0; font-size: 13px; display: flex; align-items: center; justify-content: center; gap: 4px;">
        <span>✈️</span> Поделиться
      </button>
    </div>
   `;

  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

// Закрытие окна по клику на фон или кнопкам возврата
function closeCampModal(event) {
  if (event && event.target && event.target.closest('#camp-sheet-modal') && !event.target.closest('.sheet-back-btn') && !event.target.closest('.sheet-close-btn')) {
    return;
  }
  const overlay = document.getElementById('camp-sheet-overlay');
  if (overlay) {
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  if (window.Telegram?.WebApp?.BackButton) {
    window.Telegram.WebApp.BackButton.hide();
    window.Telegram.WebApp.BackButton.offClick(closeCampModal);
  }
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

    const EVENT_PRIORITY = { festival: 1, weekend: 2, social: 3, camp: 4 };
    const dayRides = rides
      .filter(r => r.dates && r.dates.includes(dateKey))
      .sort((a, b) => (EVENT_PRIORITY[a.type] || 99) - (EVENT_PRIORITY[b.type] || 99));
    const ride = dayRides[0];

    if (ride) {
      const classMap = {
        festival: 'event-festival',
        weekend: 'event-weekend',
        social: 'event-social',
        camp: 'event-camp'
      };
      const eventClass = classMap[ride.type] || 'event-social';
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
          <span class="legend-color-dot" style="background: #10b981; box-shadow: 0 0 6px rgba(16, 185, 129, 0.8);"></span>
          <span>Фестивали</span>
        </div>
        <div class="legend-item">
          <span class="legend-color-dot" style="background: #ef4444; box-shadow: 0 0 6px rgba(239, 68, 68, 0.8);"></span>
          <span>Weekend / Dour Tour</span>
        </div>
        <div class="legend-item">
          <span class="legend-color-dot" style="background: #38bdf8; box-shadow: 0 0 6px rgba(56, 189, 248, 0.8);"></span>
          <span>Social Ride</span>
        </div>
        <div class="legend-item">
          <span class="legend-color-dot" style="background: #f59e0b; box-shadow: 0 0 6px rgba(245, 158, 11, 0.8);"></span>
          <span>Кэмпы</span>
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

  // Нативная системная кнопка «Назад» в шапке Telegram
  if (window.Telegram?.WebApp?.BackButton) {
    window.Telegram.WebApp.BackButton.show();
    window.Telegram.WebApp.BackButton.onClick(closeRideModal);
  }

  modal.innerHTML = `
    <div class="bottom-sheet-handle"></div>
    
    <!-- Навигация: Кнопка «‹ В календарь» и Крестик -->
    <div class="sheet-top-nav">
      <button class="sheet-back-btn" onclick="closeRideModal()">
        <span>‹</span> Вернуться в календарь
      </button>
      <button class="sheet-close-btn" onclick="closeRideModal()" title="Закрыть">✕</button>
    </div>

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
      <button onclick="bookSlotViaBot('${ride.id}')" 
         class="btn" 
         style="flex: 2; padding: 12px 0; font-size: 13px; text-align: center;">
        🚴 Занять слот на этот выезд
      </button>
      <button onclick="shareRide('${ride.title.replace(/'/g, "\\'")}', '${ride.dateDisplay.replace(/'/g, "\\'")}', '${ride.id}')" 
              class="btn btn-secondary" 
              style="flex: 1; padding: 12px 0; font-size: 13px; display: flex; align-items: center; justify-content: center; gap: 4px;">
        <span>🔗</span> Поделиться
      </button>
    </div>
  `;

  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

// Закрытие окна по клику на фон или кнопкам возврата
function closeRideModal(event) {
  if (event && event.target && event.target.closest('#ride-sheet-modal') && !event.target.closest('.sheet-back-btn') && !event.target.closest('.sheet-close-btn')) {
    return;
  }
  const overlay = document.getElementById('ride-sheet-overlay');
  if (overlay) {
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  // Прячем системную стрелку Telegram и отвязываем слушатель
  if (window.Telegram?.WebApp?.BackButton) {
    window.Telegram.WebApp.BackButton.hide();
    window.Telegram.WebApp.BackButton.offClick(closeRideModal);
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

// ==================== ЛОГИКА КАБИНЕТА «МОЙ КЭМП» (СЛОТЫ + СИНХРОНИЗИРОВАННАЯ БАЗА GPX 2027) ====================
let userConfirmedSlots = [];
let activeUserSlot = null;
const activeLeafletMaps = {};
const gpxFileCache = {};

let fullscreenMapInstance = null;
let currentFullscreenTrack = null;

// Синхронизированная база треков Новогоднего кэмпа 2027 по актуальному списку файлов в Gpx/
const TRACKS_REGISTRY = {
  pitsunda_shosse: {
    label: 'Пицунда — Шоссе',
    gpxFile: 'Gpx/Pitsunda_shosse.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/1321206568?ref=aso&share_token=aWG49MO64K7t5GSiGNmAO1VJh65xzwAj6ZUwJvUiWkaopf7otl&t_s=referral&t_cid=route_share',
    coords: [[43.2785, 40.2654], [43.2250, 40.3120], [43.1610, 40.3400], [43.1530, 40.3480], [43.2250, 40.3120], [43.2785, 40.2654]],
    keywords: ['пицунд', 'амшын', 'реликтовый']
  },
  pitsunda_gravel: {
    label: 'Пицунда — Гравел',
    gpxFile: 'Gpx/Pitsunda_gravel.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/2920620509?ref=aso&share_token=aTotm7kS6lV8x1pozOTdf6P2gedqgBybX6Gpf6NE1f5rRHTT59&t_s=referral&t_cid=route_share',
    coords: [[43.2785, 40.2654], [43.2250, 40.3120], [43.1610, 40.3400], [43.1530, 40.3480], [43.2250, 40.3120], [43.2785, 40.2654]],
    keywords: ['пицунда гравел', 'гравел пицунд']
  },
  lychny_mussera_shosse: {
    label: 'Лыхны / Мюссера — Шоссе',
    gpxFile: 'Gpx/Lychny_Mussera_shosse.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/3229725192?ref=aso&share_token=a5dp3vGaOcX5tgL0cilnYV8zEH57L34BeFNf0MOvoFGjqvRzzX&t_s=referral&t_cid=route_share',
    coords: [[43.3935, 40.0085], [43.2785, 40.2654], [43.1680, 40.4710], [43.1765, 40.5560], [43.2785, 40.2654], [43.3935, 40.0085]],
    keywords: ['лыхн']
  },
  lychny_mussera_gravel: {
    label: 'Лыхны / Мюссера — Гравел',
    gpxFile: 'Gpx/Lychny_Mussera_gravel.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/2666494537?ref=aso&share_token=aVXqttvbkrJIxZkkeeT73LtG1Ly4BilW0gCo6c0BxgokxrRnlT&t_s=referral&t_cid=route_share',
    coords: [[43.3935, 40.0085], [43.2785, 40.2654], [43.1680, 40.4710], [43.1765, 40.5560], [43.2785, 40.2654], [43.3935, 40.0085]],
    keywords: ['лыхны гравел']
  },
  mussera_shosse: {
    label: 'Мюссера — Шоссе',
    gpxFile: 'Gpx/Mussera_shosse.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/3229725192?ref=aso&share_token=a5dp3vGaOcX5tgL0cilnYV8zEH57L34BeFNf0MOvoFGjqvRzzX&t_s=referral&t_cid=route_share',
    coords: [[43.3935, 40.0085], [43.2785, 40.2654], [43.1680, 40.4710], [43.3935, 40.0085]],
    keywords: ['мюссер', 'форел', 'псоу']
  },
  mussera_gravel: {
    label: 'Мюссера — Гравел',
    gpxFile: 'Gpx/Mussera_gravel.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/2666494537?ref=aso&share_token=aVXqttvbkrJIxZkkeeT73LtG1Ly4BilW0gCo6c0BxgokxrRnlT&t_s=referral&t_cid=route_share',
    coords: [[43.3935, 40.0085], [43.2785, 40.2654], [43.1680, 40.4710], [43.3935, 40.0085]],
    keywords: ['мюссера гравел', 'гравел мюссер']
  },
  khashupse_shosse: {
    label: 'Хашупсинский каньон — Шоссе',
    gpxFile: 'Gpx/khashupse_shosse.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/2007571282?ref=aso&share_token=aj8F9wH1K5myg1aMjSzHpuKfilaUzAmfAP5Wb2H5nj0dnHYLNG&t_s=referral&t_cid=route_share',
    coords: [[43.2785, 40.2654], [43.3680, 40.1650], [43.4020, 40.1280], [43.3680, 40.1650], [43.2785, 40.2654]],
    keywords: ['хашупс', 'цандрипш', 'каньон']
  },
  khashupse_gravel: {
    label: 'Хашупсинский каньон — Гравел',
    gpxFile: 'Gpx/khashupse_gravel.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/3405384462?ref=aso&share_token=av8P6Fv1yfh4SIUnZFQCoAl2qTlpK53bRqmML6l35Mz4Q0qQq6&t_s=referral&t_cid=route_share',
    coords: [[43.2785, 40.2654], [43.3680, 40.1650], [43.4020, 40.1280], [43.3680, 40.1650], [43.2785, 40.2654]],
    keywords: ['хашупс гравел', 'каньон гравел']
  },
  ritsa_shosse: {
    label: 'Рицинский заповедник — Шоссе',
    gpxFile: 'Gpx/ritsa_shosse.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/2163164931?ref=aso&share_token=am16MyeqIuonAwi1Zh2WT8TyeaoCEqAbKODb5gr9ftyqcG1M5u&t_s=referral&t_cid=route_share',
    coords: [[43.2785, 40.2654], [43.2350, 40.3520], [43.3560, 40.4250], [43.4740, 40.5330], [43.3560, 40.4250], [43.2785, 40.2654]],
    keywords: ['риц', 'заповедник', 'юпшар']
  },
  sukhum_teschin_yazyk: {
    label: 'На Сухум через Тёщин язык',
    gpxFile: 'Gpx/sukhum_teschin_yazyk.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/1547984937?ref=aso&share_token=azdhzg0HqYqn8zn5dJE8cDYbAbq41EddkEu82Xzbp1RCHL0bje&t_s=referral&t_cid=route_share',
    coords: [[43.2785, 40.2654], [43.1050, 40.6200], [43.0850, 40.8380], [43.0015, 41.0234]],
    keywords: ['тёщин', 'тещин', 'ачандар', 'афон']
  },
  sukhum_eshera: {
    label: 'На Сухум через Эшеру',
    gpxFile: 'Gpx/sukhum_eshera.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/2937858989?ref=aso&share_token=ayAUkQ0SCYWdcB3s4g4TLrTXBTYo1v47mSENkGy1h7pQWPnr2d&t_s=referral&t_cid=route_share',
    coords: [[43.2785, 40.2654], [43.1050, 40.6200], [43.0280, 40.9620], [43.0015, 41.0234]],
    keywords: ['эшер', 'нижне-эшер', 'сухум']
  },
  gal_city: {
    label: 'Дорога на Гал',
    gpxFile: 'Gpx/gal_city.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/2188906729?ref=aso&share_token=axKRfsfjKifyn6Q5M3Q6G83ptb0Fdga1qggsvNoXKpsaVxPQjC&t_s=referral&t_cid=route_share',
    coords: [[43.0015, 41.0234], [42.7120, 41.4680], [42.6270, 41.7380], [43.0015, 41.0234]],
    keywords: ['дорога на гал', 'г. гал', 'гал']
  },
  gal_ingur_ges_shosse: {
    label: 'Дорога к ИнгурГЭС — Шоссе',
    gpxFile: 'Gpx/Gal_ingur_ges_shosse.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/2212290644?ref=aso&share_token=ayB4F6gE56jhOjZ0oKxo5v4SbBecoxVl3f9q6RLZnPz5R2LGv3&t_s=referral&t_cid=route_share',
    coords: [[43.0015, 41.0234], [42.6270, 41.7380], [42.7590, 42.0320], [42.6270, 41.7380], [43.0015, 41.0234]],
    keywords: ['ингур', 'границ']
  },
  gal_ingur_ges_gravel: {
    label: 'Дорога к ИнгурГЭС — Гравел',
    gpxFile: 'Gpx/Gal_ingur_ges_gravel.gpx',
    status: 'ready',
    defaultKomoot: 'https://www.komoot.com/tour/3405405743?ref=aso&share_token=a9haR61gQ8Qjv6ftVyqGotZHCpXc52I88kWgMDhvUugXRLkkGJ&t_s=referral&t_cid=route_share',
    coords: [[43.0015, 41.0234], [42.6270, 41.7380], [42.7590, 42.0320], [42.6270, 41.7380], [43.0015, 41.0234]],
    keywords: ['ингур гравел', 'гравел ингур']
  }
};

// Состояние новогоднего кэмпа 2027
if (typeof campState === 'undefined' || !campState) {
  window.campState = {};
}
if (!campState.jan5Mode) campState.jan5Mode = 'khashupse'; // 'khashupse' | 'ritsa'
if (!campState.jan7Mode) campState.jan7Mode = 'teschin';   // 'teschin' | 'eshera'

function resolveTrackMeta(titleOrKey, variantHint) {
  const raw = (titleOrKey || '').trim();
  const norm = raw.toLowerCase();
  const hint = (variantHint || '').toLowerCase();

  if (TRACKS_REGISTRY[norm]) {
    const entry = TRACKS_REGISTRY[norm];
    return { key: norm, title: raw, ...entry };
  }

  if (norm.includes('пицунд') && (norm.includes('гравел') || hint.includes('гравел'))) {
    return { key: 'pitsunda_gravel', title: raw, ...TRACKS_REGISTRY.pitsunda_gravel };
  }
  if ((norm.includes('мюссер') || norm.includes('лыхн')) && (norm.includes('гравел') || hint.includes('гравел'))) {
    return { key: norm.includes('лыхн') ? 'lychny_mussera_gravel' : 'mussera_gravel', title: raw, ...(norm.includes('лыхн') ? TRACKS_REGISTRY.lychny_mussera_gravel : TRACKS_REGISTRY.mussera_gravel) };
  }
  if ((norm.includes('хашупс') || norm.includes('каньон')) && (norm.includes('гравел') || hint.includes('гравел'))) {
    return { key: 'khashupse_gravel', title: raw, ...TRACKS_REGISTRY.khashupse_gravel };
  }
  if (norm.includes('ингур') && (norm.includes('гравел') || hint.includes('гравел'))) {
    return { key: 'gal_ingur_ges_gravel', title: raw, ...TRACKS_REGISTRY.gal_ingur_ges_gravel };
  }

  for (const [key, entry] of Object.entries(TRACKS_REGISTRY)) {
    if (entry.keywords.some(kw => norm.includes(kw))) {
      return { key, title: raw, ...entry };
    }
  }

  return {
    key: 'pitsunda_shosse',
    title: raw || 'Маршрут Abhaz Band',
    ...TRACKS_REGISTRY.pitsunda_shosse
  };
}

function parseGpxCoordsFromXml(xmlText) {
  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(xmlText, 'application/xml');
    const trkpts = Array.from(doc.getElementsByTagName('trkpt'));
    const pts = trkpts.length > 0 ? trkpts : Array.from(doc.getElementsByTagName('rtept'));
    const coords = [];
    for (const pt of pts) {
      const lat = parseFloat(pt.getAttribute('lat'));
      const lon = parseFloat(pt.getAttribute('lon'));
      if (!Number.isNaN(lat) && !Number.isNaN(lon)) {
        coords.push([lat, lon]);
      }
    }
    return coords;
  } catch (e) {
    return null;
  }
}

async function loadTrackCoordsDynamic(meta) {
  const cacheKey = meta.gpxFile || meta.key;
  if (gpxFileCache[cacheKey]) {
    return gpxFileCache[cacheKey];
  }
  if (meta.gpxFile) {
    try {
      const resp = await fetch(`${meta.gpxFile}?v=${Date.now()}`, { cache: 'no-store' });
      if (resp.ok) {
        const txt = await resp.text();
        const parsed = parseGpxCoordsFromXml(txt);
        if (parsed && parsed.length >= 2) {
          const res = { coords: parsed, rawGpx: txt, source: 'gpx' };
          gpxFileCache[cacheKey] = res;
          return res;
        }
      }
    } catch (e) {
      // Файл в Gpx/ ещё не загружен или без расширения .gpx — используем опорную нитку маршрута
    }
  }
  const fallback = { coords: meta.coords || TRACKS_REGISTRY.pitsunda_shosse.coords, rawGpx: null, source: 'preset' };
  gpxFileCache[cacheKey] = fallback;
  return fallback;
}

function buildGpxXml(title, coords) {
  const pts = (coords || TRACKS_REGISTRY.pitsunda_shosse.coords)
    .map(c => `      <trkpt lat="${c[0]}" lon="${c[1]}"></trkpt>`)
    .join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Abhaz Band Hub" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>${(title || 'Abhaz Band Route').replace(/[<>&]/g, '')}</name>
    <trkseg>
${pts}
    </trkseg>
  </trk>
</gpx>`;
}

function downloadDynamicGpx(filename, title, meta) {
  const tg = window.Telegram && window.Telegram.WebApp;
  if (tg && tg.HapticFeedback) {
    try { tg.HapticFeedback.impactOccurred('light'); } catch (e) {}
  }

  const rawFileName = (meta && meta.gpxFile)
    ? meta.gpxFile.split('/').pop()
    : ((filename || (meta && meta.key) || 'abhazband_route') + '.gpx');
  const safeFileName = rawFileName.endsWith('.gpx') ? rawFileName : (rawFileName + '.gpx');

  if (meta && meta.gpxFile) {
    const fileUrl = new URL(meta.gpxFile, window.location.href).href;

    // 1. Нативное скачивание в Telegram Mini App (Bot API 8.0+)
    if (tg && typeof tg.downloadFile === 'function') {
      try {
        tg.downloadFile({ url: fileUrl, file_name: safeFileName }, (accepted) => {
          if (accepted === false) return;
        });
        return;
      } catch (e) {
        console.warn('tg.downloadFile fallback:', e);
      }
    }

    // 2. Резервный вариант для старых клиентов Telegram — открыть прямую ссылку в системном браузере
    if (tg && typeof tg.openLink === 'function') {
      tg.openLink(fileUrl);
      return;
    }
  }

  // 3. Обычный браузер (вне Telegram)
  loadTrackCoordsDynamic(meta).then(trackData => {
    const xmlStr = trackData.rawGpx || buildGpxXml(title, trackData.coords);
    const blob = new Blob([xmlStr], { type: 'application/gpx+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = safeFileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
}

function createOsmDarkTileLayer(map) {
  const layer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18
  });
  layer.on('tileload', (e) => {
    if (e.tile && e.tile.style) {
      e.tile.style.filter = 'invert(100%) hue-rotate(180deg) brightness(88%) contrast(108%)';
    }
  });
  layer.addTo(map);
  return layer;
}

function initTrackMap(mapId, meta, customBadgeId) {
  if (typeof L === 'undefined') return;
  const el = document.getElementById(mapId);
  if (!el) return;

  if (activeLeafletMaps[mapId]) {
    try { activeLeafletMaps[mapId].remove(); } catch (e) {}
  }

  const map = L.map(mapId, {
    zoomControl: false,
    attributionControl: false,
    dragging: true,
    scrollWheelZoom: false
  });
  createOsmDarkTileLayer(map);

  const initialPts = (meta.coords && meta.coords.length > 1) ? meta.coords : TRACKS_REGISTRY.pitsunda_shosse.coords;
  const poly = L.polyline(initialPts, { color: '#38bdf8', weight: 3.5, opacity: 0.95 }).addTo(map);
  const startMarker = L.circleMarker(initialPts[0], { radius: 5, color: '#10b981', fillColor: '#10b981', fillOpacity: 1 }).addTo(map);
  const endMarker = L.circleMarker(initialPts[initialPts.length - 1], { radius: 5, color: '#ef4444', fillColor: '#ef4444', fillOpacity: 1 }).addTo(map);

  const syncMapView = () => {
    if (!activeLeafletMaps[mapId]) return;
    if (el.offsetWidth > 0 && el.offsetHeight > 0) {
      map.invalidateSize({ animate: false });
      try {
        map.fitBounds(poly.getBounds(), { padding: [18, 18] });
      } catch (e) {}
    }
  };

  syncMapView();
  activeLeafletMaps[mapId] = map;

  // Автопересчёт размера карты при открытии вкладки «Мой кэмп» (убирает баг с 1 плиткой)
  if (typeof ResizeObserver !== 'undefined') {
    const ro = new ResizeObserver(() => {
      if (el.offsetWidth > 0 && el.offsetHeight > 0) {
        syncMapView();
      }
    });
    ro.observe(el);
    map.once('unload', () => ro.disconnect());
  }

  loadTrackCoordsDynamic(meta).then(trackData => {
    if (!activeLeafletMaps[mapId]) return;
    if (trackData.coords && trackData.coords.length >= 2) {
      poly.setLatLngs(trackData.coords);
      startMarker.setLatLng(trackData.coords[0]);
      endMarker.setLatLng(trackData.coords[trackData.coords.length - 1]);
      syncMapView();
    }
    if (customBadgeId) {
      const bEl = document.getElementById(customBadgeId);
      if (bEl) {
        bEl.innerText = trackData.source === 'gpx' ? 'GPX загружен' : (meta.status === 'check_ext' ? 'Проверить .gpx' : 'GPX в очереди');
      }
    }
  });
}

function openFullscreenMap(title, meta) {
  if (typeof L === 'undefined') return;
  currentFullscreenTrack = { title, meta };

  let modal = document.getElementById('gpx-fullscreen-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'gpx-fullscreen-modal';
    modal.style.cssText = 'position:fixed;inset:0;background:#0f172a;z-index:20000;display:flex;flex-direction:column;';
    modal.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 14px;background:#1e293b;border-bottom:1px solid #334155;">
        <div id="gpx-fs-title" style="font-size:14px;font-weight:700;color:#fff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding-right:10px;"></div>
        <button onclick="closeFullscreenMap()" style="background:#0f172a;color:#38bdf8;border:1px solid #334155;border-radius:8px;padding:6px 12px;font-weight:700;font-size:12px;cursor:pointer;flex-shrink:0;">✕ Закрыть</button>
      </div>
      <div id="gpx-fs-canvas" style="flex:1;width:100%;"></div>
      <div id="gpx-fs-actions" style="padding:12px 14px;background:#1e293b;border-top:1px solid #334155;display:flex;gap:8px;"></div>
    `;
    document.body.appendChild(modal);
  }

  modal.style.display = 'flex';
  document.getElementById('gpx-fs-title').innerText = title || 'Карта маршрута';

  const actionsEl = document.getElementById('gpx-fs-actions');
  actionsEl.innerHTML = `
    <a href="${meta.defaultKomoot}" target="_blank" class="btn-track-komoot">🗺️ Открыть в Komoot</a>
    <button onclick="downloadDynamicGpx('${meta.key}', '${(title || '').replace(/'/g, "\\'")}', currentFullscreenTrack.meta)" class="btn-track-gpx">⬇️ Скачать GPX</button>
  `;

  setTimeout(() => {
    if (fullscreenMapInstance) {
      try { fullscreenMapInstance.remove(); } catch (e) {}
    }
    const fsMap = L.map('gpx-fs-canvas', { zoomControl: true, attributionControl: false });
    createOsmDarkTileLayer(fsMap);
    const pts = (meta.coords && meta.coords.length > 1) ? meta.coords : TRACKS_REGISTRY.pitsunda_shosse.coords;
    const poly = L.polyline(pts, { color: '#38bdf8', weight: 4, opacity: 0.95 }).addTo(fsMap);
    L.circleMarker(pts[0], { radius: 6, color: '#10b981', fillColor: '#10b981', fillOpacity: 1 }).addTo(fsMap);
    L.circleMarker(pts[pts.length - 1], { radius: 6, color: '#ef4444', fillColor: '#ef4444', fillOpacity: 1 }).addTo(fsMap);
    fsMap.fitBounds(poly.getBounds(), { padding: [24, 24] });
    fullscreenMapInstance = fsMap;

    loadTrackCoordsDynamic(meta).then(trackData => {
      if (fullscreenMapInstance && trackData.coords && trackData.coords.length >= 2) {
        poly.setLatLngs(trackData.coords);
        fullscreenMapInstance.fitBounds(poly.getBounds(), { padding: [24, 24] });
      }
    });
  }, 50);
}

function closeFullscreenMap() {
  const modal = document.getElementById('gpx-fullscreen-modal');
  if (modal) modal.style.display = 'none';
  if (fullscreenMapInstance) {
    try { fullscreenMapInstance.remove(); } catch (e) {}
    fullscreenMapInstance = null;
  }
}

async function checkCampAccessOnLoad() {
  try {
    const userId = (typeof tgUser !== 'undefined' && tgUser?.id)
      ? Number(tgUser.id)
      : Number(window.Telegram?.WebApp?.initDataUnsafe?.user?.id || 0);

    let slots = [];
    if (userId && typeof fetchUserConfirmedSlots === 'function') {
      slots = await fetchUserConfirmedSlots(userId);
    }

    const isAdmin = typeof BROADCAST_ADMIN_ID !== 'undefined' && userId === Number(BROADCAST_ADMIN_ID);
    if (isAdmin && slots.length === 0) {
      slots = [
        { slot_id: 'camp_ny_2027', slot_type: 'camp', slot_title: 'Новогодний кэмп Abhaz Band 2027' },
        { slot_id: 'weekend_nov_28_29', slot_type: 'weekend', slot_title: 'Сухум — Очамчыра — Гал — ИнгурГЭС' },
        { slot_id: 'social_dec_5', slot_type: 'social', slot_title: 'Псоу — Мюссера — Форелевое хозяйство' }
      ];
    }

    if (slots.length > 0) {
      userConfirmedSlots = slots;
      activeUserSlot = slots[0];
      showUnlockedCamp();
      return;
    }

    const savedPin = localStorage.getItem('abhaz_camp_pin');
    if (savedPin === CAMP_SECRET_PIN) {
      userConfirmedSlots = [{ slot_id: 'camp_ny_2027', slot_type: 'camp', slot_title: 'Новогодний кэмп Abhaz Band 2027' }];
      activeUserSlot = userConfirmedSlots[0];
      showUnlockedCamp();
    }
  } catch (e) {
    console.error('Ошибка проверки доступа в Мой кэмп:', e);
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
    userConfirmedSlots = [{ slot_id: 'camp_ny_2027', slot_type: 'camp', slot_title: 'Новогодний кэмп Abhaz Band 2027' }];
    activeUserSlot = userConfirmedSlots[0];
    showUnlockedCamp();
  } else {
    if (errorMsg) errorMsg.style.display = 'block';
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.notificationOccurred('error');
    }
  }
}

function selectActiveUserSlot(slotId) {
  const found = userConfirmedSlots.find(s => s.slot_id === slotId);
  if (!found) return;
  activeUserSlot = found;
  if (window.Telegram?.WebApp?.HapticFeedback) {
    window.Telegram.WebApp.HapticFeedback.selectionChanged();
  }
  renderSlotSwitcher();
  updateCampHeaderForSlot();
  renderTracksList();
}

function renderSlotSwitcher() {
  const box = document.getElementById('my-camp-slot-switcher');
  if (!box) return;
  if (userConfirmedSlots.length <= 1) {
    box.style.display = 'none';
    return;
  }
  box.style.display = 'flex';
  const iconMap = { camp: '🏕️', weekend: '🔴', social: '🟢', festival: '🏆' };
  box.innerHTML = userConfirmedSlots.map(s => {
    const isAct = activeUserSlot && activeUserSlot.slot_id === s.slot_id;
    const icon = iconMap[s.slot_type] || '🚴';
    const shortName = (s.slot_title || s.slot_id).slice(0, 22);
    return `<button class="slot-pill ${isAct ? 'active' : ''}" onclick="selectActiveUserSlot('${s.slot_id}')">${icon} ${shortName}</button>`;
  }).join('');
}

function updateCampHeaderForSlot() {
  const pill = document.getElementById('camp-status-pill');
  const titleEl = document.getElementById('camp-title-display');
  const datesEl = document.getElementById('camp-dates-display');
  if (!activeUserSlot) return;

  const sType = activeUserSlot.slot_type || 'camp';
  const matchedRide = (typeof rides !== 'undefined') ? rides.find(r => r.id === activeUserSlot.slot_id) : null;
  const matchedCamp = (typeof camps !== 'undefined') ? camps.find(c => c.id === activeUserSlot.slot_id) : null;

  if (sType === 'weekend') {
    if (pill) { pill.innerText = '🔴 Weekend Camp (2 дня)'; pill.style.background = '#ef4444'; }
    if (titleEl) titleEl.innerText = matchedRide ? matchedRide.title : (activeUserSlot.slot_title || 'Abhaz Band Weekend');
    if (datesEl) datesEl.innerText = matchedRide ? `📅 ${matchedRide.dateDisplay} | ${matchedRide.stats?.distance || ''}` : '📅 2 дня | Абхазия';
  } else if (sType === 'social' || sType === 'festival') {
    if (pill) { pill.innerText = sType === 'festival' ? '🏆 Фестиваль / Гонка' : '🟢 Social Ride (1 день)'; pill.style.background = '#10b981'; }
    if (titleEl) titleEl.innerText = matchedRide ? matchedRide.title : (activeUserSlot.slot_title || 'Abhaz Band Social Ride');
    if (datesEl) datesEl.innerText = matchedRide ? `📅 ${matchedRide.dateDisplay} | ${matchedRide.stats?.distance || ''}` : '📅 1 день | Абхазия';
  } else {
    const isRitsa = campState.jan5Mode === 'ritsa';
    const summaryText = isRitsa ? '🛣️ 615 км | ⛰️ +5 170 м' : '🛣️ 617 км | ⛰️ +4 900 м';
    if (pill) { pill.innerText = '🎄 Новогодний кэмп 2027'; pill.style.background = '#38bdf8'; pill.style.color = '#0f172a'; }
    if (titleEl) titleEl.innerText = matchedCamp ? matchedCamp.title : (activeUserSlot.slot_title || 'Новогодний кэмп Abhaz Band 2027');
    if (datesEl) datesEl.innerText = `📅 1 – 10 января 2027 | ${summaryText}`;
  }
}

function showUnlockedCamp() {
  const lockCard = document.getElementById('my-camp-locked');
  const unlockedDash = document.getElementById('my-camp-unlocked');

  if (lockCard) lockCard.style.display = 'none';
  if (unlockedDash) unlockedDash.style.display = 'block';

  renderSlotSwitcher();
  updateCampHeaderForSlot();
  renderTracksList();
  renderChecklistUI();
  renderMemoUI();
}

function updateCampOption(key, val) {
  campState[key] = val;
  if (window.Telegram?.WebApp?.HapticFeedback) {
    window.Telegram.WebApp.HapticFeedback.selectionChanged();
  }
  updateCampHeaderForSlot();
  renderTracksList();
}

function renderRideSlotDashboard(container, slot) {
  const matchedRide = (typeof rides !== 'undefined') ? rides.find(r => r.id === slot.slot_id) : null;
  const title = matchedRide ? matchedRide.title : (slot.slot_title || 'Выезд Abhaz Band');
  const meta = resolveTrackMeta(matchedRide?.trackKey || slot.slot_id || title, title);
  const mapId = 'slot-track-map-' + slot.slot_id.replace(/[^a-zA-Z0-9]/g, '_');
  const badgeId = 'slot-track-badge-' + slot.slot_id.replace(/[^a-zA-Z0-9]/g, '_');
  const komootUrl = matchedRide?.komootUrl || meta.defaultKomoot;

  const statsHtml = matchedRide?.stats ? `
    <div class="sheet-metrics-grid" style="margin-bottom:14px;">
      <div class="sheet-metric-box"><span class="sheet-metric-label">🛣️ Дистанция</span><span class="sheet-metric-val">${matchedRide.stats.distance}</span></div>
      <div class="sheet-metric-box"><span class="sheet-metric-label">⛰️ Набор высоты</span><span class="sheet-metric-val">${matchedRide.stats.elevation}</span></div>
      <div class="sheet-metric-box"><span class="sheet-metric-label">⚡ Темп</span><span class="sheet-metric-val">${matchedRide.stats.pace}</span></div>
      <div class="sheet-metric-box"><span class="sheet-metric-label">🛤️ Покрытие</span><span class="sheet-metric-val">${matchedRide.stats.surface}</span></div>
    </div>
  ` : '';

  const timingHtml = matchedRide?.timing ? `
    <div class="card" style="background:#1e293b; padding:12px; border-radius:12px; margin-bottom:14px; border:1px solid #334155;">
      <div class="sheet-section-title" style="margin-top:0;">⏰ Тайминг & Логистика</div>
      ${matchedRide.timing.map(t => `
        <div class="sheet-timing-item">
          <span class="sheet-time-tag">${t.time}</span>
          <span class="sheet-timing-desc">${t.text}</span>
        </div>
      `).join('')}
    </div>
  ` : '';

  container.innerHTML = `
    ${statsHtml}
    <div class="card" style="background:#1e293b; padding:12px; border-radius:12px; margin-bottom:14px; border-left:4px solid #38bdf8;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
        <div style="font-size:11px; color:#38bdf8; font-weight:bold;">🗺️ ИНТЕРАКТИВНЫЙ ТРЕК МАРШРУТА</div>
        <div style="display:flex;gap:6px;align-items:center;">
          <span id="${badgeId}" style="font-size:9px;background:rgba(56,189,248,0.15);color:#38bdf8;padding:2px 6px;border-radius:4px;font-weight:700;">OSM</span>
          <button onclick="openFullscreenMap('${title.replace(/'/g, "\\'")}', window.__activeSlotMeta)" style="background:#0f172a;color:#fff;border:1px solid #475569;border-radius:6px;padding:2px 7px;font-size:10px;cursor:pointer;">⛶ На весь экран</button>
        </div>
      </div>
      <h4 style="margin:0 0 6px 0; color:#fff; font-size:14px;">${title}</h4>
      <div id="${mapId}" class="track-map-box"></div>
      <div class="track-actions-row">
        <a href="${komootUrl}" target="_blank" class="btn-track-komoot">🗺️ Открыть в Komoot</a>
        <button class="btn-track-gpx" id="dl-gpx-${mapId}">⬇️ Скачать GPX</button>
      </div>
    </div>
    ${timingHtml}
  `;

  window.__activeSlotMeta = meta;

  setTimeout(() => {
    initTrackMap(mapId, meta, badgeId);
    const dlBtn = document.getElementById('dl-gpx-' + mapId);
    if (dlBtn) {
      dlBtn.onclick = () => downloadDynamicGpx(slot.slot_id, title, meta);
    }
  }, 60);
}

function renderTracksList() {
  const container = document.getElementById('gpx-tracks-list');
  if (!container) return;

  if (activeUserSlot && activeUserSlot.slot_type !== 'camp') {
    renderRideSlotDashboard(container, activeUserSlot);
    return;
  }

  const isRitsa = campState.jan5Mode === 'ritsa';
  const isEshera = campState.jan7Mode === 'eshera';

  let html = `
    <div style="background: #0f172a; padding: 12px; border-radius: 12px; margin-bottom: 16px; border: 1px solid #334155;">
      <div style="font-size: 11px; color: #94a3b8; font-weight: bold; margin-bottom: 8px; text-transform: uppercase;">⚙️ Настройка маршрутной программы (1–10 января 2027)</div>
      
      <div style="margin-bottom: 10px;">
        <span style="font-size: 12px; color: #cbd5e1; display: block; margin-bottom: 4px;">🏔️ Вариант 5 января:</span>
        <div style="display: flex; gap: 6px;">
          <button onclick="updateCampOption('jan5Mode', 'khashupse')" class="sub-tab-btn ${!isRitsa ? 'active' : ''}" style="flex:1; padding:6px;">Хашупсинский каньон</button>
          <button onclick="updateCampOption('jan5Mode', 'ritsa')" class="sub-tab-btn ${isRitsa ? 'active' : ''}" style="flex:1; padding:6px;">Рицинский заповедник</button>
        </div>
      </div>

      <div>
        <span style="font-size: 12px; color: #cbd5e1; display: block; margin-bottom: 4px;">🔀 Вариант 7 января (Дорога на Сухум):</span>
        <div style="display: flex; gap: 6px;">
          <button onclick="updateCampOption('jan7Mode', 'teschin')" class="sub-tab-btn ${!isEshera ? 'active' : ''}" style="flex:1; padding:6px;">Через Тёщин язык</button>
          <button onclick="updateCampOption('jan7Mode', 'eshera')" class="sub-tab-btn ${isEshera ? 'active' : ''}" style="flex:1; padding:6px;">Через Эшеру</button>
        </div>
      </div>
    </div>
  `;

  const jan5Item = isRitsa
    ? {
        day: "5 ЯНВАРЯ",
        title: "Рицинский заповедник (шоссе)",
        trackKey: "ritsa_shosse",
        type: "Шоссе",
        desc: "Один из самых красивых маршрутов в мире. Пролегает через ущелье с множеством запоминающихся видов.<br>🕕 10:30 Выезд на маршрут | 🕕 15:30 Обед в классическом охотничьем балагане | 🕕 18:00 Возвращение с маршрута.",
        stats: "🛣️ 105 км &nbsp;|&nbsp; ⛰️ +1 370 м &nbsp;|&nbsp; Асфальт 100%",
        km: 105, gain: 1370,
        links: [{ label: "🗺️ Маршрут Komoot", url: "https://www.komoot.com/tour/2163164931?ref=aso&share_token=am16MyeqIuonAwi1Zh2WT8TyeaoCEqAbKODb5gr9ftyqcG1M5u&t_s=referral&t_cid=route_share" }]
      }
    : {
        day: "5 ЯНВАРЯ (ХАШУПСЕ ИЛИ РИЦА)",
        title: "По Гагре в Хашупсинский каньон",
        trackKey: "khashupse_shosse",
        gravelTrackKey: "khashupse_gravel",
        type: "Шоссе & Гравел",
        desc: "Поездка к Хашупсинскому каньону и прогулка по нему. Посещение города Цандрипш.<br>🕕 10:00 Выезд на маршрут | 🕕 15:00 Обед в Цандрипше | 🕕 18:00 Финиш.",
        stats: "🛣️ 107 км &nbsp;|&nbsp; ⛰️ +1 100 м &nbsp;|&nbsp; Асфальт 90%",
        km: 107, gain: 1100,
        links: [
          { label: "🗺️ Шоссе Komoot", url: "https://www.komoot.com/tour/2007571282?ref=aso&share_token=aj8F9wH1K5myg1aMjSzHpuKfilaUzAmfAP5Wb2H5nj0dnHYLNG&t_s=referral&t_cid=route_share", variant: "шоссе" },
          { label: "🗺️ Гравел Komoot", url: "https://www.komoot.com/tour/3405384462?ref=aso&share_token=av8P6Fv1yfh4SIUnZFQCoAl2qTlpK53bRqmML6l35Mz4Q0qQq6&t_s=referral&t_cid=route_share", variant: "гравел" }
        ]
      };

  const jan7Item = isEshera
    ? {
        day: "7 ЯНВАРЯ • ЧЕРЕЗ ЭШЕРУ",
        title: "Дорога на Сухум (через Эшеру)",
        trackKey: "sukhum_eshera",
        type: "Шоссе / Переезд",
        desc: "День переезда на восточную базу в Сухум. Заезд в Ачандару, Новый Афон и Нижне-Эшерскую дорогу.<br>🕕 09:00 Выезд на маршрут | 🕕 14:00 Обед | 🕕 18:00 Возвращение с маршрута.",
        stats: "🛣️ 110 км &nbsp;|&nbsp; ⛰️ +800 м &nbsp;|&nbsp; Асфальт 90%",
        km: 110, gain: 800,
        links: [{ label: "🗺️ Маршрут Komoot", url: "https://www.komoot.com/tour/2937858989?ref=aso&share_token=ayAUkQ0SCYWdcB3s4g4TLrTXBTYo1v47mSENkGy1h7pQWPnr2d&t_s=referral&t_cid=route_share" }]
      }
    : {
        day: "7 ЯНВАРЯ • ЧЕРЕЗ ТЁЩИН ЯЗЫК",
        title: "Дорога на Сухум (через Тёщин язык)",
        trackKey: "sukhum_teschin_yazyk",
        type: "Шоссе / Переезд",
        desc: "День переезда на восточную базу в Сухум. Заезд в Ачандару, Новый Афон и перевал Тёщин язык.<br>🕕 09:00 Выезд на маршрут | 🕕 14:00 Обед | 🕕 18:00 Возвращение с маршрута.",
        stats: "🛣️ 110 км &nbsp;|&nbsp; ⛰️ +800 м &nbsp;|&nbsp; Асфальт 90%",
        km: 110, gain: 800,
        links: [{ label: "🗺️ Маршрут Komoot", url: "https://www.komoot.com/tour/1547984937?ref=aso&share_token=azdhzg0HqYqn8zn5dJE8cDYbAbq41EddkEu82Xzbp1RCHL0bje&t_s=referral&t_cid=route_share" }]
      };

  const schedule = [
    {
      day: "1–2 ЯНВАРЯ",
      title: "День приезда",
      type: "Оргдень",
      desc: "Встреча катальцев. Совместная сборка велосипедов.<br>‼️ Для ребят, прибывших 1-го января, 2-го по желанию вкаточный маршрут.<br>🕕 <b>20:00</b> Вечерний ужин.",
      stats: "📍 База Abhaz Band",
      km: 0, gain: 0
    },
    {
      day: "3 ЯНВАРЯ",
      title: "Пицундский маршрут",
      trackKey: "pitsunda_shosse",
      gravelTrackKey: "pitsunda_gravel",
      type: "Шоссе & Гравел",
      desc: "Разминочная вкатка. Наслаждение красотами Пицунды, проезд через Реликтовый лес, Золотой берег, небольшие наборы.<br>🕕 11:00 Выезд на маршрут | 🕕 13:00 Кофе и перекус в ресторане Амшын | 🕕 16:00 Возвращение | 🕕 18:00 Ужин.",
      stats: "🛣️ 70 км &nbsp;|&nbsp; ⛰️ +290 м &nbsp;|&nbsp; Асфальт 100%",
      km: 70, gain: 290,
      links: [
        { label: "🗺️ Шоссе Komoot", url: "https://www.komoot.com/tour/1321206568?ref=aso&share_token=aWG49MO64K7t5GSiGNmAO1VJh65xzwAj6ZUwJvUiWkaopf7otl&t_s=referral&t_cid=route_share", variant: "шоссе" },
        { label: "🗺️ Гравел Komoot", url: "https://www.komoot.com/tour/2920620509?ref=aso&share_token=aTotm7kS6lV8x1pozOTdf6P2gedqgBybX6Gpf6NE1f5rRHTT59&t_s=referral&t_cid=route_share", variant: "гравел" }
      ]
    },
    {
      day: "4 ЯНВАРЯ",
      title: "Дорога на Лыхны/Мюссеру. Дополненный",
      trackKey: "lychny_mussera_shosse",
      gravelTrackKey: "lychny_mussera_gravel",
      type: "Шоссе & Гравел",
      desc: "Один из любимейших маршрутов в новом исполнении. Дороги с околонулевым трафиком и отличные виды!<br>🕕 10:00 Выезд на маршрут | 🕕 14:00 Обед | 🕕 18:00 Возвращение с маршрута.",
      stats: "🛣️ 105 км &nbsp;|&nbsp; ⛰️ ~1 250 м &nbsp;|&nbsp; Асфальт 85%, грунты 15%",
      km: 105, gain: 1250,
      links: [
        { label: "🗺️ Шоссе Komoot", url: "https://www.komoot.com/tour/3229725192?ref=aso&share_token=a5dp3vGaOcX5tgL0cilnYV8zEH57L34BeFNf0MOvoFGjqvRzzX&t_s=referral&t_cid=route_share", variant: "шоссе" },
        { label: "🗺️ Гравел Komoot", url: "https://www.komoot.com/tour/2666494537?ref=aso&share_token=aVXqttvbkrJIxZkkeeT73LtG1Ly4BilW0gCo6c0BxgokxrRnlT&t_s=referral&t_cid=route_share", variant: "гравел" }
      ]
    },
    jan5Item,
    {
      day: "6 ЯНВАРЯ",
      title: "Выходной. День отдыха",
      type: "Rest Day",
      desc: "Восстановление. Посещение термальных источников/бани, возможность самостоятельного планирования и отдыха, хайкинг.",
      stats: "♨️ День восстановления",
      km: 0, gain: 0
    },
    jan7Item,
    {
      day: "8 ЯНВАРЯ",
      title: "Дорога на Гал",
      trackKey: "gal_city",
      type: "Шоссе",
      desc: "Посещение и ночёвка в самом удалённом городе Абхазии — г. Гал.<br>🕕 11:00 Выезд на маршрут | 🕕 15:00 Обед в кафе г. Гал | 🕕 17:00 Финиш маршрута.",
      stats: "🛣️ 85 км &nbsp;|&nbsp; ⛰️ +320 м &nbsp;|&nbsp; Асфальт 100%",
      km: 85, gain: 320,
      links: [{ label: "🗺️ Маршрут Komoot", url: "https://www.komoot.com/tour/2188906729?ref=aso&share_token=axKRfsfjKifyn6Q5M3Q6G83ptb0Fdga1qggsvNoXKpsaVxPQjC&t_s=referral&t_cid=route_share" }]
    },
    {
      day: "9 ЯНВАРЯ",
      title: "Дорога к ИнгурГЭС",
      trackKey: "gal_ingur_ges_shosse",
      gravelTrackKey: "gal_ingur_ges_gravel",
      type: "Шоссе & Гравел",
      desc: "Поездка на гидроэлектростанцию ИнгурГЭС и на границу с Грузией. Возвращение на базу в Сухум.<br>🕕 09:00 Выезд на маршрут | 🕕 15:00 Обед в кафе г. Гал | 🕕 18:00 Финиш маршрута.",
      stats: "🛣️ 140 км &nbsp;|&nbsp; ⛰️ +1 140 м &nbsp;|&nbsp; Асфальт 98%",
      km: 140, gain: 1140,
      links: [
        { label: "🗺️ Шоссе Komoot", url: "https://www.komoot.com/tour/2212290644?ref=aso&share_token=ayB4F6gE56jhOjZ0oKxo5v4SbBecoxVl3f9q6RLZnPz5R2LGv3&t_s=referral&t_cid=route_share", variant: "шоссе" },
        { label: "🗺️ Гравел Komoot", url: "https://www.komoot.com/tour/3405405743?ref=aso&share_token=a9haR61gQ8Qjv6ftVyqGotZHCpXc52I88kWgMDhvUugXRLkkGJ&t_s=referral&t_cid=route_share", variant: "гравел" }
      ]
    },
    {
      day: "10 ЯНВАРЯ",
      title: "День отъезда. Сборка и упаковка велов",
      type: "Финал",
      desc: "Утренняя заминка, сборка и упаковка велосипедов, трансфер и отъезд.",
      stats: "👋 До новых встреч!",
      km: 0, gain: 0
    }
  ];

  const totalKm = isRitsa ? 615 : 617;
  const totalGain = isRitsa ? 5170 : 4900;

  html += `
    <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 12px 14px; border-radius: 12px; margin-bottom: 16px; border: 1px dashed #38bdf8; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <div style="font-size: 11px; color: #94a3b8;">Итого по программе (${isRitsa ? '5 января — Рица' : '5 января — Хашупсинский каньон'}):</div>
        <div style="font-size: 15px; font-weight: bold; color: #fff; margin-top: 2px;">
          🛣️ ${totalKm} км &nbsp;|&nbsp; ⛰️ +${totalGain.toLocaleString()} м
        </div>
      </div>
      <span style="font-size: 20px;">🎄</span>
    </div>
  `;

  const mapsToInit = [];
  window.__campDayMetas = {};

  html += schedule.map((item, idx) => {
    const mapId = `camp-day-map-${idx}`;
    const badgeId = `camp-day-badge-${idx}`;
    const hasRoute = item.km > 0;
    const meta = hasRoute ? resolveTrackMeta(item.trackKey || item.title, item.title) : null;
    const gravelMeta = (hasRoute && item.gravelTrackKey) ? resolveTrackMeta(item.gravelTrackKey, item.title + ' гравел') : null;
    if (hasRoute) {
      window.__campDayMetas[idx] = meta;
      mapsToInit.push({ mapId, badgeId, meta, gravelMeta, title: item.title });
    }

    return `
      <div class="card" style="border-left: 4px solid ${hasRoute ? '#38bdf8' : '#64748b'}; margin-bottom: 12px; background:#1e293b; padding:12px; border-radius:10px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
          <div style="font-size:10px; color:#38bdf8; font-weight:bold;">${item.day}</div>
          <div style="display:flex;gap:6px;align-items:center;">
            ${hasRoute ? `<span id="${badgeId}" style="font-size:9px;background:rgba(56,189,248,0.15);color:#38bdf8;padding:2px 6px;border-radius:4px;font-weight:700;">${meta.status === 'ready' ? 'GPX готов' : 'Проверить .gpx'}</span>` : ''}
            <span style="font-size:9px; background:rgba(255,255,255,0.1); color:#fff; padding:2px 6px; border-radius:4px; font-weight:bold;">${item.type}</span>
          </div>
        </div>
        <h4 style="margin:2px 0 6px 0; color:#fff; font-size:14px;">${item.title}</h4>
        <p style="font-size:11px; color:#94a3b8; margin:0 0 8px 0; line-height: 1.4;">${item.desc}</p>
        <div style="font-size:11px; color:#cbd5e1; margin-bottom:8px;">${item.stats}</div>
        ${hasRoute ? `
          <div style="display:flex;justify-content:flex-end;margin-bottom:4px;">
            <button onclick="openFullscreenMap('${item.title.replace(/'/g, "\\'")}', window.__campDayMetas[${idx}])" style="background:#0f172a;color:#38bdf8;border:1px solid #334155;border-radius:6px;padding:3px 8px;font-size:10px;font-weight:700;cursor:pointer;">⛶ На весь экран</button>
          </div>
          <div id="${mapId}" class="track-map-box"></div>
        ` : ''}
        ${item.links ? `
          <div class="track-actions-row">
            ${item.links.map(l => `
              <a href="${l.url}" target="_blank" class="btn-track-komoot">${l.label}</a>
            `).join('')}
            ${hasRoute ? (gravelMeta ? `
              <button class="btn-track-gpx" id="dl-gpx-road-${mapId}">⬇️ GPX Шоссе</button>
              <button class="btn-track-gpx" id="dl-gpx-gravel-${mapId}">⬇️ GPX Гравел</button>
            ` : `<button class="btn-track-gpx" id="dl-gpx-${mapId}">⬇️ Скачать GPX</button>`) : ''}
          </div>
        ` : ''}
      </div>
    `;
  }).join('');

  container.innerHTML = html;

  setTimeout(() => {
    mapsToInit.forEach(m => {
      initTrackMap(m.mapId, m.meta, m.badgeId);
      if (m.gravelMeta) {
        const btnRoad = document.getElementById('dl-gpx-road-' + m.mapId);
        if (btnRoad) btnRoad.onclick = () => downloadDynamicGpx(m.meta.key, m.title + ' (Шоссе)', m.meta);
        const btnGravel = document.getElementById('dl-gpx-gravel-' + m.mapId);
        if (btnGravel) btnGravel.onclick = () => downloadDynamicGpx(m.gravelMeta.key, m.title + ' (Гравел)', m.gravelMeta);
      } else {
        const btn = document.getElementById('dl-gpx-' + m.mapId);
        if (btn) btn.onclick = () => downloadDynamicGpx(m.meta.key, m.title, m.meta);
      }
    });
  }, 80);
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