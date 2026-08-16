import os
import asyncio
from functools import wraps
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
# Загружаем ID администратора
ADMIN_ID = int(os.getenv('ADMIN_ID'))

CHANNELS_FILE = 'channels.txt'
LANG_FILE = 'language.txt'

# --- Работа с файлами данных ---

def load_channels():
    if not os.path.exists(CHANNELS_FILE):
        return set()
    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def save_channels(channels):
    with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
        for channel in channels:
            f.write(f"{channel}\n")

def load_language():
    if not os.path.exists(LANG_FILE):
        return 'ru'
    with open(LANG_FILE, 'r', encoding='utf-8') as f:
        lang = f.read().strip()
        return lang if lang in ['ru', 'en'] else 'ru'

def save_language(lang):
    with open(LANG_FILE, 'w', encoding='utf-8') as f:
        f.write(lang)

target_channels = load_channels()
current_lang = load_language()

waiting_for_add = {}

user_client = TelegramClient('user_session', API_ID, API_HASH)
bot_client = TelegramClient('bot_session', API_ID, API_HASH)

# --- Декоратор приватного доступа ---

def admin_only(func):
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        if event.sender_id != ADMIN_ID:
            if isinstance(event, events.CallbackQuery.Event):
                await event.answer("⛔ Доступ ограничен.", alert=True)
            else:
                await event.respond("⛔ Извините, это частный бот. Доступ разрешён только владельцу.")
            return
        return await func(event, *args, **kwargs)
    return wrapper

# --- Словарь локализации ---

TEXTS = {
    'ru': {
        'start_btn': "▶️ Старт",
        'list_btn': "📋 Список каналов",
        'add_btn': "➕ Добавить канал",
        'clear_btn': "🧹 Очистить чат",
        'lang_btn': "🌐 English",
        'welcome': "👋 **Управление лентой новостей**\n\nИспользуйте меню ниже для выбора действия:",
        'empty_list': "📭 Список отслеживаемых каналов пуст.",
        'channel_list_title': "📋 **Отслеживаемые каналы:**",
        'delete_btn': "❌ Удалить",
        'prompt_add': (
            "✏️ Отправьте юзернейм или ссылку на канал (например: `@durov` или `https://t.me/durov`).\n\n"
            "💡 _Удалить добавленный канал всегда можно через раздел 📋 **Список каналов**._"
        ),
        'clearing': "⏳ Очищаю историю сообщений...",
        'cleared': "✨ Чат очищен! Клавиатура снова доступна:",
        'added_success': "✅ Канал `{channel}` успешно добавлен в список!",
        'deleted_success': "🗑 Канал `{channel}` был удалён из списка.",
        'not_found': "Канал уже отсутствует в списке.",
        'lang_changed': "🌐 Язык успешно изменён на русский!"
    },
    'en': {
        'start_btn': "▶️ Start",
        'list_btn': "📋 Channel List",
        'add_btn': "➕ Add Channel",
        'clear_btn': "🧹 Clear Chat",
        'lang_btn': "🌐 Русский",
        'welcome': "👋 **News Feed Management**\n\nUse the menu below to select an action:",
        'empty_list': "📭 Tracked channels list is empty.",
        'channel_list_title': "📋 **Tracked Channels:**",
        'delete_btn': "❌ Delete",
        'prompt_add': (
            "✏️ Send the username or link of the channel (e.g. `@durov` or `https://t.me/durov`).\n\n"
            "💡 _You can always delete a channel via 📋 **Channel List**._"
        ),
        'clearing': "⏳ Clearing message history...",
        'cleared': "✨ Chat cleared! Keyboard is ready:",
        'added_success': "✅ Channel `{channel}` successfully added!",
        'deleted_success': "🗑 Channel `{channel}` was removed from the list.",
        'not_found': "Channel is not in the list.",
        'lang_changed': "🌐 Language successfully changed to English!"
    }
}

def get_keyboard():
    t = TEXTS[current_lang]
    return [
        [Button.text(t['start_btn'], resize=True), Button.text(t['list_btn'])],
        [Button.text(t['add_btn']), Button.text(t['clear_btn'])],
        [Button.text(t['lang_btn'])]
    ]

# --- Обработчики команд бота ---

@bot_client.on(events.NewMessage(pattern=r'(/start|/menu|^▶️ Старт$|^▶️ Start$)'))
@admin_only
async def start_handler(event):
    user_id = event.sender_id
    waiting_for_add[user_id] = False
    await event.respond(TEXTS[current_lang]['welcome'], buttons=get_keyboard())

# --- Переключение языка ---
@bot_client.on(events.NewMessage(pattern=r'^(🌐 English|🌐 Русский)$'))
@admin_only
async def switch_language_handler(event):
    global current_lang
    user_id = event.sender_id
    waiting_for_add[user_id] = False

    current_lang = 'en' if current_lang == 'ru' else 'ru'
    save_language(current_lang)

    await event.respond(
        TEXTS[current_lang]['lang_changed'],
        buttons=get_keyboard()
    )

# --- Список каналов ---
@bot_client.on(events.NewMessage(pattern=r'^(📋 Список каналов|📋 Channel List)$'))
@admin_only
async def list_channels_handler(event):
    user_id = event.sender_id
    waiting_for_add[user_id] = False
    t = TEXTS[current_lang]

    if not target_channels:
        await event.respond(t['empty_list'], buttons=get_keyboard())
        return

    inline_buttons = [
        [Button.inline(f"{t['delete_btn']} {ch}", data=f"del_{ch}")]
        for ch in target_channels
    ]

    channels_list = "\n".join([f"• {ch}" for ch in target_channels])
    await event.respond(
        f"{t['channel_list_title']}\n\n{channels_list}",
        buttons=inline_buttons
    )

# --- Добавление канала ---
@bot_client.on(events.NewMessage(pattern=r'^(➕ Добавить канал|➕ Add Channel)$'))
@admin_only
async def prompt_add_handler(event):
    user_id = event.sender_id
    waiting_for_add[user_id] = True

    await event.respond(
        TEXTS[current_lang]['prompt_add'],
        buttons=get_keyboard()
    )

# --- Удаление канала через инлайн-кнопку ---
@bot_client.on(events.CallbackQuery(pattern=r'del_(.+)'))
@admin_only
async def inline_delete_handler(event):
    channel = event.pattern_match.group(1).decode('utf-8')
    t = TEXTS[current_lang]

    if channel in target_channels:
        target_channels.remove(channel)
        save_channels(target_channels)
        await event.answer(f"{channel} deleted!")
        await event.edit(t['deleted_success'].format(channel=channel))
    else:
        await event.answer(t['not_found'])

# --- Очистка чата ---
@bot_client.on(events.NewMessage(pattern=r'^(🧹 Очистить чат|🧹 Clear Chat)$'))
@admin_only
async def clear_chat_handler(event):
    user_id = event.sender_id
    waiting_for_add[user_id] = False
    t = TEXTS[current_lang]

    status_msg = await event.respond(t['clearing'])
    bot_info = await bot_client.get_me()

    messages_to_delete = []
    async for message in user_client.iter_messages(bot_info.id):
        messages_to_delete.append(message.id)

        if len(messages_to_delete) >= 100:
            await user_client.delete_messages(bot_info.id, messages_to_delete, revoke=True)
            messages_to_delete = []

    if messages_to_delete:
        await user_client.delete_messages(bot_info.id, messages_to_delete, revoke=True)

    await bot_client.send_message(
        event.chat_id,
        t['cleared'],
        buttons=get_keyboard()
    )

# --- Обработчик ввода имени канала ---
@bot_client.on(events.NewMessage)
@admin_only
async def text_input_handler(event):
    user_id = event.sender_id
    text = event.text.strip()
    t = TEXTS[current_lang]

    # Игнорируем системные кнопки
    all_buttons = []
    for lang in TEXTS.values():
        all_buttons.extend([lang['start_btn'], lang['list_btn'], lang['add_btn'], lang['clear_btn'], lang['lang_btn']])

    if text in all_buttons or text.startswith('/'):
        return

    if waiting_for_add.get(user_id):
        channel = text
        if not channel.startswith('@') and not channel.startswith('https://t.me/'):
            channel = f"@{channel}"

        target_channels.add(channel)
        save_channels(target_channels)
        waiting_for_add[user_id] = False

        await event.respond(t['added_success'].format(channel=channel), buttons=get_keyboard())
        return

# --- Пересылка новостей из отслеживаемых каналов ---
@user_client.on(events.NewMessage)
async def handle_new_post(event):
    # Работаем только с сообщениями из каналов
    if not event.is_channel:
        return

    chat = await event.get_chat()

    # Приводим все сохранённые юзернеймы к чистому виду без '@' и ссылок
    normalized_target_channels = set()
    for ch in target_channels:
        clean_ch = ch.strip().lower().replace('https://t.me/', '').replace('@', '')
        normalized_target_channels.add(clean_ch)

    # Получаем юзернейм и ID текущего канала
    chat_username = chat.username.lower() if getattr(chat, 'username', None) else None
    chat_id_str = str(chat.id)

    # Проверяем совпадение
    is_target = False
    if chat_username and chat_username in normalized_target_channels:
        is_target = True
    elif chat_id_str in normalized_target_channels:
        is_target = True

    if is_target:
        chat_title = getattr(chat, 'title', 'Канал')
        news_text = f"📰 **{chat_title}**\n\n{event.text or ''}"

        print(f"📥 Получен новый пост из: {chat_title} (@{chat_username})")

        try:
            if event.media:
                await bot_client.send_file(ADMIN_ID, event.media, caption=news_text)
            else:
                await bot_client.send_message(ADMIN_ID, news_text)
            print(f"✅ Пост из '{chat_title}' переслан владельцу.")
        except Exception as e:
            print(f"❌ Ошибка пересылки поста из '{chat_title}': {e}")

# --- Запуск клиентов ---

async def main():
    print("Запуск системы...")
    await bot_client.start(bot_token=BOT_TOKEN)
    await user_client.start()

    bot_info = await bot_client.get_me()
    user_info = await user_client.get_me()

    print(f"✅ Бот запущен: @{bot_info.username}")
    print(f"✅ Юзербот подключён: {user_info.first_name}")
    print(f"🔐 Владелец (ADMIN_ID): {ADMIN_ID}")
    print(f"🌐 Язык интерфейса: {current_lang.upper()}")
    print("🚀 Отслеживание новостей активно.")

    await asyncio.gather(
        user_client.run_until_disconnected(),
        bot_client.run_until_disconnected()
    )

if __name__ == '__main__':
    asyncio.run(main())
