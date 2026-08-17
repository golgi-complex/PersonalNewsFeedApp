import os
import asyncio
from functools import wraps
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import JoinChannelRequest

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

CHANNELS_FILE = 'data/channels.txt'
LANG_FILE = 'data/language.txt'

# --- Нормализация и работа с файлами ---

def normalize_channel_name(ch: str) -> str:
    return ch.strip().lower().replace('https://t.me/', '').replace('@', '')

def load_channels() -> set:
    if not os.path.exists(CHANNELS_FILE):
        return set()
    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        return set(normalize_channel_name(line) for line in f if line.strip())

def save_channels(channels: set):
    os.makedirs(os.path.dirname(CHANNELS_FILE), exist_ok=True)
    with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
        for channel in channels:
            f.write(f"{channel}\n")

def load_language() -> str:
    if not os.path.exists(LANG_FILE):
        return 'ru'
    with open(LANG_FILE, 'r', encoding='utf-8') as f:
        lang = f.read().strip()
        return lang if lang in ['ru', 'en'] else 'ru'

def save_language(lang: str):
    os.makedirs(os.path.dirname(LANG_FILE), exist_ok=True)
    with open(LANG_FILE, 'w', encoding='utf-8') as f:
        f.write(lang)

target_channels = load_channels()
current_lang = load_language()

user_client = TelegramClient('data/user_session', API_ID, API_HASH)
bot_client = TelegramClient('data/bot_session', API_ID, API_HASH)

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
        'clear_btn': "🧹 Очистить чат",
        'lang_btn': "🌐 English",
        'welcome': "👋 **Управление лентой новостей**\n\n💡 Чтобы добавить канал, просто отправьте его `@юзернейм` или ссылку `https://t.me/...` прямо в чат.",
        'empty_list': "📭 Список отслеживаемых каналов пуст.",
        'channel_list_title': "📋 **Отслеживаемые каналы:**",
        'delete_btn': "❌ Удалить",
        'clearing': "⏳ Очищаю историю сообщений...",
        'cleared': "✨ Чат очищен! Клавиатура снова доступна:",
        'added_success': "✅ Канал `@{channel}` успешно добавлен и отслеживается!",
        'deleted_success': "🗑 Канал `@{channel}` был удалён из списка.",
        'not_found': "Канал уже отсутствует в списке.",
        'lang_changed': "🌐 Язык успешно изменён на русский!"
    },
    'en': {
        'start_btn': "▶️ Start",
        'list_btn': "📋 Channel List",
        'clear_btn': "🧹 Clear Chat",
        'lang_btn': "🌐 Русский",
        'welcome': "👋 **News Feed Management**\n\n💡 To add a channel, simply send its `@username` or link `https://t.me/...` directly into the chat.",
        'empty_list': "📭 Tracked channels list is empty.",
        'channel_list_title': "📋 **Tracked Channels:**",
        'delete_btn': "❌ Delete",
        'clearing': "⏳ Clearing message history...",
        'cleared': "✨ Chat cleared! Keyboard is ready:",
        'added_success': "✅ Channel `@{channel}` successfully added!",
        'deleted_success': "🗑 Channel `@{channel}` was removed from the list.",
        'not_found': "Channel is not in the list.",
        'lang_changed': "🌐 Language successfully changed to English!"
    }
}

def get_keyboard():
    t = TEXTS[current_lang]
    return [
        [Button.text(t['start_btn'], resize=True), Button.text(t['list_btn'])],
        [Button.text(t['clear_btn']), Button.text(t['lang_btn'])]
    ]

# --- Обработчики команд бота ---

@bot_client.on(events.NewMessage(pattern=r'(/start|/menu|^▶️ Старт$|^▶️ Start$)'))
@admin_only
async def start_handler(event):
    await event.respond(TEXTS[current_lang]['welcome'], buttons=get_keyboard())

# --- Переключение языка ---
@bot_client.on(events.NewMessage(pattern=r'^(🌐 English|🌐 Русский)$'))
@admin_only
async def switch_language_handler(event):
    global current_lang
    current_lang = 'en' if current_lang == 'ru' else 'ru'
    save_language(current_lang)
    await event.respond(TEXTS[current_lang]['lang_changed'], buttons=get_keyboard())

# --- Список каналов ---
@bot_client.on(events.NewMessage(pattern=r'^(📋 Список каналов|📋 Channel List)$'))
@admin_only
async def list_channels_handler(event):
    t = TEXTS[current_lang]
    if not target_channels:
        await event.respond(t['empty_list'], buttons=get_keyboard())
        return

    inline_buttons = [
        [Button.inline(f"{t['delete_btn']} @{ch}", data=f"del_{ch}")]
        for ch in target_channels
    ]
    channels_list = "\n".join([f"• @{ch}" for ch in target_channels])
    await event.respond(f"{t['channel_list_title']}\n\n{channels_list}", buttons=inline_buttons)

# --- Удаление канала через инлайн-кнопку ---
@bot_client.on(events.CallbackQuery(pattern=r'del_(.+)'))
@admin_only
async def inline_delete_handler(event):
    channel = event.pattern_match.group(1).decode('utf-8')
    t = TEXTS[current_lang]
    if channel in target_channels:
        target_channels.remove(channel)
        save_channels(target_channels)
        await event.answer(f"@{channel} deleted!")
        await event.edit(t['deleted_success'].format(channel=channel))
    else:
        await event.answer(t['not_found'])

# --- Очистка чата ---
@bot_client.on(events.NewMessage(pattern=r'^(🧹 Очистить чат|🧹 Clear Chat)$'))
@admin_only
async def clear_chat_handler(event):
    t = TEXTS[current_lang]
    await event.respond(t['clearing'])
    bot_info = await bot_client.get_me()

    messages_to_delete = []
    async for message in user_client.iter_messages(bot_info.id):
        messages_to_delete.append(message.id)
        if len(messages_to_delete) >= 100:
            await user_client.delete_messages(bot_info.id, messages_to_delete, revoke=True)
            messages_to_delete = []

    if messages_to_delete:
        await user_client.delete_messages(bot_info.id, messages_to_delete, revoke=True)

    await bot_client.send_message(event.chat_id, t['cleared'], buttons=get_keyboard())

# --- Автоматическое добавление канала по @юзернейму или ссылке ---
@bot_client.on(events.NewMessage)
@admin_only
async def text_input_handler(event):
    text = event.text.strip()
    t = TEXTS[current_lang]

    all_buttons = []
    for lang in TEXTS.values():
        all_buttons.extend([lang['start_btn'], lang['list_btn'], lang['clear_btn'], lang['lang_btn']])

    if text in all_buttons or text.startswith('/'):
        return

    if text.startswith('@') or text.startswith('https://t.me/'):
        clean_ch = normalize_channel_name(text)

        # Автоматическая подписка юзербота на новый канал
        try:
            await user_client(JoinChannelRequest(clean_ch))
        except Exception as e:
            print(f"⚠️ Не удалось автоматически подписать юзербота на {clean_ch}: {e}")

        target_channels.add(clean_ch)
        save_channels(target_channels)

        await event.respond(t['added_success'].format(channel=clean_ch), buttons=get_keyboard())

# --- Пересылка новостей из отслеживаемых каналов ---
@user_client.on(events.NewMessage)
async def handle_new_post(event):
    if not event.is_channel:
        return

    chat = await event.get_chat()
    chat_username = chat.username.lower() if getattr(chat, 'username', None) else None
    chat_id_str = str(chat.id)

    if (chat_username and chat_username in target_channels) or (chat_id_str in target_channels):
        chat_title = getattr(chat, 'title', 'Канал')
        news_text = f"📰 **{chat_title}**\n\n{event.text or ''}"

        try:
            if event.media:
                print(f"📥 Скачиваю медиа из '{chat_title}'...")
                # Скачиваем медиа во временный файл от лица юзербота
                media_path = await user_client.download_media(event.media)

                if media_path and os.path.exists(media_path):
                    try:
                        file_size = os.path.getsize(media_path)
                        print(f"📤 Отправляю медиа ({file_size} байт) ботом...")

                        if len(news_text) <= 1024:
                            await bot_client.send_file(
                                ADMIN_ID,
                                media_path,
                                caption=news_text,
                                supports_streaming=True
                            )
                        else:
                            await bot_client.send_file(
                                ADMIN_ID,
                                media_path,
                                supports_streaming=True
                            )
                            await bot_client.send_message(ADMIN_ID, news_text)
                    finally:
                        # Удаляем временный файл с диска
                        if os.path.exists(media_path):
                            os.remove(media_path)
                else:
                    await bot_client.send_message(ADMIN_ID, news_text)
            else:
                await bot_client.send_message(ADMIN_ID, news_text)

            print(f"✅ Пост из '{chat_title}' успешно переслан.")
        except Exception as e:
            print(f"❌ Ошибка пересылки из '{chat_title}': {e}")

# --- Запуск клиентов ---

async def main():
    print("Запуск системы...")
    await bot_client.start(bot_token=BOT_TOKEN)
    await user_client.start()

    print("🔄 Загружаю диалоги юзербота...")
    await user_client.get_dialogs()

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
