from aiogram.types import CallbackQuery
from aiogram import F, Router

# Импортируем сразу либы для кнопочек
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Бдшечка
from db.models import User

tasklist = Router()

# Импортируем сюда API'шку, для получения заданий
from api.get_scheduler import get_tasks, get_task_details, login

# Глобальные переменные для хранения состояния
user_tasks_data = {}  # {user_id: {"tasks": [...], "page": 1}}
TASKS_PER_PAGE = 5

@tasklist.callback_query(F.data=="tasks")
async def show_tasks_list(call: CallbackQuery):
    user_id = call.from_user.id
    user = await User.get_or_none(telegram_id=user_id)
    
    # Получаем все задачи
    all_tasks = await get_tasks(user.email, user.password, user.telegram_id)
    
    # Сохраняем в глобальный словарь
    user_tasks_data[user_id] = {
        "tasks": all_tasks,
        "page": 1
    }
    
    # Показываем первую страницу
    await show_tasks_page(call)

async def show_tasks_page(call: CallbackQuery, page: int = None):
    user_id = call.from_user.id
    data = user_tasks_data.get(user_id)
    
    if not data:
        await call.answer("❌ Данные устарели, нажмите /tasks")
        return
    
    if page:
        data["page"] = page
    
    current_page = data["page"]
    all_tasks = data["tasks"]
    
    # Вычисляем какие задачи показывать
    start_idx = (current_page - 1) * TASKS_PER_PAGE
    end_idx = start_idx + TASKS_PER_PAGE
    page_tasks = all_tasks[start_idx:end_idx]
    
    # Формируем сообщение
    builder = InlineKeyboardBuilder()
    
    for i, task in enumerate(page_tasks, start_idx + 1):
        task_name = task["contentBlock"]["name"]
        task_id = task["contentBlock"]["id"]
        deadline = task.get("taskDeadline")
        
        # Эмоджи для дедлайна
        emoji = get_deadline_emoji(deadline)
        
        # Укорачиваем длинные названия
        if len(task_name) > 30:
            task_name = task_name[:27] + "..."
        
        builder.add(InlineKeyboardButton(
            text=f"{emoji} {task_name}", 
            callback_data=f"task_{task_id}"
        ))
    
    builder.adjust(1)
    
    # Кнопки пагинации
    nav_buttons = []
    total_pages = (len(all_tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE
    
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад", 
            callback_data=f"page_{current_page-1}"
        ))
    
    nav_buttons.append(InlineKeyboardButton(
        text=f"{current_page}/{total_pages}", 
        callback_data="current"
    ))
    
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="Вперед ➡️", 
            callback_data=f"page_{current_page+1}"
        ))
    
    builder.row(*nav_buttons)
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="profile"))
    
    # Отправляем/редактируем сообщение
    if call.message.text:
        await call.message.edit_text(f"📚 Задания (страница {current_page}):<blockquote>🔴 - Просрочено\n🟡 - Сегодня дедлайн\n🕒 - Есть время</blockquote>",
            reply_markup=builder.as_markup(), parse_mode="HTML"
        )
    else:
        await call.message.answer(f"📚 Задания (страница {current_page}):<blockquote>🔴 - Просрочено\n🟡 - Сегодня дедлайн\n🕒 - Есть время</blockquote>", 
            reply_markup=builder.as_markup(), parse_mode="HTML"
        )

@tasklist.callback_query(F.data.startswith("page_"))
async def change_page(call: CallbackQuery):
    page = int(call.data.split("_")[1])
    await show_tasks_page(call, page)

def get_deadline_emoji(deadline_str: str) -> str:
    if not deadline_str:
        return "🕒"  # Нет дедлайна
    
    from datetime import datetime, timezone
    
    deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    
    # Разница в днях
    diff_days = (deadline - now).days
    
    if diff_days < 0:
        return "🔴"  # Просрочено
    elif diff_days == 0:
        return "🟡"  # Сегодня
    else:
        return "🕒"  # Есть время


@tasklist.callback_query(F.data.startswith("task_"))
async def show_task_details(call: CallbackQuery):
    task_id = call.data.split("_")[1]
    
    # 1. Находим задание в списке
    user_data = user_tasks_data.get(call.from_user.id)
    if not user_data:
        await call.answer("❌ Сначала откройте список заданий")
        return
    
    task = None
    for t in user_data["tasks"]:
        if t["contentBlock"]["id"] == task_id:
            task = t
            break
    
    if not task:
        await call.answer("❌ Задание не найдено")
        return
    
    # 2. Получаем пользователя для student_id
    user = await User.get_or_none(telegram_id=call.from_user.id)
    if not user:
        await call.answer("❌ Пользователь не найден")
        return
    
    # 3. Получаем токен и детали задания
    token = login(user.email, user.password)
    
    task_details = await get_task_details(
        token=token,
        topic_id=task["topic"]["id"],
        content_id=task["contentBlock"]["id"],
        student_id=user.id_student
    )
    
    # 4. Форматируем информацию
    task_name = task["contentBlock"]["name"]
    discipline = task["topic"]["chapter"]["discipline"]["name"]
    topic_name = task["topic"]["name"]
    max_score = task["contentBlock"].get("maxScore", "?")
    deadline = task.get("taskDeadline")
    status = task["studentTopic"].get("status", "Не начато")
    
    # 5. Определяем эмодзи статуса
    status_emoji = {
        None: "❓",
        "Не сдано": "⏳",
        "В ожидании": "👁️",
        "Сдано": "✅"
    }.get(status, "❓")
    
    # 6. Определяем эмодзи дедлайна
    deadline_emoji = "🕒"
    if deadline:
        from datetime import datetime, timezone
        deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        if deadline_dt < now:
            deadline_emoji = "🔴"
        elif (deadline_dt - now).days == 0:
            deadline_emoji = "🟡"
    
    # 7. Собираем текст
    text = f"📌 <b>{task_name}</b>\n\n"
    text += f"{status_emoji} <b>Статус:</b> {status if status else 'Не начато'}\n"
    text += f"📚 <b>Дисциплина:</b> {discipline}\n"
    text += f"📖 <b>Тема:</b> {topic_name}\n"
    text += f"💯 <b>Макс. балл:</b> {max_score}\n"
    
    if deadline:
        deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        deadline_str = deadline_dt.strftime("%d.%m.%Y, %H:%M")
        text += f"{deadline_emoji} <b>Дедлайн:</b> {deadline_str}\n"
    else:
        text += f"{deadline_emoji} <b>Дедлайн:</b> Не установлен\n"
    
    # 8. Добавляем описание если есть
    if task_details and task_details.get("body"):
        import json, re
        try:
            body_data = json.loads(task_details["body"])
            description_text = ""
            
            for item in body_data:
                if item.get("type") == "paragraph" and item.get("data", {}).get("text"):
                    clean_text = item["data"]["text"]
                    clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
                    clean_text = re.sub(r'\s{2,}', ' ', clean_text).strip()
                    if clean_text:
                        description_text += clean_text + "\n\n"
            
            if description_text:
                text += f"\n📄 <b>Описание:</b>\n"
                if len(description_text) > 1000:
                    description_text = description_text[:997] + "..."
                text += description_text
                
        except Exception as e:
            text += f"\n📄 <b>Описание:</b> Ошибка чтения\n"
            print(f"Ошибка парсинга описания: {e}")
    
    text += "\n" + "━" * 30
    
    # 9. Формируем URL для кнопки
    try:
        organization_id = task["topic"]["chapter"]["discipline"]["suborganization"]["organization"]["id"]
        discipline_id = task["topic"]["chapter"]["disciplineId"]
        topic_id = task["topic"]["id"]
        content_id = task["contentBlock"]["id"]
        student_id = user.id_student
        
        task_url = (
            f"https://newlxp.ru/education/"
            f"{organization_id}/disciplines/"
            f"{discipline_id}/topics/"
            f"{topic_id}/tasks/"
            f"{content_id}/students/"
            f"{student_id}"
        )
    except KeyError as e:
        print(f"Ошибка формирования URL: {e}")
        task_url = f"https://newlxp.ru"  # Запасной вариант
    
    # 10. Кнопки
    builder = InlineKeyboardBuilder()
    
    # Кнопка с реальным URL
    builder.add(InlineKeyboardButton(
        text="🔗 Перейти к заданию", 
        url=task_url
    ))
    
    # Кнопка "Назад"
    builder.add(InlineKeyboardButton(
        text="⬅️ Назад к списку", 
        callback_data="tasks"
    ))
    
    
    # 11. Отправляем
    try:
        await call.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        if len(text) > 4096:
            text = text[:4000] + "...\n\n⚠️ <i>Описание было сокращено</i>"
            await call.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )
    
    await call.answer()