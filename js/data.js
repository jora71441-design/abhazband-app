// --- КЭМПЫ ---
const camps = [
  {
    id: "camp_oct_1_2026",
    title: "Комбинированный Шоссе vs Гравел",
    dates: "04 - 14 октября (11 дней)",
    location: "База AbhazBand (Гагра / Гал / Сухум)",
    price: "85 000 ₽ (80 000 ₽ для членов AbhazBand)",
    specs: "Пробег: ~800 км | Набор: ~7 000 м",
    description: "Комбинированный шоссейно-гравийный кэмп по западным и восточным маршрутам.",
    image: "./Okt_shos_gravel-compressed.jpeg",
    link: "https://t.me/Piti4"
  },
  {
    id: "camp_oct_2_2026",
    title: "Классический Шоссейный кэмп",
    dates: "24 октября - 03 ноября (11 дней)",
    location: "База AbhazBand (Гагра / Гал / Сухум)",
    price: "85 000 ₽ (80 000 ₽ для членов AbhazBand)",
    specs: "Пробег: ~800 км | Набор: ~7 000 м",
    description: "Классический шоссейный кэмп по западным и восточным маршрутам.",
    image: "./Okt_shosse-compressed.jpeg",
    link: "https://t.me/Piti4"
  },
  {
    id: "camp_nov_2026",
    title: "Клубные кэмпы",
    dates: "05 - 30 ноября",
    location: "Абхазия",
    price: "Уточняйте",
    specs: "",
    description: "Сезонные клубные заезды и тренировочные сборы.",
    image: "./Klubnie-compressed.jpeg",
    link: "https://t.me/Piti4"
  },
  {
    id: "camp_dec_2026",
    title: "Подготовка к Abhaz Band New Year",
    dates: "1 - 31 декабря",
    location: "Абхазия",
    price: "Уточняйте",
    specs: "",
    description: "Самостоятельные шоссейные приезды и локальные СошлРайды",
    image: "./Noviy_god-compressed.jpeg",
    link: "https://t.me/Piti4"
  }
];

// --- SOCIAL RIDES ---
const rides = [
  {
    title: "Субботний кофе-райд: Гагра — Пицунда",
    date: "Каждая суббота | Сбор: 09:00",
    startPoint: "📍 Гагра, Кофейня на набережной",
    stats: "🚴 55 км | ↗️ 320 м | ⏱️ 23-25 км/ч",
    type: "Шоссе / Гравел",
    desc: "Традиционный расслабленный заезд с остановкой на кофе в Пицунде. Подходит для любого уровня подготовки.",
    gpxUrl: "https://t.me/Piti4",
    chatUrl: "https://t.me/Piti4"
  }
];

// --- МЕДИА-КАНАЛЫ ---
const mediaChannels = [
  {
    name: "Abhaz Band Photo",
    tag: "ОФИЦИАЛЬНЫЙ АРХИВ",
    desc: "Самые сочные кадры с горных серпантинов, кэмпов и субботних кофе-райдов.",
    image: "./Okt_shos_gravel-compressed.jpeg",
    link: "https://disk.yandex.ru/d/OIfy3OpN-5yYMg"
  }
];

// --- ЧЕК-ЛИСТ УЧАСТНИКА КЭМПА ---
const CAMP_CHECKLIST_DATA = [
  {
    category: "🚲 Велосипед & Запчасти",
    items: [
      { id: "c_mech", label: "Запасной петух (если есть)" },
      { id: "c_pads", label: "Колодки запасные" },
      { id: "c_lube", label: "Смазка цепи" },
      { id: "c_tubes", label: "Запасные камеры (2 шт)" },
      { id: "c_lights", label: "Задний и передний фонарь" },
      { id: "c_pump", label: "Компактный насос или CO2 баллоны" },
      { id: "c_tool", label: "Мультитул" }
    ]
  },
  {
    category: "👕 Экипировка & Гаджеты",
    items: [
      { id: "c_wind", label: "Ветровка/Жилетка/Рукава/Гамаши " },
      { id: "c_bibs", label: "Велоформа (2 комплекта)" },
      { id: "c_rain", label: "Дождевик/бахилы " },
      { id: "c_shoes", label: "Велотуфли + Запасные шипы" },
      { id: "c_glasses", label: "Велоочки (в идеале фотохром)" },
      { id: "c_hr", label: "Пульсометр (проверить батарейку)" },
      { id: "c_computer", label: "Велокомп (зарядка к компу)" }
    ]
  },
  {
    category: "💊 Личное, Документы & Питание",
    items: [
      { id: "c_passport", label: "Паспорт РФ (для границы)" },
      { id: "c_hygiene", label: "Средства личной гигиены" },
      { id: "c_phone_charger", label: "Зарядка мобильного" },
      { id: "c_pbank", label: "Пауэрбанк и кабели для зарядки гаджетов" },
      { id: "c_cash", label: "Наличные деньги" },
      { id: "c_nutrition", label: "Энергетические гели / изотоники" },
      { id: "c_suncream", label: "Крем от солнца & крем от натирания" }
    ]
  }
];

// --- КАТАЛОГ «ВЕЛОУЮТ» ---
const VELOUYUT_PRODUCTS_DATA = [
  { id: "v1", title: "Настенный держатель для велошлема и очков", colors: "Черный / Белый", price: 650, image: "./images/velouyut/V1.jpg" },
  { id: "v2", title: "Настенный держатель для велошлема Компактный", colors: "Черный / Белый", price: 950, image: "./images/velouyut/v2.png" },
  { id: "v3", title: "Настенный держатель для велошлема Универсальный", colors: "Черный / Белый", price: 950, image: "./images/velouyut/v3.png" },
  { id: "v4", title: "Органайзер для велоочков", colors: "Черный / Белый", price: 1500, image: "./images/velouyut/v4.png" },
  { id: "v5", title: "Настенный держатель для Велошлема Премиум", colors: "Черный / Белый", price: 2200, image: "./images/velouyut/v5.png" },
  { id: "v6", title: "Настенный держатель для Велоэкипировки МТВ", colors: "Черный / Белый", price: 2200, image: "./images/velouyut/v6.jpg" },
  { id: "v7", title: "Универсальный настенный держатель велоэкипировки", colors: "Черный / Белый", price: 2500, image: "./images/velouyut/v7.png" },
  { id: "v8", title: "Горизонтальная стойка для Велоэкипировки", colors: "Черный / Белый", price: 3000, image: "./images/velouyut/v8.png" },
  { id: "v9", title: "Вертикальная стойка для Велоэкипировки", colors: "Черный / Белый", price: 3000, image: "./images/velouyut/v9.png" },
  { id: "v10", title: "Настенное крепление для велосипедных колес", colors: "Черный / Белый", price: 1500, image: "./images/velouyut/v10.PNG" }
];

// Состояние развилок маршрутов
let campState = {
  restDay: 10,
  branch: 'gal',
  distSukhum: 90
};
