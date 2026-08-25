import os
import re
import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError, ChannelPrivateError, UsernameInvalidError

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# ==============================
# КОНСТАНТЫ
# ==============================

DB_PATH = 'data/database.sqlite'
CHECK_INTERVAL = 600          # Интервал проверки каналов (сек)
DELAY_BETWEEN_CHANNELS = 60    # Пауза между запросами к каналам (сек)
INACTIVITY_DAYS = 60          # Дней неактивности до удаления пользователя
MAX_CHANNELS_PER_USER = 10    # Максимум каналов на одного пользователя
MAX_CAPTION_LENGTH = 1024     # Максимальная длина подписи к медиа в Telegram
MAX_POSTS_PER_CHECK = 20      # Максимум новых постов за одну проверку канала
MAX_LOG_LINES = 30            # Сколько последних строк лога показывать

# ==============================
# ЛОГИРОВАНИЕ
# ==============================

os.makedirs('data', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('data/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==============================
# БАЗА ДАННЫХ
# ==============================

_conn = None

def get_db() -> sqlite3.Connection:
    # Возвращает единственное соединение с БД (singleton)
    global _conn
    if _conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn


def init_db():
    # Создаёт таблицы если их нет
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT 'ru',
            last_active TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_channels (
            user_id INTEGER,
            channel TEXT,
            PRIMARY KEY (user_id, channel)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS last_seen_ids (
            user_id INTEGER,
            channel TEXT,
            last_msg_id INTEGER,
            PRIMARY KEY (user_id, channel)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_messages (
            user_id INTEGER,
            msg_id INTEGER,
            PRIMARY KEY (user_id, msg_id)
        )
    ''')
    conn.commit()
    logger.info("База данных инициализирована.")


init_db()

# ==============================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ БД ДЛЯ СООБЩЕНИЙ
# ==============================

def save_msg_id(user_id: int, msg_id: int):
    # Сохраняет ID сообщения для последующего удаления
    if not msg_id:
        return
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO user_messages (user_id, msg_id) VALUES (?, ?)",
        (user_id, msg_id)
    )
    conn.commit()


def get_and_clear_user_messages(user_id: int) -> list:
    # Возвращает список ID сообщений пользователя и удаляет их из БД
    conn = get_db()
    rows = conn.execute(
        "SELECT msg_id FROM user_messages WHERE user_id = ?", (user_id,)
    ).fetchall()
    msg_ids = [row['msg_id'] for row in rows]

    conn.execute("DELETE FROM user_messages WHERE user_id = ?", (user_id,))
    conn.commit()
    return msg_ids

# ==============================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==============================

def normalize_channel_name(ch: str) -> str | None:
    ch = ch.strip().lower()
    ch = ch.replace('https://t.me/', '').replace('@', '').split('/')[0]

    if not re.match(r'^[a-z0-9_]{3,32}$', ch):
        return None
    return ch


def update_user_activity(user_id: int):
    # Обновляет время последней активности пользователя
    conn = get_db()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('''
        INSERT INTO users (user_id, last_active) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET last_active = ?
    ''', (user_id, now_str, now_str))
    conn.commit()


def get_user_lang(user_id: int) -> str:
    conn = get_db()
    res = conn.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return res['lang'] if res else 'ru'


def set_user_lang(user_id: int, lang: str):
    conn = get_db()
    conn.execute('''
        INSERT INTO users (user_id, lang) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET lang = ?
    ''', (user_id, lang, lang))
    conn.commit()


def get_user_channels(user_id: int) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT channel FROM user_channels WHERE user_id = ?", (user_id,)
    ).fetchall()
    return [row['channel'] for row in rows]


def add_user_channel(user_id: int, channel: str) -> bool:
    conn = get_db()
    if user_id != ADMIN_ID:
        count = conn.execute(
            "SELECT COUNT(*) as cnt FROM user_channels WHERE user_id = ?", (user_id,)
        ).fetchone()['cnt']

        if count >= MAX_CHANNELS_PER_USER:
            return False

    conn.execute(
        "INSERT OR IGNORE INTO user_channels (user_id, channel) VALUES (?, ?)",
        (user_id, channel)
    )
    conn.commit()
    return True


def delete_user_channel(user_id: int, channel: str):
    conn = get_db()
    conn.execute(
        "DELETE FROM user_channels WHERE user_id = ? AND channel = ?",
        (user_id, channel)
    )
    conn.execute(
        "DELETE FROM last_seen_ids WHERE user_id = ? AND channel = ?",
        (user_id, channel)
    )
    conn.commit()


def get_all_unique_channels() -> set:
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT channel FROM user_channels").fetchall()
    return {row['channel'] for row in rows}


def get_users_for_channel(channel: str) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT user_id FROM user_channels WHERE channel = ?", (channel,)
    ).fetchall()
    return [row['user_id'] for row in rows]


def get_last_seen_id(user_id: int, channel: str) -> int:
    conn = get_db()
    res = conn.execute(
        "SELECT last_msg_id FROM last_seen_ids WHERE user_id = ? AND channel = ?",
        (user_id, channel)
    ).fetchone()
    return res['last_msg_id'] if res else 0


def update_last_seen_id(user_id: int, channel: str, msg_id: int):
    conn = get_db()
    conn.execute('''
        INSERT INTO last_seen_ids (user_id, channel, last_msg_id)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, channel) DO UPDATE SET last_msg_id = ?
    ''', (user_id, channel, msg_id, msg_id))
    conn.commit()


def cleanup_inactive_users(days_limit: int):
    conn = get_db()
    cutoff_date = (datetime.now() - timedelta(days=days_limit)).strftime('%Y-%m-%d %H:%M:%S')
    inactive = conn.execute(
        "SELECT user_id FROM users WHERE last_active < ?", (cutoff_date,)
    ).fetchall()

    if inactive:
        inactive_ids = [row['user_id'] for row in inactive]
        logger.info(f"Очистка: удаляю {len(inactive_ids)} неактивных пользователей: {inactive_ids}")

        for u_id in inactive_ids:
            conn.execute("DELETE FROM users WHERE user_id = ?", (u_id,))
            conn.execute("DELETE FROM user_channels WHERE user_id = ?", (u_id,))
            conn.execute("DELETE FROM last_seen_ids WHERE user_id = ?", (u_id,))
            conn.execute("DELETE FROM user_messages WHERE user_id = ?", (u_id,))
        conn.commit()

# ==============================
# КЛИЕНТЫ TELETHON
# ==============================

user_client = TelegramClient('data/user_session', API_ID, API_HASH)
bot_client = TelegramClient('data/bot_session', API_ID, API_HASH)

# ==============================
# ЛОКАЛИЗАЦИЯ
# ==============================

TEXTS = {
    'ru': {
        'start_btn': "▶️ Старт",
        'list_btn': "📋 Мои каналы",
        'clear_btn': "🧹 Очистить чат",
        'lang_btn': "🌐 English",
        'welcome': (
            "👋 **Ваша приватная лента новостей**\n\n"
            "💡 Отправьте `@юзернейм` или ссылку на публичный канал, "
            "чтобы получать из него новости.\n\n"
            f"⚠️ Лимит ограничен полдпиской на {MAX_CHANNELS_PER_USER} каналов"
        ),
        'empty_list': "📭 Ваш список отслеживаемых каналов пуст.",
        'channel_list_title': "📋 **Ваши отслеживаемые каналы:**",
        'delete_btn': "❌ Удалить",
        'clearing': "⏳ Очищаю историю сообщений...",
        'cleared': "✨ Чат очищен! Клавиатура снова доступна.",
        'added_success': "✅ Канал `@{channel}` добавлен в ваш список!",
        'already_added': "ℹ️ Канал `@{channel}` уже есть в вашем списке.",
        'limit_reached': f"⚠️ Достигнут лимит каналов ({MAX_CHANNELS_PER_USER}). Удалите ненужные каналы.",
        'invalid_channel': "❌ Неверный формат канала. Отправьте `@юзернейм` или `https://t.me/username`.",
        'deleted_success': "🗑 Канал `@{channel}` удалён из вашего списка.",
        'not_found': "Канал не найден в вашем списке.",
        'lang_changed': "🌐 Язык изменён на русский!"
    },
    'en': {
        'start_btn': "▶️ Start",
        'list_btn': "📋 My Channels",
        'clear_btn': "🧹 Clear Chat",
        'lang_btn': "🌐 Русский",
        'welcome': (
            "👋 **Your Private News Feed**\n\n"
            "💡 Send `@username` or channel link to get updates.\n\n"
            f"⚠️ Subscription limit is {MAX_CHANNELS_PER_USER} channels"
        ),
        'empty_list': "📭 Your tracked channels list is empty.",
        'channel_list_title': "📋 **Your Tracked Channels:**",
        'delete_btn': "❌ Delete",
        'clearing': "⏳ Clearing message history...",
        'cleared': "✨ Chat cleared! Keyboard is ready.",
        'added_success': "✅ Channel `@{channel}` added to your list!",
        'already_added': "ℹ️ Channel `@{channel}` is already in your list.",
        'limit_reached': f"⚠️ Channel limit reached ({MAX_CHANNELS_PER_USER}). Please remove unused channels.",
        'invalid_channel': "❌ Invalid channel format. Send `@username` or `https://t.me/username`.",
        'deleted_success': "🗑 Channel `@{channel}` removed from your list.",
        'not_found': "Channel not found in your list.",
        'lang_changed': "🌐 Language changed to English!"
    }
}


def t(user_id: int, key: str) -> str:
    lang = get_user_lang(user_id)
    return TEXTS.get(lang, TEXTS['ru'])[key]


def get_keyboard(user_id: int):
    lang = get_user_lang(user_id)
    texts = TEXTS.get(lang, TEXTS['ru'])
    keyboard = [
        [Button.text(texts['start_btn'], resize=True), Button.text(texts['list_btn'])],
        [Button.text(texts['clear_btn']), Button.text(texts['lang_btn'])]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([Button.text("📜 Логи")])
    return keyboard

# ==============================
# ОБРАБОТЧИКИ КОМАНД
# ==============================

@bot_client.on(events.NewMessage(pattern=r'(/start|/menu|^▶️ Старт$|^▶️ Start$)'))
async def start_handler(event):
    user_id = event.sender_id
    save_msg_id(user_id, event.message.id)
    update_user_activity(user_id)

    res = await event.respond(t(user_id, 'welcome'), buttons=get_keyboard(user_id))
    save_msg_id(user_id, res.id)
    logger.info(f"Пользователь {user_id} открыл меню.")


@bot_client.on(events.NewMessage(pattern=r'^(🌐 English|🌐 Русский)$'))
async def switch_language_handler(event):
    user_id = event.sender_id
    save_msg_id(user_id, event.message.id)
    update_user_activity(user_id)

    current_lang = get_user_lang(user_id)
    new_lang = 'en' if current_lang == 'ru' else 'ru'
    set_user_lang(user_id, new_lang)

    res = await event.respond(TEXTS[new_lang]['lang_changed'], buttons=get_keyboard(user_id))
    save_msg_id(user_id, res.id)


@bot_client.on(events.NewMessage(pattern=r'^(📋 Мои каналы|📋 My Channels)$'))
async def list_channels_handler(event):
    user_id = event.sender_id
    save_msg_id(user_id, event.message.id)
    update_user_activity(user_id)

    channels = get_user_channels(user_id)

    if not channels:
        res = await event.respond(t(user_id, 'empty_list'), buttons=get_keyboard(user_id))
        save_msg_id(user_id, res.id)
        return

    lang = get_user_lang(user_id)
    texts = TEXTS.get(lang, TEXTS['ru'])

    inline_buttons = [
        [Button.inline(f"{texts['delete_btn']} @{ch}", data=f"del_{ch}")]
        for ch in channels
    ]
    channels_list = "\n".join([f"• @{ch}" for ch in channels])
    count_info = f"({len(channels)}/{MAX_CHANNELS_PER_USER if user_id != ADMIN_ID else '∞'})"

    res = await event.respond(
        f"{texts['channel_list_title']} {count_info}\n\n{channels_list}",
        buttons=inline_buttons
    )
    save_msg_id(user_id, res.id)


@bot_client.on(events.CallbackQuery(pattern=r'del_(.+)'))
async def inline_delete_handler(event):
    user_id = event.sender_id
    update_user_activity(user_id)
    channel = event.pattern_match.group(1).decode('utf-8')
    user_channels = get_user_channels(user_id)

    if channel in user_channels:
        delete_user_channel(user_id, channel)
        await event.answer(f"@{channel} deleted!")
        await event.edit(t(user_id, 'deleted_success').format(channel=channel))
        logger.info(f"Пользователь {user_id} удалил канал @{channel}.")
    else:
        await event.answer(t(user_id, 'not_found'))


@bot_client.on(events.NewMessage(pattern=r'^(🧹 Очистить чат|🧹 Clear Chat)$'))
async def clear_chat_handler(event):
    user_id = event.sender_id
    update_user_activity(user_id)

    # Добавляем само сообщение нажатия кнопки в список
    save_msg_id(user_id, event.message.id)

    status_msg = await event.respond(t(user_id, 'clearing'))

    msg_ids = get_and_clear_user_messages(user_id)

    # Удаляем пачками по 100 элементов (ограничение Telegram API)
    for i in range(0, len(msg_ids), 100):
        batch = msg_ids[i:i + 100]
        try:
            await bot_client.delete_messages(user_id, batch)
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщений для {user_id}: {e}")

    try:
        await status_msg.delete()
    except Exception:
        pass

    final_msg = await bot_client.send_message(
        user_id,
        t(user_id, 'cleared'),
        buttons=get_keyboard(user_id)
    )
    save_msg_id(user_id, final_msg.id)
    logger.info(f"Пользователь {user_id} очистил свой чат.")


@bot_client.on(events.NewMessage(pattern=r'^📜 Логи$'))
async def show_logs_handler(event):
    user_id = event.sender_id
    save_msg_id(user_id, event.message.id)

    if user_id != ADMIN_ID:
        res = await event.respond("⛔ Доступ запрещён.")
        save_msg_id(user_id, res.id)
        return

    log_path = 'data/bot.log'
    if not os.path.exists(log_path):
        res = await event.respond("📭 Лог-файл пуст или не найден.")
        save_msg_id(user_id, res.id)
        return

    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    last_lines = lines[-MAX_LOG_LINES:]
    log_text = "".join(last_lines)
    res = await event.respond(f"📜 **Последние {MAX_LOG_LINES} строк лога:**\n\n```\n{log_text}\n```")
    save_msg_id(user_id, res.id)


@bot_client.on(events.NewMessage)
async def text_input_handler(event):
    user_id = event.sender_id
    text = event.text.strip()

    all_buttons = ["📜 Логи"]
    for lang_texts in TEXTS.values():
        all_buttons.extend([
            lang_texts['start_btn'],
            lang_texts['list_btn'],
            lang_texts['clear_btn'],
            lang_texts['lang_btn']
        ])

    if text in all_buttons or text.startswith('/'):
        return

    if not (text.startswith('@') or text.startswith('https://t.me/')):
        return

    save_msg_id(user_id, event.message.id)
    update_user_activity(user_id)

    clean_ch = normalize_channel_name(text)
    if not clean_ch:
        res = await event.respond(t(user_id, 'invalid_channel'), buttons=get_keyboard(user_id))
        save_msg_id(user_id, res.id)
        return

    user_channels = get_user_channels(user_id)
    if clean_ch in user_channels:
        res = await event.respond(
            t(user_id, 'already_added').format(channel=clean_ch),
            buttons=get_keyboard(user_id)
        )
        save_msg_id(user_id, res.id)
        return

    success = add_user_channel(user_id, clean_ch)
    if not success:
        limit_msg = t(user_id, 'limit_reached')
        res = await event.respond(limit_msg, buttons=get_keyboard(user_id))
        save_msg_id(user_id, res.id)
        return

    res = await event.respond(
        t(user_id, 'added_success').format(channel=clean_ch),
        buttons=get_keyboard(user_id)
    )
    save_msg_id(user_id, res.id)
    logger.info(f"Пользователь {user_id} добавил канал @{clean_ch}.")

# ==============================
# ФОНОВЫЕ ЗАДАЧИ
# ==============================

async def send_post_to_user(user_id: int, news_text: str, msg):
    # Отправляет пост пользователю и сохраняет ID отправленных сообщений
    if msg.media:
        media_path = await user_client.download_media(msg.media)
        if media_path and os.path.exists(media_path):
            try:
                if len(news_text) <= MAX_CAPTION_LENGTH:
                    res = await bot_client.send_file(
                        user_id, media_path,
                        caption=news_text,
                        supports_streaming=True
                    )
                    save_msg_id(user_id, res.id)
                else:
                    res1 = await bot_client.send_file(user_id, media_path, supports_streaming=True)
                    res2 = await bot_client.send_message(user_id, news_text)
                    save_msg_id(user_id, res1.id)
                    save_msg_id(user_id, res2.id)
            finally:
                if os.path.exists(media_path):
                    os.remove(media_path)
        else:
            res = await bot_client.send_message(user_id, news_text)
            save_msg_id(user_id, res.id)
    else:
        res = await bot_client.send_message(user_id, news_text)
        save_msg_id(user_id, res.id)


async def fetch_channel_posts_loop():
    await asyncio.sleep(5)

    while True:
        unique_channels = get_all_unique_channels()

        if unique_channels:
            logger.info(f"Сканирую {len(unique_channels)} уникальных каналов...")

            for channel in unique_channels:
                try:
                    users = get_users_for_channel(channel)

                    for user_id in users:
                        last_id = get_last_seen_id(user_id, channel)

                        messages = await user_client.get_messages(
                            channel,
                            min_id=last_id,
                            limit=MAX_POSTS_PER_CHECK
                        )

                        if not messages:
                            continue

                        if last_id == 0:
                            update_last_seen_id(user_id, channel, messages[0].id)
                            continue

                        chat = await user_client.get_entity(channel)
                        chat_title = getattr(chat, 'title', channel)

                        for msg in reversed(messages):
                            if msg.id > last_id:
                                news_text = f"📰 **{chat_title}** (`@{channel}`)\n\n{msg.text or ''}"
                                await send_post_to_user(user_id, news_text, msg)
                                update_last_seen_id(user_id, channel, msg.id)
                                logger.info(f"Пост {msg.id} из @{channel} отправлен пользователю {user_id}.")

                except FloodWaitError as e:
                    logger.warning(f"FloodWait. Пауза на {e.seconds} секунд...")
                    await asyncio.sleep(e.seconds)
                except (ChannelPrivateError, UsernameInvalidError):
                    logger.warning(f"Канал @{channel} недоступен или не существует.")
                except Exception as e:
                    logger.error(f"Ошибка получения постов из @{channel}: {e}")

                await asyncio.sleep(DELAY_BETWEEN_CHANNELS)

        await asyncio.sleep(CHECK_INTERVAL)


async def cleanup_loop():
    while True:
        try:
            cleanup_inactive_users(INACTIVITY_DAYS)
        except Exception as e:
            logger.error(f"Ошибка при очистке неактивных пользователей: {e}")
        await asyncio.sleep(86400)

# ==============================
# ЗАПУСК
# ==============================

async def main():
    logger.info("Запуск системы...")

    await bot_client.start(bot_token=BOT_TOKEN)
    await user_client.start()

    logger.info("Загружаю диалоги юзербота...")
    await user_client.get_dialogs()

    bot_info = await bot_client.get_me()
    user_info = await user_client.get_me()

    logger.info(f"Бот запущен: @{bot_info.username}")
    logger.info(f"Юзербот подключён: {user_info.first_name}")
    logger.info("Система готова к работе.")

    asyncio.create_task(fetch_channel_posts_loop())
    asyncio.create_task(cleanup_loop())

    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )


if __name__ == '__main__':
    asyncio.run(main())
