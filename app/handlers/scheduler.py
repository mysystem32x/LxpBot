from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, BufferedInputFile
from aiogram.types import Message, CallbackQuery
from aiogram import Router, F
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap

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

def load_fonts():
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        font_italic = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", 22)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_italic = ImageFont.load_default()
    return font_large, font_medium, font_small, font_italic

def create_schedule_image(lessons):
    width = 1200
    header_h = 250
    lesson_height = 180
    day_header_h = 100
    
    sorted_lessons = sorted(lessons, key=lambda x: x["from"])
    
    # Считаем количество уникальных дней
    unique_days = len(set(get_date_from_utc_msk(l["from"]) for l in sorted_lessons))
    
    total_height = header_h + (len(lessons) * lesson_height) + (unique_days * day_header_h) + 150
    total_height = max(1000, total_height)

    # Цветовая палитра (Романтично-эстетичная)
    bg_color = (255, 245, 247) # Нежно-розовый фон
    accent_color = (255, 105, 180) # Hot Pink
    soft_accent = (255, 182, 193) # Light Pink
    text_dark = (74, 44, 50) # Темно-коричнево-розовый
    card_bg = (255, 255, 255)
    
    img = Image.new("RGB", (width, total_height), bg_color)
    draw = ImageDraw.Draw(img)
    font_large, font_medium, font_small, font_italic = load_fonts()

    # ===== ГРАДИЕНТНЫЙ HEADER =====
    for i in range(header_h):
        r = int(255 - (i * 0.1))
        g = int(182 - (i * 0.2))
        b = int(193 - (i * 0.1))
        draw.line([(0, i), (width, i)], fill=(r, g, b))

    title = "✨ МОЁ РАСПИСАНИЕ ✨"
    draw.text((width // 2, 100), title, fill="white", font=font_large, anchor="mm")
    
    stats = f"Нас ждёт {len(lessons)} увлекательных занятий"
    draw.text((width // 2, 170), stats, fill="white", font=font_medium, anchor="mm")

    # ===== CONTENT =====
    y = header_h + 50
    current_date = None

    for i, lesson in enumerate(sorted_lessons, 1):
        msk_datetime = get_datetime_from_utc_msk(lesson["from"])
        date_str = msk_datetime.strftime("%d.%m")
        day_name = msk_datetime.strftime("%A").upper()
        
        # Перевод дней недели
        days_ru = {"MONDAY": "ПОНЕДЕЛЬНИК", "TUESDAY": "ВТОРНИК", "WEDNESDAY": "СРЕДА", 
                   "THURSDAY": "ЧЕТВЕРГ", "FRIDAY": "ПЯТНИЦА", "SATURDAY": "СУББОТА", "SUNDAY": "ВОСКРЕСЕНЬЕ"}
        day_name_ru = days_ru.get(day_name, day_name)

        # ===== DATE BLOCK =====
        if date_str != current_date:
            current_date = date_str
            y += 20
            draw.text((100, y), f"🌸 {day_name_ru} • {date_str}", fill=accent_color, font=font_medium)
            draw.line([(100, y + 50), (width - 100, y + 50)], fill=soft_accent, width=3)
            y += 80

        # ===== CARD =====
        card_margin = 80
        card_x1, card_y1 = card_margin, y
        card_x2, card_y2 = width - card_margin, y + 150

        # Тень
        draw.rounded_rectangle([(card_x1+4, card_y1+4), (card_x2+4, card_y2+4)], radius=25, fill=(230, 210, 215))
        # Сама карточка
        draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=25, fill=card_bg, outline=soft_accent, width=2)

        # Время
        time_start = convert_utc_to_msk(lesson['from'])
        time_end = convert_utc_to_msk(lesson['to'])
        
        draw.rounded_rectangle([(card_x1 + 30, card_y1 + 30), (card_x1 + 180, card_y1 + 120)], radius=20, fill=soft_accent)
        draw.text((card_x1 + 105, card_y1 + 55), time_start, fill="white", font=font_medium, anchor="mm")
        draw.text((card_x1 + 105, card_y1 + 95), time_end, fill="white", font=font_small, anchor="mm")

        # Информация о занятии
        text_x = card_x1 + 220
        discipline = lesson["discipline"]["name"]
        lines = textwrap.wrap(discipline, width=35)
        
        for j, line in enumerate(lines[:2]):
            draw.text((text_x, card_y1 + 30 + j * 35), line, fill=text_dark, font=font_medium)

        details = f"📍 {lesson['classroom']['name']}  •  👥 {lesson['learningGroup']['name']}"
        draw.text((text_x, card_y1 + 105), details, fill=(150, 120, 125), font=font_small)

        # Тип (Онлайн/Очно)
        is_online = lesson.get("isOnline", False)
        status_text = "☁️ ОНЛАЙН" if is_online else "🏛 ОЧНО"
        status_color = (135, 206, 250) if is_online else (221, 160, 221)
        
        status_w = 160
        draw.rounded_rectangle([(card_x2 - status_w - 30, card_y1 + 50), (card_x2 - 30, card_y1 + 100)], radius=15, fill=status_color)
        draw.text((card_x2 - (status_w//2) - 30, card_y1 + 75), status_text, fill="white", font=font_small, anchor="mm")

        y += lesson_height

    # ===== FOOTER =====
    footer_y = total_height - 100
    draw.text((width // 2, footer_y), f"С любовью, ваш LXP Бот • {datetime.now().strftime('%d.%m.%Y')}", fill=accent_color, font=font_italic, anchor="mm")

    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
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
            [InlineKeyboardButton(text=f"💖 СЕГОДНЯ ({len(today_lessons)})", callback_data="schedule_today")],
            [InlineKeyboardButton(text="✨ ПОЛНОЕ РАСПИСАНИЕ", callback_data="schedule_full")],
            [InlineKeyboardButton(text="🏠 ГЛАВНОЕ МЕНЮ", callback_data="profile")]
        ]
    )
    
    await call.message.delete()
    await call.message.answer(
        "🌸 <b>РАСПИСАНИЕ ЗАНЯТИЙ</b>\n\n"
        f"Найдено занятий: <b>{len(lessons)}</b>\n"
        f"Сегодня занятий: <b>{len(today_lessons)}</b>\n\n"
        "Что хочешь посмотреть?",
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
    
    if not today_lessons:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✨ ПОЛНОЕ", callback_data="schedule_full")], [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="schedule")]])
        await call.message.edit_text("✨ <b>Сегодня выходной!</b>\nОтдохни и наберись сил 💖", parse_mode="HTML", reply_markup=keyboard)
        return
    
    text = "🎯 <b>ТВОЙ ПЛАН НА СЕГОДНЯ</b>\n\n"
    for i, lesson in enumerate(today_lessons, 1):
        start = convert_utc_to_msk(lesson['from'])
        end = convert_utc_to_msk(lesson['to'])
        type_l = "☁️ ОНЛАЙН" if lesson.get('isOnline') else "🏛 ОЧНО"
        text += f"<b>{i}. {start}–{end}</b> | {type_l}\n"
        text += f"🌸 <b>{lesson['discipline']['name']}</b>\n"
        text += f"📍 {lesson['classroom']['name']}\n"
        if lesson.get('meetingLink'):
            text += f"🔗 <a href='{lesson['meetingLink']}'>Присоединиться</a>\n"
        text += "┈" * 15 + "\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✨ ПОЛНОЕ", callback_data="schedule_full")], [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="schedule")]])
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)

@schedulerlist.callback_query(F.data == "schedule_full")
async def show_full_schedule(call: CallbackQuery):
    await call.answer("🌸 Рисую расписание...")
    user = await User.get_or_none(telegram_id=call.from_user.id)
    schedule_data = await get_schedule(user.email, user.password)
    lessons = schedule_data['data']['manyClasses']
    
    img_bytes = create_schedule_image(lessons)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💖 СЕГОДНЯ", callback_data="schedule_today")], [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="schedule")]])
    
    await call.message.delete()
    await call.message.answer_photo(
        BufferedInputFile(img_bytes.getvalue(), filename="schedule.png"),
        caption="✨ Твоё прекрасное расписание на неделю ✨",
        reply_markup=keyboard
    )
