import html
import json


def build_hub_widget_html(
    initial_tab: str = "overview",
    user_name: str = "Райдер",
    miniapp_url: str = "https://jora71441-design.github.io/abhazband-app/",
) -> str:
    """
    Автономный HTML/CSS/JS виджет Bot API 10.4 (QuickJS, ~9 КБ, без сетевых запросов).
    Три вкладки: «Обзор» (стартовый экран выбора), «Заезды» и «Кэмпы».
    """
    safe_tab = initial_tab if initial_tab in ("overview", "rides", "camps") else "overview"
    safe_user = html.escape(user_name[:24])
    base_url = miniapp_url.rstrip("/")

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
  body {{ background: #0f172a; color: #f8fafc; padding: 12px; font-size: 13px; }}
  .hdr {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
  .brand {{ font-weight: 800; font-size: 14px; letter-spacing: 0.3px; color: #f8fafc; }}
  .brand span {{ color: #10b981; }}
  .tag {{ font-size: 10px; background: #1e293b; color: #94a3b8; padding: 3px 7px; border-radius: 99px; border: 1px solid #334155; }}
  .tabs {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; background: #1e293b; padding: 4px; border-radius: 10px; margin-bottom: 11px; }}
  .tab {{ border: none; background: transparent; color: #94a3b8; padding: 7px 4px; border-radius: 7px; font-size: 11px; font-weight: 700; cursor: pointer; transition: 0.15s; }}
  .tab.active {{ background: #334155; color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }}
  .panel {{ display: none; }}
  .panel.active {{ display: block; }}

  /* Стартовый экран Обзор */
  .intro {{ background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.28); border-radius: 10px; padding: 9px 10px; font-size: 11.5px; line-height: 1.38; color: #cbd5e1; margin-bottom: 9px; }}
  .nav-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 11px; margin-bottom: 8px; cursor: pointer; transition: 0.15s; }}
  .nav-card:active {{ transform: scale(0.99); border-color: #10b981; }}
  .nc-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }}
  .nc-title {{ font-size: 13.5px; font-weight: 800; color: #f8fafc; }}
  .nc-cta {{ font-size: 11px; font-weight: 700; color: #10b981; background: rgba(16,185,129,0.14); padding: 3px 8px; border-radius: 6px; }}
  .nc-desc {{ font-size: 11px; color: #94a3b8; line-height: 1.35; }}
  .ov-foot {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 9px; }}

  /* Вкладки Заезды и Кэмпы */
  .pills {{ display: flex; gap: 5px; overflow-x: auto; margin-bottom: 9px; padding-bottom: 2px; }}
  .pill {{ border: 1px solid #334155; background: #1e293b; color: #cbd5e1; padding: 5px 9px; border-radius: 8px; font-size: 11px; font-weight: 600; white-space: nowrap; cursor: pointer; }}
  .pill.active-w {{ background: rgba(239,68,68,0.18); border-color: #ef4444; color: #fca5a5; }}
  .pill.active-s {{ background: rgba(16,185,129,0.18); border-color: #10b981; color: #6ee7b7; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 11px; }}
  .badge {{ display: inline-block; font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 6px; margin-bottom: 5px; }}
  .b-w {{ background: rgba(239,68,68,0.18); color: #fca5a5; border: 1px solid #ef4444; }}
  .b-s {{ background: rgba(16,185,129,0.18); color: #6ee7b7; border: 1px solid #10b981; }}
  .title {{ font-size: 14px; font-weight: 800; margin-bottom: 3px; line-height: 1.25; }}
  .sub {{ font-size: 11px; color: #94a3b8; margin-bottom: 9px; line-height: 1.35; }}
  .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 10px; }}
  .stat {{ background: #0f172a; border-radius: 8px; padding: 6px 8px; }}
  .stat-l {{ font-size: 10px; color: #64748b; display: block; }}
  .stat-v {{ font-size: 12px; font-weight: 700; color: #e2e8f0; }}
  .actions {{ display: flex; flex-direction: column; gap: 6px; }}
  .btn {{ width: 100%; border: none; border-radius: 9px; padding: 10px; font-size: 12px; font-weight: 700; cursor: pointer; background: #10b981; color: #052e16; text-align: center; text-decoration: none; display: block; }}
  .btn:active {{ opacity: 0.85; }}
  .btn.booked {{ background: #334155; color: #6ee7b7; }}
  .btn-sec {{ background: #0f172a; color: #e2e8f0; border: 1px solid #334155; font-weight: 600; padding: 8px; font-size: 11.5px; }}
</style>
</head>
<body>
  <div class="hdr">
    <div class="brand">ABHAZ<span>BAND</span> • ПУЛЬТ</div>
    <div class="tag">@{safe_user}</div>
  </div>

  <div class="tabs">
    <button class="tab" id="t-overview" onclick="setTab('overview')">🏠 Обзор</button>
    <button class="tab" id="t-rides" onclick="setTab('rides')">📅 Заезды</button>
    <button class="tab" id="t-camps" onclick="setTab('camps')">⛺ Кэмпы</button>
  </div>

  <!-- ВКЛАДКА 0: СТАРТОВЫЙ ОБЗОР -->
  <div class="panel" id="p-overview">
    <div class="intro">
      <b>Велоклуб AbhazBand (Гагра, Абхазия)</b> — шоссейные и гравел-сборы, а также выезды выходного дня от КПП Псоу с машиной сопровождения.
    </div>

    <div class="nav-card" onclick="setTab('rides')">
      <div class="nc-top">
        <div class="nc-title">📅 Заезды (Уикенды и Social Rides)</div>
        <div class="nc-cta">Выбрать →</div>
      </div>
      <div class="nc-desc">Ближайший старт: <b>14–15 Ноября</b> • Гагра — Сухум (195 км). Выезды на 1–2 дня с техничкой и кофе-стопами.</div>
    </div>

    <div class="nav-card" onclick="setTab('camps')">
      <div class="nc-top">
        <div class="nc-title">⛺ Велокэмпы в Абхазии</div>
        <div class="nc-cta">Смотреть →</div>
      </div>
      <div class="nc-desc">Актуальные сборы: <b>Ноябрь • Декабрь • Новый год 2027</b>. Проживание, радиалки на Рицу и Мамдзышху.</div>
    </div>

    <div class="ov-foot">
      <a class="btn btn-sec" href="{base_url}/" onclick="openAppTab('overview')">🚀 Открыть Хаб</a>
      <a class="btn btn-sec" href="https://t.me/Piti4">💬 Вопрос @Piti4</a>
    </div>
  </div>

  <!-- ВКЛАДКА 1: ЗАЕЗДЫ -->
  <div class="panel" id="p-rides">
    <div class="pills" id="ride-pills"></div>
    <div class="card">
      <span class="badge" id="r-badge"></span>
      <div class="title" id="r-title"></div>
      <div class="sub" id="r-sub"></div>
      <div class="grid2">
        <div class="stat"><span class="stat-l">🛣️ Дистанция</span><span class="stat-v" id="r-dist"></span></div>
        <div class="stat"><span class="stat-l">⛰️ Набор</span><span class="stat-v" id="r-elev"></span></div>
        <div class="stat"><span class="stat-l">⚡ Темп</span><span class="stat-v" id="r-pace"></span></div>
        <div class="stat"><span class="stat-l">⏰ Старт</span><span class="stat-v" id="r-time"></span></div>
      </div>
      <div class="actions">
        <button class="btn" id="r-book-btn" onclick="bookItem('ride')">🚴 Занять слот на этот выезд</button>
        <a class="btn btn-sec" href="{base_url}/?tab=rides" onclick="openAppTab('rides')">📅 Весь календарь и GPX →</a>
      </div>
    </div>
  </div>

  <!-- ВКЛАДКА 2: КЭМПЫ -->
  <div class="panel" id="p-camps">
    <div class="pills" id="camp-pills"></div>
    <div class="card">
      <span class="badge b-s" id="c-badge"></span>
      <div class="title" id="c-title"></div>
      <div class="sub" id="c-sub"></div>
      <div class="grid2">
        <div class="stat"><span class="stat-l">📆 Даты</span><span class="stat-v" id="c-dates"></span></div>
        <div class="stat"><span class="stat-l">📍 Локация</span><span class="stat-v" id="c-loc"></span></div>
        <div class="stat"><span class="stat-l">🚲 Формат</span><span class="stat-v" id="c-type"></span></div>
        <div class="stat"><span class="stat-l">🚗 Сопровождение</span><span class="stat-v" id="c-sup"></span></div>
      </div>
      <div class="actions">
        <button class="btn" id="c-book-btn" onclick="bookItem('camp')">⛺ Забронировать место в кэмпе</button>
        <a class="btn btn-sec" href="{base_url}/?tab=camps" onclick="openAppTab('camps')">📖 Полная программа и маршруты →</a>
      </div>
    </div>
  </div>

<script>
  const RIDES = [
    {{ id: "w_nov14", pill: "14–15 Ноя", kind: "w", badge: "WEEKEND CAMP • 2 ДНЯ", title: "Гагра — Ачандара — Сухум", sub: "База с бассейном в Сухуме, машина сопровождения и фотосет", dist: "195 км", elev: "+1 950 м", pace: "27–30 км/ч", time: "09:00 КПП Псоу" }},
    {{ id: "s_nov21", pill: "21 Ноя", kind: "s", badge: "SOCIAL RIDE • 1 ДЕНЬ", title: "Псоу — Пицунда — Ацгуара", sub: "Комфортный раскат по сосновым аллеям, кофе-стоп и техничка", dist: "85 км", elev: "+350 м", pace: "25–28 км/ч", time: "09:00 КПП Псоу" }},
    {{ id: "w_nov28", pill: "28–29 Ноя", kind: "w", badge: "WEEKEND CAMP • 2 ДНЯ", title: "Восточный эпик: ИнгурГЭС", sub: "Сухум — Очамчыра — Гал — дамба ИнгурГЭС, встреча вечерней Ласточки", dist: "220 км", elev: "+1 450 м", pace: "27–30 км/ч", time: "Сухум / Ласточка" }},
    {{ id: "s_dec05", pill: "5 Дек", kind: "s", badge: "SOCIAL RIDE • 1 ДЕНЬ", title: "Мюссера и Форелевое хозяйство", sub: "Живописные холмы Мюссеры + обед со свежей форелью у горной реки", dist: "95 км", elev: "+850 м", pace: "25–28 км/ч", time: "09:00 КПП Псоу" }}
  ];

  const CAMPS = [
    {{ id: "camp_nov", pill: "Ноябрь", badge: "КЛУБНЫЕ ЗАЕЗДЫ", title: "Ноябрьский кэмп в Гагре", sub: "Гибкий заезд на 4–10 дней: радиалки на Рицу, Мамдзышху и побережье", dates: "5 – 30 Ноября", loc: "Гагра, Абхазия", type: "Шоссе / Гравел", sup: "Техничка + гид" }},
    {{ id: "camp_dec", pill: "Декабрь", badge: "ЗИМНЯЯ ВКАТКА", title: "Декабрьская подготовка", sub: "Тёплый прибрежный объём без снега и гололёда + субботние Social Rides", dates: "1 – 30 Декабря", loc: "Гагра, Абхазия", type: "Шоссе", sup: "Техничка + фото" }},
    {{ id: "camp_ny", pill: "Новый год", badge: "ПРАЗДНИЧНЫЙ КЭМП", title: "Новогодний велокэмп 2027", sub: "Праздничные старты по пустым дорогам Абхазии, мандарины и горные перевалы", dates: "1 – 10 Января", loc: "Гагра, Абхазия", type: "Шоссе / Гравел", sup: "Полный пакет" }}
  ];

  let rideIdx = 0;
  let campIdx = 0;
  let booked = {{}};

  function sendBridge(payloadObj) {{
    const raw = JSON.stringify(payloadObj);
    if (window.TelegramWidget && typeof window.TelegramWidget.sendQuery === "function") {{
      window.TelegramWidget.sendQuery(raw);
    }} else if (window.Telegram && window.Telegram.WebApp && typeof window.Telegram.WebApp.sendData === "function") {{
      window.Telegram.WebApp.sendData(raw);
    }}
  }}

  function setTab(t) {{
    ["overview", "rides", "camps"].forEach(id => {{
      document.getElementById("t-" + id).classList.toggle("active", id === t);
      document.getElementById("p-" + id).classList.toggle("active", id === t);
    }});
  }}

  function renderRides() {{
    document.getElementById("ride-pills").innerHTML = RIDES.map((r, i) => {{
      const cls = i === rideIdx ? (r.kind === "w" ? "pill active-w" : "pill active-s") : "pill";
      return `<button class="${{cls}}" onclick="pickRide(${{i}})">${{r.kind === 'w' ? '🔴' : '🟢'}} ${{r.pill}}</button>`;
    }}).join("");

    const r = RIDES[rideIdx];
    const badge = document.getElementById("r-badge");
    badge.textContent = r.badge;
    badge.className = "badge " + (r.kind === "w" ? "b-w" : "b-s");
    document.getElementById("r-title").textContent = r.title;
    document.getElementById("r-sub").textContent = r.sub;
    document.getElementById("r-dist").textContent = r.dist;
    document.getElementById("r-elev").textContent = r.elev;
    document.getElementById("r-pace").textContent = r.pace;
    document.getElementById("r-time").textContent = r.time;

    const btn = document.getElementById("r-book-btn");
    if (booked[r.id]) {{
      btn.textContent = "✅ Заявка отправлена (@Piti4 свяжется)";
      btn.className = "btn booked";
    }} else {{
      btn.textContent = "🚴 Занять слот на этот выезд";
      btn.className = "btn";
    }}
  }}

  function renderCamps() {{
    document.getElementById("camp-pills").innerHTML = CAMPS.map((c, i) => {{
      const cls = i === campIdx ? "pill active-s" : "pill";
      return `<button class="${{cls}}" onclick="pickCamp(${{i}})">⛺ ${{c.pill}}</button>`;
    }}).join("");

    const c = CAMPS[campIdx];
    document.getElementById("c-badge").textContent = c.badge;
    document.getElementById("c-title").textContent = c.title;
    document.getElementById("c-sub").textContent = c.sub;
    document.getElementById("c-dates").textContent = c.dates;
    document.getElementById("c-loc").textContent = c.loc;
    document.getElementById("c-type").textContent = c.type;
    document.getElementById("c-sup").textContent = c.sup;

    const btn = document.getElementById("c-book-btn");
    if (booked[c.id]) {{
      btn.textContent = "✅ Заявка отправлена (@Piti4 свяжется)";
      btn.className = "btn booked";
    }} else {{
      btn.textContent = "⛺ Забронировать место в кэмпе";
      btn.className = "btn";
    }}
  }}

  function pickRide(i) {{ rideIdx = i; renderRides(); }}
  function pickCamp(i) {{ campIdx = i; renderCamps(); }}

  function bookItem(category) {{
    const item = category === "ride" ? RIDES[rideIdx] : CAMPS[campIdx];
    if (booked[item.id]) return;
    booked[item.id] = true;
    category === "ride" ? renderRides() : renderCamps();
    sendBridge({{
      action: "book_item",
      category: category,
      id: item.id,
      title: item.title,
      dates: category === "ride" ? item.pill : item.dates
    }});
  }}

  function openAppTab(tabName) {{
    sendBridge({{ action: "open_tab", tab: tabName }});
  }}

  setTab("{safe_tab}");
  renderRides();
  renderCamps();
</script>
</body>
</html>"""


def parse_widget_action(raw_data: str) -> dict:
    try:
        data = json.loads(raw_data or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}
