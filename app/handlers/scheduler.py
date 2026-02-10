from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, BufferedInputFile
from aiogram.types import Message, CallbackQuery
from aiogram import Router, F
from datetime import datetime, timedelta
import imgkit
import os

# Импорт функции из api/get_scheduler
from api.get_scheduler import get_schedule
from db.models import User

schedulerlist = Router()

def convert_utc_to_msk(utc_time_str):
    if not utc_time_str:
        return "??:??"
    try:
        utc_time = datetime.fromisoformat(utc_time_str.replace('Z', ''))
        msk_time = utc_time + timedelta(hours=3)
        return msk_time.strftime('%H:%M')
    except:
        return "??:??"

def get_date_from_utc_msk(utc_time_str):
    try:
        utc_time = datetime.fromisoformat(utc_time_str.replace('Z', ''))
        msk_time = utc_time + timedelta(hours=3)
        return msk_time.date()
    except:
        return datetime.now().date()

def create_schedule_image(lessons):
    sorted_lessons = sorted(lessons, key=lambda x: x["from"])
    
    # Группировка по дням
    days_data = {}
    days_ru = {"MONDAY": "ПОНЕДЕЛЬНИК", "TUESDAY": "ВТОРНИК", "WEDNESDAY": "СРЕДА", 
               "THURSDAY": "ЧЕТВЕРГ", "FRIDAY": "ПЯТНИЦА", "SATURDAY": "СУББОТА", "SUNDAY": "ВОСКРЕСЕНЬЕ"}
    
    for lesson in sorted_lessons:
        msk_dt = datetime.fromisoformat(lesson["from"].replace('Z', '')) + timedelta(hours=3)
        date_str = msk_dt.strftime("%d.%m.%Y")
        day_name = days_ru.get(msk_dt.strftime("%A").upper(), msk_dt.strftime("%A").upper())
        
        if date_str not in days_data:
            days_data[date_str] = {"name": day_name, "lessons": []}
        
        days_data[date_str]["lessons"].append({
            "time": f"{convert_utc_to_msk(lesson['from'])} - {convert_utc_to_msk(lesson['to'])}",
            "discipline": lesson["discipline"]["name"],
            "classroom": lesson['classroom']['name'] if lesson.get('classroom') else "Не указано",
            "group": lesson['learningGroup']['name'] if lesson.get('learningGroup') else "Не указано",
            "online": lesson.get("isOnline", False)
        })

    # HTML Шаблон с использованием Google Fonts (Comic Neue и Noto Sans)
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Comic+Neue:wght@400;700&family=Noto+Sans:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Comic Neue', 'Noto Sans', sans-serif;
                background-color: #f0f2f5;
                margin: 0;
                padding: 40px;
                width: 1000px;
            }
            .header {
                background-color: #2196f3;
                color: white;
                padding: 40px;
                text-align: center;
                border-radius: 15px 15px 0 0;
                margin-bottom: 30px;
            }
            .header h1 { margin: 0; font-size: 48px; text-transform: uppercase; }
            .header p { margin: 10px 0 0; font-size: 24px; opacity: 0.9; }
            
            .day-section { margin-bottom: 40px; }
            .day-title {
                font-size: 32px;
                font-weight: bold;
                color: #333;
                border-bottom: 3px solid #2196f3;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            
            .card {
                background: white;
                border-left: 10px solid #2196f3;
                margin-bottom: 15px;
                padding: 20px;
                display: flex;
                align-items: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .time-box {
                min-width: 180px;
                font-size: 28px;
                font-weight: bold;
                color: #2196f3;
            }
            .info-box {
                flex-grow: 1;
                padding-left: 30px;
            }
            .discipline { font-size: 30px; font-weight: bold; color: #222; margin-bottom: 5px; }
            .details { font-size: 22px; color: #666; }
            
            .status-tag {
                padding: 8px 15px;
                border: 2px solid #2196f3;
                color: #2196f3;
                font-weight: bold;
                border-radius: 5px;
                font-size: 18px;
                text-transform: uppercase;
            }
            .footer {
                text-align: center;
                color: #888;
                font-size: 18px;
                margin-top: 50px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>РАСПИСАНИЕ ЗАНЯТИЙ</h1>
            <p>Всего занятий: {{total_lessons}}</p>
        </div>
        
        {% for date, data in days.items() %}
        <div class="day-section">
            <div class="day-title">{{data.name}} • {{date}}</div>
            {% for lesson in data.lessons %}
            <div class="card">
                <div class="time-box">{{lesson.time}}</div>
                <div class="info-box">
                    <div class="discipline">{{lesson.discipline}}</div>
                    <div class="details">Ауд: {{lesson.classroom}} | Группа: {{lesson.group}}</div>
                </div>
                <div class="status-tag">{% if lesson.online %}ОНЛАЙН{% else %}ОЧНО{% endif %}</div>
            </div>
            {% endfor %}
        </div>
        {% endfor %}
        
        <div class="footer">
            LXP Бот • {{now}}
        </div>
    </body>
    </html>
    """
    
    # Простая замена шаблона (без Jinja2 для минимизации зависимостей)
    html = html_template.replace("{{total_lessons}}", str(len(lessons)))
    html = html.replace("{{now}}", datetime.now().strftime('%d.%m.%Y %H:%M'))
    
    days_html = ""
    for date, data in days_data.items():
        day_html = f'<div class="day-section"><div class="day-title">{data["name"]} • {date}</div>'
        for lesson in data["lessons"]:
            status = "ОНЛАЙН" if lesson["online"] else "ОЧНО"
            day_html += f"""
            <div class="card">
                <div class="time-box">{lesson['time']}</div>
                <div class="info-box">
                    <div class="discipline">{lesson['discipline']}</div>
                    <div class="details">Ауд: {lesson['classroom']} | Группа: {lesson['group']}</div>
                </div>
                <div class="status-tag">{status}</div>
            </div>
            """
        day_html += "</div>"
        days_html += day_html
    
    html = html.replace("{% for date, data in days.items() %}", "").replace("{% endfor %}", "")
    html = html.replace("{% for lesson in data.lessons %}", "").replace("{% if lesson.online %}ОНЛАЙН{% else %}ОЧНО{% endif %}", "")
    # На самом деле проще было переписать логику вставки, что я и сделал выше
    
    # Финальная сборка HTML
    final_html = html_template.split('{% for date, data in days.items() %}')[0] + days_html + html_template.split('{% endfor %}')[-1]
    final_html = final_html.replace("{{total_lessons}}", str(len(lessons))).replace("{{now}}", datetime.now().strftime('%d.%m.%Y %H:%M'))

    options = {
        'format': 'png',
        'encoding': "UTF-8",
        'quiet': '',
        'enable-local-file-access': '',
        'width': 1080
    }
    
    output_path = "schedule_temp.png"
    imgkit.from_string(final_html, output_path, options=options)
    
    with open(output_path, "rb") as f:
        img_bytes = f.read()
    
    os.remove(output_path)
    return img_bytes

@schedulerlist.callback_query(F.data == 'schedule')
async def get_scheduler_lists(call: CallbackQuery):
    user = await User.get_or_none(telegram_id=call.from_user.id)
    if not user or not user.email or not user.password:
        await call.message.edit_text("❌ Ошибка: Данные для входа не найдены.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="profile")]]))
        return
    
    schedule_data = await get_schedule(user.email, user.password)
    if not schedule_data or 'data' not in schedule_data:
        await call.message.edit_text("❌ Не удалось получить расписание.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="profile")]]))
        return
    
    lessons = schedule_data['data']['manyClasses']
    today = datetime.now().date()
    today_lessons = [l for l in lessons if get_date_from_utc_msk(l['from']) == today]
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📅 СЕГОДНЯ ({len(today_lessons)})", callback_data="schedule_today")],
            [InlineKeyboardButton(text="📊 ПОЛНОЕ РАСПИСАНИЕ", callback_data="schedule_full")],
            [InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="profile")]
        ]
    )
    
    await call.message.delete()
    await call.message.answer(
        "📅 <b>РАСПИСАНИЕ ЗАНЯТИЙ</b>\n\n"
        f"Найдено занятий: <b>{len(lessons)}</b>\n"
        f"Сегодня занятий: <b>{len(today_lessons)}</b>\n\n"
        "Выберите формат отображения:",
        parse_mode="HTML",
        reply_markup=keyboard
    )

@schedulerlist.callback_query(F.data == "schedule_today")
async def show_today_schedule(call: CallbackQuery):
    user = await User.get_or_none(telegram_id=call.from_user.id)
    schedule_data = await get_schedule(user.email, user.password)
    lessons = schedule_data['data']['manyClasses']
    today = datetime.now().date()
    today_lessons = sorted([l for l in lessons if get_date_from_utc_msk(l['from']) == today], key=lambda x: x['from'])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📊 ПОЛНОЕ", callback_data="schedule_full")], [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="schedule")]])
    
    if not today_lessons:
        text = "📅 <b>Сегодня занятий нет.</b>\nМожно отдохнуть!"
    else:
        text = "📅 <b>РАСПИСАНИЕ НА СЕГОДНЯ</b>\n\n"
        for i, lesson in enumerate(today_lessons, 1):
            start = convert_utc_to_msk(lesson['from'])
            end = convert_utc_to_msk(lesson['to'])
            type_l = "☁️ ОНЛАЙН" if lesson.get('isOnline') else "🏛 ОЧНО"
            text += f"<b>{i}. {start}–{end}</b> | {type_l}\n"
            text += f"📘 <b>{lesson['discipline']['name']}</b>\n"
            text += f"📍 {lesson['classroom']['name']}\n"
            if lesson.get('meetingLink'):
                text += f"🔗 <a href='{lesson['meetingLink']}'>Ссылка на встречу</a>\n"
            text += "─" * 15 + "\n"
    
    try:
        if call.message.photo:
            await call.message.delete()
            await call.message.answer(text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)
        else:
            if call.message.text != text:
                await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)
            else:
                await call.answer()
    except Exception as e:
        await call.message.answer(text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)

@schedulerlist.callback_query(F.data == "schedule_full")
async def show_full_schedule(call: CallbackQuery):
    await call.answer("Генерирую расписание...")
    user = await User.get_or_none(telegram_id=call.from_user.id)
    schedule_data = await get_schedule(user.email, user.password)
    lessons = schedule_data['data']['manyClasses']
    
    img_bytes = create_schedule_image(lessons)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📅 СЕГОДНЯ", callback_data="schedule_today")], [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="schedule")]])
    
    await call.message.delete()
    await call.message.answer_photo(
        BufferedInputFile(img_bytes, filename="schedule.png"),
        caption="📊 Ваше актуальное расписание",
        reply_markup=keyboard
    )
