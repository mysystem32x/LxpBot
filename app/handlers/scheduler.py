from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, BufferedInputFile
from aiogram.types import Message, CallbackQuery
from aiogram import Router, F
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import textwrap
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

def get_datetime_from_utc_msk(utc_time_str):
    try:
        utc_time = datetime.fromisoformat(utc_time_str.replace('Z', ''))
        return utc_time + timedelta(hours=3)
    except:
        return datetime.now()

def load_safe_font(size, bold=False):
    """Пытается загрузить системный шрифт, который точно есть на Win/Linux"""
    font_names = []
    if os.name == 'nt': # Windows
        if bold:
            font_names = ["arialbd.ttf", "tahomabd.ttf", "verdana.ttf"]
        else:
            font_names = ["arial.ttf", "tahoma.ttf", "verdana.ttf"]
    else: # Linux
        if bold:
            font_names = ["DejaVuSans-Bold.ttf", "FreeSans-Bold.ttf", "LiberationSans-Bold.ttf"]
        else:
            font_names = ["DejaVuSans.ttf", "FreeSans.ttf", "LiberationSans.ttf"]
    
    # Также проверяем наши скачанные шрифты как приоритетные
    local_fonts = ["assets/fonts/noto-bold.ttf", "assets/fonts/noto.ttf"] if not bold else ["assets/fonts/noto-bold.ttf"]
    
    for font_name in (local_fonts + font_names):
        try:
            # Пробуем загрузить по имени (из системных путей) или по пути
            return ImageFont.truetype(font_name, size)
        except:
            continue
            
    return ImageFont.load_default()

def create_schedule_image(lessons):
    width = 1000
    header_h = 180
    lesson_height = 140
    day_header_h = 70
    
    sorted_lessons = sorted(lessons, key=lambda x: x["from"])
    unique_days = len(set(get_date_from_utc_msk(l["from"]) for l in sorted_lessons))
    
    total_height = header_h + (len(lessons) * lesson_height) + (unique_days * day_header_h) + 100
    total_height = max(600, total_height)

    # Цвета (Строгий современный стиль)
    bg_color = (245, 247, 250)
    accent_color = (33, 150, 243) # Blue
    text_dark = (40, 44, 52)
    text_muted = (120, 124, 135)
    card_bg = (255, 255, 255)
    
    img = Image.new("RGB", (width, total_height), bg_color)
    draw = ImageDraw.Draw(img)
    
    font_lg = load_safe_font(44, True)
    font_md_b = load_safe_font(28, True)
    font_md = load_safe_font(28)
    font_sm = load_safe_font(22)
    font_xs = load_safe_font(18)

    # Header
    draw.rectangle([(0, 0), (width, header_h)], fill=accent_color)
    draw.text((width // 2, 70), "РАСПИСАНИЕ ЗАНЯТИЙ", fill="white", font=font_lg, anchor="mm")
    draw.text((width // 2, 130), f"Всего занятий: {len(lessons)}", fill="white", font=font_md, anchor="mm")

    y = header_h + 30
    current_date = None
    days_ru = {"MONDAY": "ПОНЕДЕЛЬНИК", "TUESDAY": "ВТОРНИК", "WEDNESDAY": "СРЕДА", 
               "THURSDAY": "ЧЕТВЕРГ", "FRIDAY": "ПЯТНИЦА", "SATURDAY": "СУББОТА", "SUNDAY": "ВОСКРЕСЕНЬЕ"}

    for lesson in sorted_lessons:
        msk_dt = get_datetime_from_utc_msk(lesson["from"])
        date_str = msk_dt.strftime("%d.%m.%Y")
        
        if date_str != current_date:
            current_date = date_str
            day_name = days_ru.get(msk_dt.strftime("%A").upper(), msk_dt.strftime("%A").upper())
            y += 20
            draw.text((60, y), f"{day_name} • {date_str}", fill=text_dark, font=font_md_b)
            draw.line([(60, y + 40), (width - 60, y + 40)], fill=accent_color, width=2)
            y += 60

        # Card
        x1, y1 = 60, y
        x2, y2 = width - 60, y + 120
        draw.rectangle([(x1, y1), (x2, y2)], fill=card_bg, outline=(220, 220, 220), width=1)
        draw.rectangle([(x1, y1), (x1 + 8, y2)], fill=accent_color) # Боковая полоса

        # Time
        time_str = f"{convert_utc_to_msk(lesson['from'])} - {convert_utc_to_msk(lesson['to'])}"
        draw.text((x1 + 30, y1 + 35), time_str, fill=accent_color, font=font_md_b)

        # Info
        discipline = lesson["discipline"]["name"]
        lines = textwrap.wrap(discipline, width=40)
        for i, line in enumerate(lines[:2]):
            draw.text((x1 + 250, y1 + 25 + i * 35), line, fill=text_dark, font=font_md)

        classroom = lesson['classroom']['name'] if lesson.get('classroom') else "???"
        group = lesson['learningGroup']['name'] if lesson.get('learningGroup') else "???"
        draw.text((x1 + 250, y1 + 85), f"Ауд: {classroom}  |  Группа: {group}", fill=text_muted, font=font_sm)

        # Status
        status = "ОНЛАЙН" if lesson.get("isOnline") else "ОЧНО"
        draw.rectangle([(x2 - 130, y1 + 40), (x2 - 30, y1 + 80)], outline=accent_color, width=2)
        draw.text((x2 - 80, y1 + 60), status, fill=accent_color, font=font_xs, anchor="mm")

        y += lesson_height

    # Footer
    draw.text((width // 2, total_height - 40), f"LXP Бот • {datetime.now().strftime('%d.%m.%Y %H:%M')}", fill=text_muted, font=font_xs, anchor="mm")

    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes.getvalue()

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
