let supabaseClient = null;
try {
  if (window.supabase && typeof window.supabase.createClient === 'function') {
    supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }
} catch (e) {
  console.warn("Supabase init bypassed:", e);
}

// Проверка и инициализация статуса тумблера
async function initSubscriptionToggle() {
  const toggle = document.getElementById('sub-toggle');
  if (!toggle) return;

  if (!tgUser?.id || !supabaseClient) {
    toggle.checked = true;
    return;
  }

  try {
    const { data } = await supabaseClient
      .from('subscribers')
      .select('is_subscribed')
      .eq('user_id', tgUser.id)
      .maybeSingle();

    if (data !== null && data.is_subscribed !== undefined) {
      toggle.checked = data.is_subscribed;
    } else {
      toggle.checked = true;
      await supabaseClient
        .from('subscribers')
        .upsert({
          user_id: tgUser.id,
          username: tgUser.username || '',
          first_name: tgUser.first_name || '',
          is_subscribed: true,
          updated_at: new Date().toISOString()
        });
    }
  } catch (err) {
    console.error('Ошибка подписки при входе:', err);
    toggle.checked = true;
  }
}

// Изменение статуса подписки
async function toggleSubscription(isSubscribed) {
  if (!tgUser?.id) {
    if (tg?.showAlert) {
      tg.showAlert("Для управления подпиской откройте приложение через Telegram.");
    }
    return;
  }

  if (!supabaseClient) return;

  try {
    const { error } = await supabaseClient
      .from('subscribers')
      .upsert({
        user_id: tgUser.id,
        username: tgUser.username || '',
        first_name: tgUser.first_name || '',
        is_subscribed: isSubscribed,
        updated_at: new Date().toISOString()
      });

    if (error) {
      console.error('Ошибка сохранения подписки:', error);
    } else {
      tg?.HapticFeedback?.impactOccurred('light');
    }
  } catch (err) {
    console.error('Ошибка отправки подписки в Supabase:', err);
  }
}

// Проверка прав администратора
function checkAdmin() {
  if (tgUser && Number(tgUser.id) === BROADCAST_ADMIN_ID) {
    const panel = document.getElementById("admin-panel");
    if (panel) panel.style.display = "block";
  }
}

// Рассылка сообщений
async function startBroadcast() {
  const imageUrl = document.getElementById("broadcast-image").value.trim();
  const text = document.getElementById("broadcast-text").value.trim();
  const btnText = document.getElementById("broadcast-btn-text").value.trim();
  const btnUrl = document.getElementById("broadcast-btn-url").value.trim();
  const statusDiv = document.getElementById("broadcast-status");
  const btn = document.getElementById("send-broadcast-btn");

  if (!text) {
    alert("Заполните текст сообщения!");
    return;
  }

  if (!confirm("Вы уверены, что хотите запустить рассылку по всем подписчикам?")) {
    return;
  }

  btn.disabled = true;
  btn.style.opacity = "0.5";
  statusDiv.innerHTML = "⏳ Загрузка подписчиков из Supabase...";

  try {
    if (!supabaseClient) throw new Error("Supabase не инициализирован");

    const { data: subscribers, error } = await supabaseClient
      .from('subscribers')
      .select('user_id')
      .eq('is_subscribed', true);

    if (error) throw error;

    if (!subscribers || subscribers.length === 0) {
      statusDiv.innerHTML = "❌ В базе нет активных подписчиков.";
      btn.disabled = false;
      btn.style.opacity = "1";
      return;
    }

    let replyMarkup = null;
    if (btnText && btnUrl) {
      replyMarkup = { inline_keyboard: [[{ text: btnText, url: btnUrl }]] };
    }

    let sent = 0;
    let blocked = 0;
    let errors = 0;

    for (let i = 0; i < subscribers.length; i++) {
      const userId = subscribers[i].user_id;
      statusDiv.innerHTML = `🚀 Отправка: ${i + 1} из ${subscribers.length}...`;

      const method = imageUrl ? 'sendPhoto' : 'sendMessage';
      const payload = {
        chat_id: userId,
        parse_mode: 'HTML',
        reply_markup: replyMarkup
      };

      if (imageUrl) {
        payload.photo = imageUrl;
        payload.caption = text;
      } else {
        payload.text = text;
      }

      try {
        const res = await fetch(`https://api.telegram.org/bot${BROADCAST_BOT_TOKEN}/${method}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const result = await res.json();

        if (result.ok) {
          sent++;
        } else {
          if (result.description && result.description.toLowerCase().includes("blocked")) {
            blocked++;
            await supabaseClient
              .from('subscribers')
              .update({ is_subscribed: false })
              .eq('user_id', userId);
          } else {
            errors++;
          }
        }
      } catch (err) {
        errors++;
      }

      await new Promise(r => setTimeout(r, 50));
    }

    statusDiv.innerHTML = `
      <div style="color: #30d158; font-weight: 600; margin-bottom: 4px;">✅ Рассылка завершена!</div>
      • Успешно доставлено: <b>${sent}</b><br>
      • Заблокировали бота (отписаны): <b>${blocked}</b><br>
      • Ошибки: <b>${errors}</b>
    `;

  } catch (err) {
    statusDiv.innerHTML = `❌ Ошибка: ${err.message || err}`;
  } finally {
    btn.disabled = false;
    btn.style.opacity = "1";
  }
}
