from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, BufferedInputFile
from aiogram.types import Message, CallbackQuery
from aiogram import Router, F
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

def load_fonts():
    # Приоритет Noto Sans для гарантированной кириллицы (кубиков не будет)
    font_path = "/home/ubuntu/LXPBOT/assets/fonts/noto.ttf"
    font_bold_path = "/home/ubuntu/LXPBOT/assets/fonts/noto-bold.ttf"
    
    # Запасной вариант - Comic Neue
    alt_font_path = "/home/ubuntu/LXPBOT/assets/fonts/comic.ttf"
    alt_font_bold_path = "/home/ubuntu/LXPBOT/assets/fonts/comic-bold.ttf"
    
    def get_font(path, size, alt_path=None):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
        if alt_path and os.path.exists(alt_path):
            return ImageFont.truetype(alt_path, size)
        return ImageFont.load_default()

    try:
        font_large = get_font(font_bold_path, 48, alt_font_bold_path)
        font_medium_bold = get_font(font_bold_path, 32, alt_font_bold_path)
        font_medium = get_font(font_path, 32, alt_font_path)
        font_small = get_font(font_path, 24, alt_font_path)
        font_tiny = get_font(font_path, 20, alt_font_path)
    except Exception as e:
        print(f"Font loading error: {e}")
        font_large = font_medium = font_medium_bold = font_small = font_tiny = ImageFont.load_default()
            
    except Exception as e:
        print(f"Font loading error: {e}")
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_medium_bold = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()
        
    return font_large, font_medium, font_medium_bold, font_small, font_tiny

def create_schedule_image(lessons):
    width = 1200
    header_h = 200
    lesson_height = 160
    day_header_h = 80
    
    sorted_lessons = sorted(lessons, key=lambda x: x["from"])
    
    # Считаем количество уникальных дней
    unique_days = len(set(get_date_from_utc_msk(l["from"]) for l in sorted_lessons))
    
    total_height = header_h + (len(lessons) * lesson_height) + (unique_days * day_header_h) + 100
    total_height = max(800, total_height)

    # Цветовая палитра (Строгий современный дизайн)
    bg_color = (240, 242, 245) # Светло-серый фон
    accent_color = (33, 150, 243) # Blue
    text_dark = (33, 37, 41) # Почти черный
    text_muted = (108, 117, 125) # Серый текст
    card_bg = (255, 255, 255)
    
    img = Image.new("RGB", (width, total_height), bg_color)
    draw = ImageDraw.Draw(img)
    font_large, font_medium, font_medium_bold, font_small, font_tiny = load_fonts()

    # ===== HEADER =====
    draw.rectangle([(0, 0), (width, header_h)], fill=accent_color)

    title = "РАСПИСАНИЕ ЗАНЯТИЙ"
    draw.text((width // 2, 80), title, fill="white", font=font_large, anchor="mm")
    
    stats = f"Всего занятий: {len(lessons)}"
    draw.text((width // 2, 140), stats, fill="white", font=font_medium, anchor="mm")

    # ===== CONTENT =====
    y = header_h + 40
    current_date = None

    for i, lesson in enumerate(sorted_lessons, 1):
        msk_datetime = get_datetime_from_utc_msk(lesson["from"])
        date_str = msk_datetime.strftime("%d.%m.%Y")
        day_name = msk_datetime.strftime("%A").upper()
        
        # Перевод дней недели
        days_ru = {"MONDAY": "ПОНЕДЕЛЬНИК", "TUESDAY": "ВТОРНИК", "WEDNESDAY": "СРЕДА", 
                   "THURSDAY": "ЧЕТВЕРГ", "FRIDAY": "ПЯТНИЦА", "SATURDAY": "СУББОТА", "SUNDAY": "ВОСКРЕСЕНЬЕ"}
        day_name_ru = days_ru.get(day_name, day_name)

        # ===== DATE BLOCK =====
        if date_str != current_date:
            current_date = date_str
            y += 20
            draw.text((80, y), f"{day_name_ru} • {date_str}", fill=text_dark, font=font_medium_bold)
            draw.line([(80, y + 45), (width - 80, y + 45)], fill=accent_color, width=2)
            y += 70

        # ===== CARD =====
        card_margin = 80
        card_x1, card_y1 = card_margin, y
        card_x2, card_y2 = width - card_margin, y + 140

        # Сама карточка (без теней, строгий стиль)
        draw.rectangle([(card_x1, card_y1), (card_x2, card_y2)], fill=card_bg, outline=(222, 226, 230), width=1)

        # Время
        time_start = convert_utc_to_msk(lesson['from'])
        time_end = convert_utc_to_msk(lesson['to'])
        
        # Боковая полоска акцента
        draw.rectangle([(card_x1, card_y1), (card_x1 + 10, card_y2)], fill=accent_color)
        
        draw.text((card_x1 + 40, card_y1 + 40), f"{time_start} - {time_end}", fill=accent_color, font=font_medium_bold)

        # Информация о занятии
        text_x = card_x1 + 300
        discipline = lesson["discipline"]["name"]
        lines = textwrap.wrap(discipline, width=45)
        
        for j, line in enumerate(lines[:2]):
            draw.text((text_x, card_y1 + 30 + j * 40), line, fill=text_dark, font=font_medium)

        classroom = lesson['classroom']['name'] if lesson.get('classroom') else "Не указано"
        group = lesson['learningGroup']['name'] if lesson.get('learningGroup') else "Не указано"
        details = f"Ауд: {classroom}  |  Группа: {group}"
        draw.text((text_x, card_y1 + 100), details, fill=text_muted, font=font_small)

        # Тип (Онлайн/Очно)
        is_online = lesson.get("isOnline", False)
        status_text = "ОНЛАЙН" if is_online else "ОЧНО"
        
        status_w = 120
        draw.rectangle([(card_x2 - status_w - 40, card_y1 + 45), (card_x2 - 40, card_y1 + 95)], outline=accent_color, width=2)
        draw.text((card_x2 - (status_w//2) - 40, card_y1 + 70), status_text, fill=accent_color, font=font_small, anchor="mm")

        y += lesson_height

    # ===== FOOTER =====
    footer_y = total_height - 50
    draw.text((width // 2, footer_y), f"LXP Бот • {datetime.now().strftime('%d.%m.%Y %H:%M')}", fill=text_muted, font=font_tiny, anchor="mm")

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
        print(f"Error updating schedule message: {e}")
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
        BufferedInputFile(img_bytes.getvalue(), filename="schedule.png"),
        caption="📊 Ваше актуальное расписание",
        reply_markup=keyboard
    )
