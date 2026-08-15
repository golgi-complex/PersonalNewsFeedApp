# 📰 Telegram News Feed Bot

A bot for tracking and forwarding news from Telegram channels directly to your personal chat with the bot. Manage channels through a convenient button menu. Supports Russian and English languages.

---

## ⚙️ Features

- 📡 Automatic forwarding of new posts from selected channels
- ➕ Adding channels through the bot menu
- ❌ Removing channels via inline buttons
- 📋 Viewing the list of tracked channels
- 🧹 Clearing chat history with the bot
- 🌐 Switching interface language (RU / EN)
- 💾 Saving channels and language settings between restarts

---

## 📁 Project Structure

```
project/
├── main.py           ← main program
├── channels.txt      ← list of tracked channels (created automatically)
├── language.txt      ← saved interface language (created automatically)
├── .env              ← environment variables (API keys)
├── requirements.txt  ← dependencies
└── README_EN.md      ← documentation in English
```

---

## 🔧 Installation

### 1. Clone the repository or copy the project files

```bash
mkdir telegram_news_bot
cd telegram_news_bot
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv myenv
source myenv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Getting API Keys

### API_ID and API_HASH (Telegram API)

1. Go to [my.telegram.org](https://my.telegram.org)
2. Log in to your Telegram account
3. Click **API development tools**
4. Fill out the form (name and description can be anything)
5. Copy **App api_id** and **App api_hash**

### BOT_TOKEN

1. Open Telegram and find **@BotFather**
2. Send `/newbot`
3. Choose a name and username for your bot
4. Copy the token you receive

---

## 📄 Setting Up the .env File

Create a `.env` file in the project folder and paste:

```
API_ID=123456789
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
```

---

## 📦 Dependencies (requirements.txt)

```
telethon
python-dotenv
```

Install them:

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Bot

```bash
python main.py
```

On the first launch, Telegram will ask you to log in — enter your phone number and the confirmation code. After that, the session will be saved and you won't need to log in again on subsequent runs.

You will see in the terminal:

```
Starting system...
✅ Bot started: @your_bot
✅ Account connected: Name
🌐 Current language: EN
🚀 System is ready.
```

---

## 📱 Usage

Open the chat with the bot in Telegram and press **/start**.

| Button | Action |
|---|---|
| ▶️ Start | Open the main menu |
| 📋 Channel List | Show all tracked channels |
| ➕ Add Channel | Add a new channel |
| 🧹 Clear Chat | Delete message history in the chat with the bot |
| 🌐 English / Русский | Switch interface language |

### How to Add a Channel

1. Press **➕ Add Channel**
2. Send the username or link to the channel:
   - `@durov`
   - `https://t.me/durov`

### How to Remove a Channel

1. Press **📋 Channel List**
2. Press the **❌ Delete** button next to the channel you want to remove

---

## ⚠️ Important

- The bot forwards messages **only to your personal chat** with the bot
- Only **public channels** (with a username) are supported
- `channels.txt` and `language.txt` are created automatically on first launch
- Do not share `.env` and session files (`*.session`) with anyone — they contain access to your Telegram account

# 📰 Telegram News Feed Bot

Бот для отслеживания и пересылки новостей из Telegram-каналов прямо в ваш личный чат с ботом. Управление каналами через удобное меню с кнопками. Поддерживает русский и английский язык.

---

## ⚙️ Возможности

- 📡 Автоматическая пересылка новых постов из выбранных каналов
- ➕ Добавление каналов через меню бота
- ❌ Удаление каналов через инлайн-кнопки
- 📋 Просмотр списка отслеживаемых каналов
- 🧹 Очистка истории чата с ботом
- 🌐 Переключение языка интерфейса (RU / EN)
- 💾 Сохранение каналов и языка между перезапусками

---

## 📁 Структура проекта

```
project/
├── main.py           ← основная программа
├── channels.txt      ← список отслеживаемых каналов (создаётся автоматически)
├── language.txt      ← сохранённый язык интерфейса (создаётся автоматически)
├── .env              ← переменные окружения (API ключи)
├── requirements.txt  ← зависимости
└── README_RU.md      ← документация на русском
```

---

## 🔧 Установка

### 1. Клонируй репозиторий или скопируй файлы проекта

```bash
mkdir telegram_news_bot
cd telegram_news_bot
```

### 2. Создай и активируй виртуальную среду

```bash
python3 -m venv myenv
source myenv/bin/activate
```

### 3. Установи зависимости

```bash
pip install -r requirements.txt
```

---

## 🔑 Получение API ключей

### API_ID и API_HASH (Telegram API)

1. Зайди на сайт [my.telegram.org](https://my.telegram.org)
2. Войди в свой аккаунт Telegram
3. Нажми **API development tools**
4. Заполни форму (название и описание — любые)
5. Скопируй **App api_id** и **App api_hash**

### BOT_TOKEN

1. Открой Telegram и найди **@BotFather**
2. Напиши `/newbot`
3. Придумай имя и username бота
4. Скопируй полученный токен

---

## 📄 Настройка файла .env

Создай файл `.env` в папке проекта и вставь:

```
API_ID=123456789
API_HASH=твой_api_hash
BOT_TOKEN=токен_от_botfather
```

---

## 📦 Зависимости (requirements.txt)

```
telethon
python-dotenv
```

Установка:

```bash
pip install -r requirements.txt
```

---

## 🚀 Запуск

```bash
python main.py
```

При первом запуске Telegram попросит тебя войти в аккаунт — введи номер телефона и код подтверждения. После этого сессия сохранится и при следующих запусках авторизация не потребуется.

В терминале появится:

```
Запуск системы...
✅ Бот запущен: @твой_бот
✅ Аккаунт подключён: Имя
🌐 Текущий язык: RU
🚀 Система готова к работе.
```

---

## 📱 Использование

Открой чат с ботом в Telegram и нажми **/start**.

| Кнопка | Действие |
|---|---|
| ▶️ Старт | Открыть главное меню |
| 📋 Список каналов | Показать все отслеживаемые каналы |
| ➕ Добавить канал | Добавить новый канал |
| 🧹 Очистить чат | Удалить историю сообщений в чате с ботом |
| 🌐 English / Русский | Переключить язык интерфейса |

### Как добавить канал

1. Нажми **➕ Добавить канал**
2. Отправь username или ссылку на канал:
   - `@durov`
   - `https://t.me/durov`

### Как удалить канал

1. Нажми **📋 Список каналов**
2. Нажми кнопку **❌ Удалить** рядом с нужным каналом

---

## ⚠️ Важно

- Бот пересылает сообщения **только в твой личный чат** с ботом
- Отслеживаются только **публичные каналы** (с username)
- Файлы `channels.txt` и `language.txt` создаются автоматически при первом запуске
- Не передавай файлы `.env` и сессий (`*.session`) третьим лицам — они содержат доступ к твоему аккаунту
