// --- ИНИЦИАЛИЗАЦИЯ TELEGRAM WEBAPP ---
const tg = window.Telegram?.WebApp;
if (tg) {
  try {
    tg.ready();
    tg.expand();
  } catch (e) {
    console.warn("Telegram WebApp init error:", e);
  }
}
const tgUser = tg?.initDataUnsafe?.user;

// --- КОНФИГУРАЦИЯ SUPABASE ---
const SUPABASE_URL = "https://eotbacbevzxckhyodgak.supabase.co"; 
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVvdGJhY2Jldnp4Y2toeW9kZ2FrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc0MDc2OTAsImV4cCI6MjEwMjk4MzY5MH0.v0lKQkwB7YXOD52TFH-V9a5BKm67M52QBImzdsG_cec"; 

// --- ПАРАМЕТРЫ АДМИНИСТРАТОРА И РАССЫЛКИ ---
const BROADCAST_BOT_TOKEN = '6800059891:AAHyovskefzHoCQ7Ad2H8T9diJm89Bfu4IU';
const BROADCAST_ADMIN_ID = 303365656;

// --- КОД ДОСТУПА В ЗАКРЫТЫЙ КЭМП ---
const CAMP_SECRET_PIN = "ABHAZ2026";
