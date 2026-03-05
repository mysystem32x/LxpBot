🎓 LXP Bot — Умный помощник для студентов ItHub

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-green)](https://docs.aiogram.dev)
[![GraphQL](https://img.shields.io/badge/API-GraphQL-e535ab)](https://graphql.org)

Telegram-бот для студентов платформы [newlxp.ru](https://newlxp.ru), который предоставляет быстрый доступ к учебной информации через GraphQL API. Следи за расписанием, статусом обучения, задачами и получай уведомления прямо в Telegram.

## Demo
<img width="3" height="2" alt="изображение" src="https://github.com/user-attachments/assets/a5f6b0aa-dbbe-41ef-9dae-b86c214204cd" />
<img width="3" height="2" alt="изображение" src="https://github.com/user-attachments/assets/6155e42e-5d4c-4c19-a21e-a683edea0012" />

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


## Инструкция по запуску и использованию

### Что нужно ввести в бота (логин/пароль):
При первом запуске бота, после команды `/start`, тебе нужно будет ввести:
1. **Логин** — обычно это email, который ты используешь для входа на newlxp.ru
2. **Пароль** — пароль от аккаунта на платформе

Бот сохранит эти данные локально (в памяти или базе данных) для последующих запросов к API.

