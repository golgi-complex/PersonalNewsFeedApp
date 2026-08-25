# 📰 Telegram News Feed Bot

A bot for tracking and forwarding news from Telegram channels directly to your personal chat with the bot. Manage channels through a convenient button menu. Supports Russian and English languages.

---

## ⚙️ Features

- 📡 Automatic forwarding of new posts from selected channels
- ➕ Adding channels by sending a username or link directly to the chat
- ❌ Removing channels via inline buttons
- 📋 Viewing the list of tracked channels with a counter
- 🧹 Clearing chat history with the bot
- 🌐 Switching interface language (RU / EN)
- 💾 Data stored in SQLite database
- 🔐 Access protected — only the bot owner can manage it
- 🧹 Automatic cleanup of inactive users after 60 days

---

## 📁 Project Structure

```
project/
├── main.py           ← main program
├── data/             ← created automatically on first launch
│   ├── database.sqlite   ← SQLite database
│   ├── user_session      ← Telethon user session
│   ├── bot_session       ← Telethon bot session
│   └── bot.log           ← activity log
├── .env              ← environment variables (API keys)
├── .gitignore        ← git ignore rules
├── requirements.txt  ← dependencies
└── README.md         ← documentation
```

---

## 🔧 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your_username/your_repo.git
cd your_repo
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
pyaes==1.6.1
pyasn1==0.6.4
python-dotenv==1.2.2
rsa==4.9.1
Telethon==1.44.0
```

Install them:

```bash
pip install -r requirements.txt
```

---

## 🔒 File Permissions (recommended)

Run once after the first launch to protect sensitive files:

```bash
chmod 600 .env
chmod 600 data/user_session.session
chmod 600 data/bot_session.session
chmod 600 data/database.sqlite
chmod 700 data/
```

---

## 🚀 Running the Bot

```bash
python main.py
```

On the first launch, Telegram will ask you to log in — enter your phone number and the confirmation code. After that, the session will be saved and you won't need to log in again on subsequent runs.

You will see in the terminal:

```
2026-01-01 12:00:00 [INFO] База данных инициализирована.
2026-01-01 12:00:00 [INFO] Запуск системы...
2026-01-01 12:00:01 [INFO] Бот запущен: @your_bot
2026-01-01 12:00:01 [INFO] Юзербот подключён: Name
2026-01-01 12:00:01 [INFO] Система готова к работе.
```

---

## 🔄 Updating the Bot on Server

```bash
git pull
python main.py
```

---

## 📱 Usage

Open the chat with the bot in Telegram and press **/start**.

| Button | Action |
|---|---|
| ▶️ Start | Open the main menu |
| 📋 My Channels | Show tracked channels with counter (e.g. 3/10) |
| 🧹 Clear Chat | Delete message history in the chat with the bot |
| 🌐 English / Русский | Switch interface language |

### How to Add a Channel

Simply send the username or link directly to the chat:
- `@durov`
- `https://t.me/durov`

### How to Remove a Channel

1. Press **📋 My Channels**
2. Press the **❌ Delete** button next to the channel you want to remove

---

## ⚙️ Configuration

All key settings are at the top of `main.py`:

| Constant | Default | Description |
|---|---|---|
| `CHECK_INTERVAL` | 300 | Channel check interval in seconds |
| `DELAY_BETWEEN_CHANNELS` | 4 | Pause between channel requests in seconds |
| `INACTIVITY_DAYS` | 60 | Days before inactive user is deleted |
| `MAX_CHANNELS_PER_USER` | 10 | Maximum channels per user |
| `MAX_POSTS_PER_CHECK` | 10 | Maximum new posts per check |

---

## ⚠️ Important

- Only **public channels** (with a username) are supported
- Data is stored in `data/` folder — add it to `.gitignore`
- Do not share `.env` and session files (`*.session`) with anyone — they contain access to your Telegram account
- Activity log is saved to `data/bot.log`

---

---

# 📰 Telegram News Feed Bot

Бот для отслеживания и пересылки новостей из Telegram-каналов прямо в ваш личный чат с ботом. Управление каналами через удобное меню с кнопками. Поддерживает русский и английский язык.

---

## ⚙️ Возможности

- 📡 Автоматическая пересылка новых постов из выбранных каналов
- ➕ Добавление каналов отправкой юзернейма или ссылки прямо в чат
- ❌ Удаление каналов через инлайн-кнопки
- 📋 Просмотр списка каналов со счётчиком
- 🧹 Очистка истории чата с ботом
- 🌐 Переключение языка интерфейса (RU / EN)
- 💾 Данные хранятся в базе SQLite
- 🔐 Защита доступа — управлять ботом может только владелец
- 🧹 Автоматическое удаление неактивных пользователей через 60 дней

---

## 📁 Структура проекта

```
project/
├── main.py           ← основная программа
├── data/             ← создаётся автоматически при первом запуске
│   ├── database.sqlite   ← база данных SQLite
│   ├── user_session      ← сессия Telethon юзербота
│   ├── bot_session       ← сессия Telethon бота
│   └── bot.log           ← лог активности
├── .env              ← переменные окружения (API ключи)
├── .gitignore        ← правила git ignore
├── requirements.txt  ← зависимости
└── README.md         ← документация
```

---

## 🔧 Установка

### 1. Клонируй репозиторий

```bash
git clone https://github.com/твой_username/твой_репозиторий.git
cd твой_репозиторий
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
pyaes==1.6.1
pyasn1==0.6.4
python-dotenv==1.2.2
rsa==4.9.1
Telethon==1.44.0
```

Установка:

```bash
pip install -r requirements.txt
```

---

## 🔒 Права доступа к файлам (рекомендуется)

Выполни один раз после первого запуска для защиты чувствительных файлов:

```bash
chmod 600 .env
chmod 600 data/user_session.session
chmod 600 data/bot_session.session
chmod 600 data/database.sqlite
chmod 700 data/
```

---

## 🚀 Запуск

```bash
python main.py
```

При первом запуске Telegram попросит тебя войти в аккаунт — введи номер телефона и код подтверждения. После этого сессия сохранится и при следующих запусках авторизация не потребуется.

В терминале появится:

```
2026-01-01 12:00:00 [INFO] База данных инициализирована.
2026-01-01 12:00:00 [INFO] Запуск системы...
2026-01-01 12:00:01 [INFO] Бот запущен: @твой_бот
2026-01-01 12:00:01 [INFO] Юзербот подключён: Имя
2026-01-01 12:00:01 [INFO] Система готова к работе.
```

---

## 🔄 Обновление бота на сервере

```bash
git pull
python main.py
```

---

## 📱 Использование

Открой чат с ботом в Telegram и нажми **/start**.

| Кнопка | Действие |
|---|---|
| ▶️ Старт | Открыть главное меню |
| 📋 Мои каналы | Показать список каналов со счётчиком (например 3/10) |
| 🧹 Очистить чат | Удалить историю сообщений в чате с ботом |
| 🌐 English / Русский | Переключить язык интерфейса |

### Как добавить канал

Просто отправь юзернейм или ссылку прямо в чат:
- `@durov`
- `https://t.me/durov`

### Как удалить канал

1. Нажми **📋 Мои каналы**
2. Нажми кнопку **❌ Удалить** рядом с нужным каналом

---

## ⚙️ Настройки

Все ключевые настройки находятся в начале файла `main.py`:

| Константа | Значение | Описание |
|---|---|---|
| `CHECK_INTERVAL` | 300 | Интервал проверки каналов в секундах |
| `DELAY_BETWEEN_CHANNELS` | 4 | Пауза между запросами к каналам в секундах |
| `INACTIVITY_DAYS` | 60 | Дней до удаления неактивного пользователя |
| `MAX_CHANNELS_PER_USER` | 10 | Максимум каналов на пользователя |
| `MAX_POSTS_PER_CHECK` | 10 | Максимум новых постов за одну проверку |

---

## ⚠️ Важно

- Отслеживаются только **публичные каналы** (с username)
- Данные хранятся в папке `data/` — добавь её в `.gitignore`
- Не передавай файлы `.env` и сессий (`*.session`) третьим лицам — они содержат доступ к твоему аккаунту
- Лог активности сохраняется в `data/bot.log`
