🎓 LXP Bot — Умный помощник для студентов NewLXP

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-green)](https://docs.aiogram.dev)
[![GraphQL](https://img.shields.io/badge/API-GraphQL-e535ab)](https://graphql.org)

Telegram-бот для студентов платформы [newlxp.ru](https://newlxp.ru), который предоставляет быстрый доступ к учебной информации через GraphQL API. Следи за расписанием, статусом обучения, задачами и получай уведомления прямо в Telegram.

## 🚀 Быстрый старт

### Требования
- Python 3.10+
- Токен Telegram бота (получить у [@BotFather](https://t.me/botfather))

### Установка

1. **Клонируй репозиторий**
```bash
git clone https://github.com/yourusername/LxpBot.git
cd LxpBot
```

2. **Установи зависимости**
```bash
pip install -r requirements.txt
```

3. **Запусти бота**
```bash
python bot.py
```

## 📋 Использование

### Первый вход
После запуска бота, введи свои учетные данные от платформы newlxp.ru:

1. Нажми `/start`
2. Введи логин (обычно email)
3. Введи пароль
4. ✅ Готово! Бот запомнит тебя


## 🛠 Технологии

- **[Aiogram 3.x](https://docs.aiogram.dev)** — асинхронный фреймворк для Telegram API


## 🔧 Настройка уведомлений

Бот поддерживает гибкую настройку уведомлений:

- ⏰ За 15/30/60 минут до пары
- 📅 Ежедневный дайджест в 9:00
- ⚠️ Напоминания о дедлайнах
- 📊 Еженедельный отчет об успеваемости

## 📞 Контакты

По вопросам и предложениям:
- Telegram: [@rhytm7](https://t.me/rhytm7)
- Email: slnho7coder@gmail.com

---

**🌟 Если бот полезен — поставь звезду на GitHub!**
```

## Инструкция по запуску и использованию

### Что нужно ввести в бота (логин/пароль):
При первом запуске бота, после команды `/start`, тебе нужно будет ввести:
1. **Логин** — обычно это email, который ты используешь для входа на newlxp.ru
2. **Пароль** — пароль от аккаунта на платформе

Бот сохранит эти данные локально (в памяти или базе данных) для последующих запросов к API.

### Как настроить проект:

1. **Получи токен бота:**
   - Напиши [@BotFather](https://t.me/botfather) в Telegram
   - Создай нового бота командой `/newbot`
   - Скопируй полученный токен

2. **Настрой окружение:**
   ```bash
   # Установи зависимости
   pip install aiogram aiohttp python-dotenv pydantic
   
   # Создай файл .env
   echo "BOT_TOKEN=твой_токен_бота" > .env
   echo "API_URL=https://newlxp.ru/graphql" >> .env
   ```

3. **Проверь GraphQL API:**
   Убедись, что эндпоинт `https://newlxp.ru/graphql` доступен. Можешь проверить через браузер или Postman.

4. **Запусти бота:**
   ```bash
   python bot.py
   ```
