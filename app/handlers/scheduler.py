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
    """Загружает шрифт с поддержкой кириллицы"""
    # Список возможных путей к шрифтам
    font_paths = [
        "assets/fonts/noto-bold.ttf" if bold else "assets/fonts/noto.ttf",
        "assets/fonts/dejavu.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    
    for path in font_paths:
        try:
            # Если путь относительный, добавляем корень проекта
            full_path = path
            if not path.startswith('/'):
                full_path = os.path.join(os.getcwd(), path)
            
            if os.path.exists(full_path):
                return ImageFont.truetype(full_path, size)
        except:
            continue
            
    return ImageFont.load_default()

def create_schedule_image(lessons):
    # Константы дизайна
    WIDTH = 1000
    PADDING = 50
    HEADER_HEIGHT = 200
    CARD_MARGIN = 25
    CARD_PADDING = 30
    SIDE_STRIP_WIDTH = 12
    
    # Сортировка
    sorted_lessons = sorted(lessons, key=lambda x: x["from"])
    
    # Группировка по дням для расчета высоты
    days_data = {}
    for lesson in sorted_lessons:
        date_str = get_datetime_from_utc_msk(lesson["from"]).strftime("%d.%m.%Y")
        if date_str not in days_data:
            days_data[date_str] = []
        days_data[date_str].append(lesson)
    
    # Расчет высоты
    # Header + (Кол-во дней * заголовок дня) + (Кол-во пар * высота пары) + Footer
    total_height = HEADER_HEIGHT + (len(days_data) * 80) + (len(lessons) * 160) + 120
    total_height = max(800, total_height)

    # Цветовая палитра (Премиальный темный/светлый стиль)
    BG_COLOR = (248, 249, 253)
    ACCENT_COLOR = (63, 81, 181) # Indigo
    ACCENT_LIGHT = (232, 234, 246)
    TEXT_MAIN = (33, 33, 33)
    TEXT_SECONDARY = (117, 117, 117)
    CARD_BG = (255, 255, 255)
    ONLINE_COLOR = (76, 175, 80) # Green
    OFFLINE_COLOR = (255, 152, 0) # Orange
    
    img = Image.new("RGB", (WIDTH, total_height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Шрифты
    font_h1 = load_safe_font(52, True)
    font_h2 = load_safe_font(32, True)
    font_time = load_safe_font(28, True)
    font_body = load_safe_font(26)
    font_info = load_safe_font(20)
    font_footer = load_safe_font(18)
    font_tag = load_safe_font(16, True)

    # 1. Header
    draw.rectangle([(0, 0), (WIDTH, HEADER_HEIGHT)], fill=ACCENT_COLOR)
    # Декоративный элемент в хедере
    draw.ellipse([WIDTH-150, -50, WIDTH+50, 150], fill=(255, 255, 255, 40))
    
    draw.text((PADDING, 60), "РАСПИСАНИЕ", fill="white", font=font_h1)
    draw.text((PADDING, 130), f"Период: {datetime.now().strftime('%d.%m')} — {(datetime.now() + timedelta(days=7)).strftime('%d.%m.%Y')}", fill=(220, 220, 220), font=font_body)
    
    # Статистика в углу хедера
    stat_text = f"Занятий: {len(lessons)}"
    stat_bbox = draw.textbbox((0, 0), stat_text, font=font_h2)
    draw.text((WIDTH - PADDING - (stat_bbox[2]-stat_bbox[0]) - 50, 80), stat_text, fill="white", font=font_h2)

    y_offset = HEADER_HEIGHT + 40
    days_ru = {"MONDAY": "Понедельник", "TUESDAY": "Вторник", "WEDNESDAY": "Среда", 
               "THURSDAY": "Четверг", "FRIDAY": "Пятница", "SATURDAY": "Суббота", "SUNDAY": "Воскресенье"}

    for date_str, day_lessons in days_data.items():
        # Заголовок дня
        msk_dt = get_datetime_from_utc_msk(day_lessons[0]["from"])
        day_name = days_ru.get(msk_dt.strftime("%A").upper(), msk_dt.strftime("%A").upper())
        
        # Подложка под дату
        draw.text((PADDING, y_offset), f"{day_name}, {date_str}", fill=ACCENT_COLOR, font=font_h2)
        y_offset += 55
        draw.line([(PADDING, y_offset), (WIDTH - PADDING, y_offset)], fill=(200, 200, 200), width=1)
        y_offset += 30

        for lesson in day_lessons:
            # Параметры карточки
            card_x1 = PADDING
            card_y1 = y_offset
            card_x2 = WIDTH - PADDING
            card_y2 = y_offset + 140
            
            # Тень (имитация)
            draw.rectangle([(card_x1+2, card_y1+2), (card_x2+2, card_y2+2)], fill=(230, 230, 230))
            # Фон карточки
            draw.rectangle([(card_x1, card_y1), (card_x2, card_y2)], fill=CARD_BG, outline=(225, 225, 225), width=1)
            
            # Акцентная полоса слева
            status_color = ONLINE_COLOR if lesson.get("isOnline") else OFFLINE_COLOR
            draw.rectangle([(card_x1, card_y1), (card_x1 + SIDE_STRIP_WIDTH, card_y2)], fill=status_color)

            # Время
            time_start = convert_utc_to_msk(lesson['from'])
            time_end = convert_utc_to_msk(lesson['to'])
            draw.text((card_x1 + 40, card_y1 + 35), f"{time_start}", fill=TEXT_MAIN, font=font_time)
            draw.text((card_x1 + 40, card_y1 + 75), f"{time_end}", fill=TEXT_SECONDARY, font=font_body)

            # Разделитель времени и контента
            draw.line([(card_x1 + 160, card_y1 + 30), (card_x1 + 160, card_y2 - 30)], fill=(230, 230, 230), width=1)

            # Дисциплина
            discipline = lesson["discipline"]["name"]
            # Ограничение длины текста
            max_chars = 45
            if len(discipline) > max_chars:
                discipline = discipline[:max_chars-3] + "..."
            
            draw.text((card_x1 + 190, card_y1 + 30), discipline, fill=TEXT_MAIN, font=font_h2)

            # Доп инфо (Аудитория, Группа)
            classroom = lesson['classroom']['name'] if lesson.get('classroom') else "—"
            group = lesson['learningGroup']['name'] if lesson.get('learningGroup') else "—"
            info_text = f"Ауд: {classroom}   •   Гр: {group}"
            draw.text((card_x1 + 190, card_y1 + 85), info_text, fill=TEXT_SECONDARY, font=font_info)

            # Тег статуса (Онлайн/Очно)
            status_text = "ОНЛАЙН" if lesson.get("isOnline") else "ОЧНО"
            tag_w, tag_h = 110, 36
            tag_x1 = card_x2 - tag_w - 30
            tag_y1 = card_y2 - tag_h - 20
            draw.rounded_rectangle([(tag_x1, tag_y1), (tag_x1 + tag_w, tag_y1 + tag_h)], radius=5, fill=ACCENT_LIGHT)
            
            # Центрирование текста в теге
            t_bbox = draw.textbbox((0, 0), status_text, font=font_tag)
            t_w = t_bbox[2] - t_bbox[0]
            t_h = t_bbox[3] - t_bbox[1]
            draw.text((tag_x1 + (tag_w - t_w)//2, tag_y1 + (tag_h - t_h)//2 - 2), status_text, fill=ACCENT_COLOR, font=font_tag)

            y_offset += 140 + CARD_MARGIN
        
        y_offset += 20

    # Footer
    footer_text = f"Сгенерировано LXP Bot • {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    draw.text((WIDTH // 2, total_height - 50), footer_text, fill=TEXT_SECONDARY, font=font_footer, anchor="mm")

    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG", optimize=True)
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
    
    if not lessons:
        await call.message.answer("❌ Расписание пусто.")
        return

    img_bytes = create_schedule_image(lessons)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📅 СЕГОДНЯ", callback_data="schedule_today")], [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="schedule")]])
    
    await call.message.delete()
    await call.message.answer_photo(
        BufferedInputFile(img_bytes, filename="schedule.png"),
        caption="📊 Ваше актуальное расписание",
        reply_markup=keyboard
    )
