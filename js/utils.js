// Переключение основных вкладок
function switchTab(tabId, element) {
  try {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-item').forEach(item => item.classList.remove('active'));
    const targetTab = document.getElementById(tabId);
    if (targetTab) targetTab.classList.add('active');
    if (element) element.classList.add('active');
  } catch (e) {
    console.error("Ошибка переключения вкладки:", e);
  }
}

// Переключение под-вкладок кабинета участника
function switchSubTab(tabId, btnEl) {
  document.querySelectorAll('.sub-tab-content').forEach(el => el.style.display = 'none');
  document.querySelectorAll('.sub-tab-btn').forEach(btn => btn.classList.remove('active'));

  const target = document.getElementById(tabId);
  if (target) target.style.display = 'block';
  if (btnEl) btnEl.classList.add('active');
}

// Переключение под-вкладок магазина
function switchShopSubTab(tabId, btnEl) {
  document.querySelectorAll('.shop-sub-content').forEach(el => el.style.display = 'none');
  document.querySelectorAll('#shop-tab .sub-tab-btn').forEach(btn => btn.classList.remove('active'));

  const target = document.getElementById(tabId);
  if (target) target.style.display = 'block';
  if (btnEl) btnEl.classList.add('active');
}

// Безопасное открытие Telegram-ссылок
function openBotLink(username) {
  const url = `https://t.me/${username}`;
  if (window.Telegram?.WebApp?.openTelegramLink) {
    window.Telegram.WebApp.openTelegramLink(url);
  } else {
    window.open(url, '_blank');
  }
}

function openLifeRideBot() {
  openBotLink('liferidelife_bot');
}

function openFititi() {
  if (window.Telegram?.WebApp?.openLink) {
    window.Telegram.WebApp.openLink('https://fititi.ru/');
  } else {
    window.open('https://fititi.ru/', '_blank');
  }
}

// Шеринг заезда
function shareRide(title, date) {
  const botAppUrl = 'https://t.me/abhazband_bot';
  const text = `🚴 Поедешь со мной на заезд?\n\n"${title}"\n📅 ${date}`;
  const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(botAppUrl)}&text=${encodeURIComponent(text)}`;
  
  if (window.Telegram?.WebApp?.openTelegramLink) {
    window.Telegram.WebApp.openTelegramLink(shareUrl);
  } else {
    window.open(shareUrl, '_blank');
  }
}

// Шеринг товара Велоуют
function shareProduct(title, price) {
  const botAppUrl = 'https://t.me/abhazband_bot';
  const text = `🔥 Смотри, классная вещь для велоуюта: ${title} (${price.toLocaleString()} ₽)`;
  const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(botAppUrl)}&text=${encodeURIComponent(text)}`;
  
  if (window.Telegram?.WebApp?.openTelegramLink) {
    window.Telegram.WebApp.openTelegramLink(shareUrl);
  } else {
    window.open(shareUrl, '_blank');
  }
}

// Калькулятор давления в шинах
function calcPressure() {
  const weightRange = document.getElementById('weight-range');
  const systemType = document.getElementById('system-type');
  const tyreProfile = document.getElementById('tyre-profile');

  if (!weightRange || !systemType || !tyreProfile) return;

  const weight = parseInt(weightRange.value);
  const system = systemType.value;
  const profile = tyreProfile.value;

  const weightVal = document.getElementById('weight-val');
  if (weightVal) weightVal.innerText = weight + ' кг';

  let baseBar = 3.0;

  switch(profile) {
    case 'road_25': baseBar = 6.2; break;
    case 'road_28': baseBar = 5.5; break;
    case 'road_30': baseBar = 4.8; break;
    case 'road_32': baseBar = 4.5; break;
    case 'g700_35': baseBar = 3.2; break;
    case 'g700_40': baseBar = 2.8; break;
    case 'g700_45': baseBar = 2.4; break;
    case 'g700_48': baseBar = 2.3; break;
    case 'g700_50': baseBar = 2.2; break;
    case 'g650_19': baseBar = 2.4; break;
    case 'g650_21': baseBar = 2.1; break;
    case 'g650_23': baseBar = 1.9; break;
  }

  let weightFactor = weight / 75;
  let tubelessBonus = (system === 'tubeless') ? -0.35 : 0.0;

  let frontBar = Math.max(1.2, (baseBar * weightFactor * 0.86) + tubelessBonus);
  let rearBar = Math.max(1.4, (baseBar * weightFactor * 1.14) + tubelessBonus);

  frontBar = frontBar.toFixed(1);
  rearBar = rearBar.toFixed(1);

  let frontPsi = Math.round(frontBar * 14.5038);
  let rearPsi = Math.round(rearBar * 14.5038);

  const frontRes = document.getElementById('front-res');
  const rearRes = document.getElementById('rear-res');
  if (frontRes) frontRes.innerText = `${frontBar} Bar (${frontPsi} PSI)`;
  if (rearRes) rearRes.innerText = `${rearBar} Bar (${rearPsi} PSI)`;
}
