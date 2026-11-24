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
      <a href="https://t.me/Piti4?text=${encodeURIComponent('Привет! Хочу задать вопрос/забронировать слот в кэмп: ' + camp.title + ' (' + camp.dates + ')')}" 
         target="_blank" 
         class="btn" 
         style="flex: 2; padding: 12px 0; font-size: 13px; text-align: center; text-decoration: none;">
        💬 Задать вопрос / Забронировать
      </a>
      <button onclick="shareCamp('${camp.title.replace(/'/g, "\\'")}', '${camp.dates.replace(/'/g, "\\'")}', '${camp.location.replace(/'/g, "\\'")}', '${camp.price.split('(')[0].trim().replace(/'/g, "\\'")}')" 
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

// ==================== ЛОГИКА КАБИНЕТА «МОЙ КЭМП» (СЛОТЫ + ВИЗУАЛЬНЫЕ ТРЕКИ) ====================
let userConfirmedSlots = [];
let activeUserSlot = null;
const activeLeafletMaps = {};

// Базовые координаты ключевых маршрутов Абхазии для визуализации трека на карте и генерации GPX
const ROUTE_COORDS_PRESETS = {
  pitsunda: [[43.2785, 40.2654], [43.2250, 40.3120], [43.1610, 40.3400], [43.1530, 40.3480], [43.2250, 40.3120], [43.2785, 40.2654]],
  mussera: [[43.3935, 40.0085], [43.2785, 40.2654], [43.1680, 40.4710], [43.1765, 40.5560], [43.2785, 40.2654], [43.3935, 40.0085]],
  gagra: [[43.2785, 40.2654], [43.3260, 40.2230], [43.3320, 40.2140], [43.2950, 40.2600], [43.2785, 40.2654]],
  ritsa: [[43.2785, 40.2654], [43.2350, 40.3520], [43.3560, 40.4250], [43.4740, 40.5330], [43.3560, 40.4250], [43.2785, 40.2654]],
  sukhum: [[43.0015, 41.0234], [43.0580, 41.0720], [43.0850, 40.8380], [43.0015, 41.0234]],
  transit: [[43.2785, 40.2654], [43.1050, 40.6200], [43.0850, 40.8380], [43.0015, 41.0234]],
  ingur: [[43.0015, 41.0234], [42.7120, 41.4680], [42.6270, 41.7380], [42.7590, 42.0320], [42.6270, 41.7380], [43.0015, 41.0234]],
  tkuarchal: [[43.0015, 41.0234], [42.7120, 41.4680], [42.8510, 41.6820], [42.8780, 41.7550], [42.7120, 41.4680], [43.0015, 41.0234]]
};

function getCoordsForTitle(title) {
  const t = (title || '').toLowerCase();
  if (t.includes('ингур') || t.includes('гал') || t.includes('очамчыр')) return ROUTE_COORDS_PRESETS.ingur;
  if (t.includes('мюссер') || t.includes('лыхн') || t.includes('форел')) return ROUTE_COORDS_PRESETS.mussera;
  if (t.includes('риц')) return ROUTE_COORDS_PRESETS.ritsa;
  if (t.includes('пицунд')) return ROUTE_COORDS_PRESETS.pitsunda;
  if (t.includes('ткуарчал') || t.includes('акармар')) return ROUTE_COORDS_PRESETS.tkuarchal;
  if (t.includes('транзит')) return ROUTE_COORDS_PRESETS.transit;
  if (t.includes('сухум') || t.includes('афон')) return ROUTE_COORDS_PRESETS.sukhum;
  return ROUTE_COORDS_PRESETS.gagra;
}

function downloadRouteGpx(filename, title, coords) {
  const pts = (coords || ROUTE_COORDS_PRESETS.gagra)
    .map(c => `      <trkpt lat="${c[0]}" lon="${c[1]}"></trkpt>`)
    .join('\n');
  const gpxXml = `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Abhaz Band Hub" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>${(title || 'Abhaz Band Route').replace(/[<>&]/g, '')}</name>
    <trkseg>
${pts}
    </trkseg>
  </trk>
</gpx>`;
  const blob = new Blob([gpxXml], { type: 'application/gpx+xml' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = (filename || 'abhazband_route') + '.gpx';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function initTrackMap(mapId, coords) {
  if (typeof L === 'undefined') return;
  const el = document.getElementById(mapId);
  if (!el) return;
  if (activeLeafletMaps[mapId]) {
    try { activeLeafletMaps[mapId].remove(); } catch (e) {}
  }
  const pts = coords && coords.length > 1 ? coords : ROUTE_COORDS_PRESETS.gagra;
  const map = L.map(mapId, { zoomControl: false, attributionControl: false, dragging: true, scrollWheelZoom: false });
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 16 }).addTo(map);
  const poly = L.polyline(pts, { color: '#38bdf8', weight: 3.5, opacity: 0.95 }).addTo(map);
  L.circleMarker(pts[0], { radius: 5, color: '#10b981', fillColor: '#10b981', fillOpacity: 1 }).addTo(map);
  L.circleMarker(pts[pts.length - 1], { radius: 5, color: '#ef4444', fillColor: '#ef4444', fillOpacity: 1 }).addTo(map);
  map.fitBounds(poly.getBounds(), { padding: [18, 18] });
  activeLeafletMaps[mapId] = map;
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

    // Для администратора добавляем быстрый предпросмотр всех 3 уровней доступа
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

    // Резервный вход по клубному PIN-коду
    const savedPin = localStorage.getItem('abhaz_camp_pin');
    if (savedPin === CAMP_SECRET_PIN) {
      userConfirmedSlots = [{ slot_id: 'camp_ny_2027', slot_type: 'camp', slot_title: 'Abhaz Band. Октябрь 2026' }];
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
    userConfirmedSlots = [{ slot_id: 'camp_ny_2027', slot_type: 'camp', slot_title: 'Abhaz Band. Октябрь 2026' }];
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
    if (pill) { pill.innerText = '🔥 Полный кэмп Abhaz Band'; pill.style.background = '#38bdf8'; pill.style.color = '#0f172a'; }
    if (titleEl) titleEl.innerText = matchedCamp ? matchedCamp.title : (activeUserSlot.slot_title || 'Новогодний кэмп Abhaz Band 2027');
    if (datesEl) datesEl.innerText = matchedCamp ? `📅 ${matchedCamp.dates} | ${matchedCamp.location}` : '📅 Гагра / Сухум, Абхазия';
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
  renderTracksList();
}

function renderRideSlotDashboard(container, slot) {
  const matchedRide = (typeof rides !== 'undefined') ? rides.find(r => r.id === slot.slot_id) : null;
  const title = matchedRide ? matchedRide.title : (slot.slot_title || 'Выезд Abhaz Band');
  const coords = getCoordsForTitle(title);
  const mapId = 'slot-track-map-' + slot.slot_id.replace(/[^a-zA-Z0-9]/g, '_');
  const komootUrl = matchedRide?.komootUrl || 'https://www.komoot.com/tour/2163164931';

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
      <div style="font-size:11px; color:#38bdf8; font-weight:bold; margin-bottom:4px;">🗺️ ИНТЕРАКТИВНЫЙ ТРЕК МАРШРУТА</div>
      <h4 style="margin:0 0 6px 0; color:#fff; font-size:14px;">${title}</h4>
      <div id="${mapId}" class="track-map-box"></div>
      <div class="track-actions-row">
        <a href="${komootUrl}" target="_blank" class="btn-track-komoot">🗺️ Открыть в Komoot</a>
        <button class="btn-track-gpx" id="dl-gpx-${mapId}">⬇️ Скачать GPX</button>
      </div>
    </div>
    ${timingHtml}
  `;

  setTimeout(() => {
    initTrackMap(mapId, coords);
    const dlBtn = document.getElementById('dl-gpx-' + mapId);
    if (dlBtn) {
      dlBtn.onclick = () => downloadRouteGpx(slot.slot_id, title, coords);
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
      stats: "📍 База Abhaz Band",
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

  const mapsToInit = [];
  html += schedule.map((item, idx) => {
    const mapId = `camp-day-map-${idx}`;
    const hasRoute = item.km > 0;
    const coords = hasRoute ? getCoordsForTitle(item.title) : null;
    if (hasRoute) mapsToInit.push({ mapId, coords, title: item.title });

    return `
      <div class="card" style="border-left: 4px solid ${hasRoute ? '#38bdf8' : '#64748b'}; margin-bottom: 12px; background:#1e293b; padding:12px; border-radius:10px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
          <div style="font-size:10px; color:#38bdf8; font-weight:bold;">${item.day}</div>
          <span style="font-size:9px; background:rgba(255,255,255,0.1); color:#fff; padding:2px 6px; border-radius:4px; font-weight:bold;">${item.type}</span>
        </div>
        <h4 style="margin:2px 0 6px 0; color:#fff; font-size:14px;">${item.title}</h4>
        <p style="font-size:11px; color:#94a3b8; margin:0 0 8px 0; line-height: 1.4;">${item.desc}</p>
        <div style="font-size:11px; color:#cbd5e1; margin-bottom:8px;">${item.stats}</div>
        ${hasRoute ? `<div id="${mapId}" class="track-map-box"></div>` : ''}
        ${item.links ? `
          <div class="track-actions-row">
            ${item.links.map(l => `
              <a href="${l.url}" target="_blank" class="btn-track-komoot">${l.label}</a>
            `).join('')}
            ${hasRoute ? `<button class="btn-track-gpx" id="dl-gpx-${mapId}">⬇️ Скачать GPX</button>` : ''}
          </div>
        ` : ''}
      </div>
    `;
  }).join('');

  container.innerHTML = html;

  setTimeout(() => {
    mapsToInit.forEach(m => {
      initTrackMap(m.mapId, m.coords);
      const btn = document.getElementById('dl-gpx-' + m.mapId);
      if (btn) btn.onclick = () => downloadRouteGpx(m.mapId, m.title, m.coords);
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