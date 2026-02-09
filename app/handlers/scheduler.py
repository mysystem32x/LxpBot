from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, BufferedInputFile
from aiogram.types import Message, CallbackQuery
from aiogram import Router, F
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import textwrap



# Импорт функции из api/get_scheduler
from api.get_scheduler import get_schedule
from db.models import User

schedulerlist = Router()

def convert_utc_to_msk(utc_time_str):
    """
    Конвертирует время из UTC в московское (UTC+3)
    """
    if not utc_time_str:
        return "??:??"
    
    try:
        # Парсим UTC время
        utc_time = datetime.fromisoformat(utc_time_str.replace('Z', ''))
        # Добавляем 3 часа для московского времени
        msk_time = utc_time + timedelta(hours=3)
        return msk_time.strftime('%H:%M')
    except:
        return "??:??"

def get_date_from_utc_msk(utc_time_str):
    """
    Получаем дату из UTC времени с учетом MSK
    """
    try:
        utc_time = datetime.fromisoformat(utc_time_str.replace('Z', ''))
        msk_time = utc_time + timedelta(hours=3)
        return msk_time.date()
    except:
        return datetime.now().date()

def get_datetime_from_utc_msk(utc_time_str):
    """
    Получаем datetime из UTC времени с учетом MSK
    """
    try:
        utc_time = datetime.fromisoformat(utc_time_str.replace('Z', ''))
        return utc_time + timedelta(hours=3)
    except:
        return datetime.now()

# Загрузка шрифтов
def load_fonts():
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    return font_large, font_medium, font_small


def create_schedule_image(lessons):
    width = 1200
    base_height = 200
    lesson_height = 160
    height = base_height + len(lessons) * lesson_height
    height = max(900, min(height, 3500))

    img = Image.new("RGB", (width, height), (245, 247, 250))
    draw = ImageDraw.Draw(img)

    font_large, font_medium, font_small = load_fonts()

    # ===== HEADER =====
    header_h = 150
    draw.rectangle([(0, 0), (width, header_h)], fill=(32, 90, 170))

    title = "РАСПИСАНИЕ ЗАНЯТИЙ"
    draw.text((width // 2, 45), title, fill="white", font=font_large, anchor="mm")

    stats = f"Всего занятий: {len(lessons)}"
    draw.text((width // 2, 105), stats, fill="#DDE8FF", font=font_medium, anchor="mm")

    # ===== CONTENT =====
    y = header_h + 40
    current_date = None
    day_counter = 0

    sorted_lessons = sorted(lessons, key=lambda x: x["from"])

    for i, lesson in enumerate(sorted_lessons, 1):
        msk_datetime = get_datetime_from_utc_msk(lesson["from"])
        date_str = msk_datetime.strftime("%d.%m")

        # ===== DATE BLOCK =====
        if date_str != current_date:
            current_date = date_str
            day_counter += 1

            draw.text((80, y), f"ДЕНЬ {day_counter} • {date_str}",
                      fill=(32, 90, 170), font=font_medium)
            draw.line([(80, y + 40), (width - 80, y + 40)], fill=(200, 220, 240), width=2)
            y += 70

        # ===== CARD SHADOW =====
        card_x1, card_y1 = 60, y
        card_x2, card_y2 = width - 60, y + 130

        shadow_offset = 6
        draw.rounded_rectangle(
            [(card_x1 + shadow_offset, card_y1 + shadow_offset),
             (card_x2 + shadow_offset, card_y2 + shadow_offset)],
            radius=20,
            fill=(220, 220, 220)
        )

        # ===== CARD =====
        draw.rounded_rectangle(
            [(card_x1, card_y1), (card_x2, card_y2)],
            radius=20,
            fill="white",
            outline=(220, 230, 240),
            width=2
        )

        # ===== TIME BLOCK =====
        time_start = convert_utc_to_msk(lesson['from'])
        time_end = convert_utc_to_msk(lesson['to'])

        draw.rounded_rectangle(
            [(card_x1 + 20, card_y1 + 20), (card_x1 + 160, card_y1 + 110)],
            radius=15,
            fill=(32, 90, 170)
        )

        draw.text((card_x1 + 90, card_y1 + 45), time_start,
                  fill="white", font=font_medium, anchor="mm")
        draw.text((card_x1 + 90, card_y1 + 80), time_end,
                  fill="white", font=font_medium, anchor="mm")

        # ===== LESSON INFO =====
        text_x = card_x1 + 200

        discipline = lesson["discipline"]["name"]
        lines = textwrap.wrap(discipline, width=32)

        for j, line in enumerate(lines[:2]):
            draw.text((text_x, card_y1 + 25 + j * 32),
                      line, fill=(30, 30, 30), font=font_medium)

        details_y = card_y1 + 90
        details = f"Кабинет: {lesson['classroom']['name']}   •   Группа: {lesson['learningGroup']['name']}"
        draw.text((text_x, details_y), details, fill="#666", font=font_small)

        # ===== STATUS =====
        status_x = card_x2 - 140
        is_online = lesson.get("isOnline", False)

        status_color = (76, 175, 80) if is_online else (156, 39, 176)
        status_text = "ОНЛАЙН" if is_online else "ОЧНО"

        draw.rounded_rectangle(
            [(status_x, card_y1 + 40), (status_x + 110, card_y1 + 90)],
            radius=15,
            fill=status_color
        )

        draw.text((status_x + 55, card_y1 + 65),
                  status_text, fill="white", font=font_small, anchor="mm")

        y += 160

    # ===== FOOTER =====
    footer_y = height - 120
    draw.rectangle([(0, footer_y), (width, height)], fill="#F5F7FA")

    draw.text((width // 2, footer_y + 40),
              datetime.now().strftime("%d.%m.%Y • %H:%M"),
              fill="#666", font=font_small, anchor="mm")

    draw.text((width // 2, footer_y + 80),
              "NEWLXP.RU",
              fill="#205AAA", font=font_medium, anchor="mm")

    # ===== EXPORT =====
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG", quality=95)
    img_bytes.seek(0)
    return img_bytes

@schedulerlist.callback_query(F.data == 'schedule')
async def get_scheduler_lists(call: CallbackQuery):
    user = await User.get_or_none(telegram_id=call.from_user.id)
    
    if not user:
        await call.message.delete()
        await call.message.answer("❌ Пользователь не найден в базе данных")
        return
    
    if not user.email or not user.password:
        await call.message.delete()
        await call.message.answer("❌ Данные для входа не найдены. Пожалуйста, войдите в аккаунт.")
        return
    
    schedule_data = await get_schedule(user.email, user.password)
    
    if not schedule_data or 'data' not in schedule_data:
        await call.message.delete()
        await call.message.answer(
            "❌ Не удалось получить расписание\n"
            "Проверьте данные для входа в настройках"
        )
        return
    
    lessons = schedule_data['data']['manyClasses']
    
    # Фильтруем сегодняшние занятия с учетом MSK
    today = datetime.now().date()
    today_lessons = []
    for lesson in lessons:
        lesson_date = get_date_from_utc_msk(lesson['from'])
        if lesson_date == today:
            today_lessons.append(lesson)
    
    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📅 СЕГОДНЯ ({len(today_lessons)})", callback_data="schedule_today")],
            [InlineKeyboardButton(text="📋 ПОЛНОЕ РАСПИСАНИЕ", callback_data="schedule_full")],
            [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="profile")]
        ]
    )
    
    await call.message.delete()
    await call.message.answer(
        "📚 <b>РАСПИСАНИЕ ЗАНЯТИЙ</b>\n\n"
        f"Найдено занятий: <b>{len(lessons)}</b>\n"
        f"Сегодня занятий: <b>{len(today_lessons)}</b>\n\n"
        "Выберите период для просмотра:",
        parse_mode="HTML",
        reply_markup=keyboard
    )

@schedulerlist.callback_query(F.data == "schedule_today")
async def show_today_schedule(call: CallbackQuery):
    user = await User.get_or_none(telegram_id=call.from_user.id)
    
    if not user or not user.email or not user.password:
        await call.answer("❌ Данные пользователя не найдены", show_alert=True)
        return
    
    schedule_data = await get_schedule(user.email, user.password)
    
    if not schedule_data or 'data' not in schedule_data:
        await call.answer("❌ Ошибка получения расписания", show_alert=True)
        return
    
    lessons = schedule_data['data']['manyClasses']
    
    # Фильтруем сегодняшние занятия с учетом MSK
    today = datetime.now().date()
    today_lessons = []
    for lesson in lessons:
        lesson_date = get_date_from_utc_msk(lesson['from'])
        if lesson_date == today:
            today_lessons.append(lesson)
    
    if not today_lessons:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📋 ПОЛНОЕ РАСПИСАНИЕ", callback_data="schedule_full")],
                [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="schedule")]
            ]
        )
        await call.message.delete()
        await call.message.answer(
            "🎉 <b>СЕГОДНЯ ЗАНЯТИЙ НЕТ!</b>\n\n"
            "Можно отдохнуть или заняться самообразованием",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return
    
    # Сортируем занятия по времени начала
    today_lessons.sort(key=lambda x: x['from'])
    
    # Создаем красивый текст для сегодняшних занятий
    text = "🎯 <b>РАСПИСАНИЕ НА СЕГОДНЯ</b>\n\n"
    
    for i, lesson in enumerate(today_lessons, 1):
        # Конвертируем время в московское
        start_time = convert_utc_to_msk(lesson['from'])
        end_time = convert_utc_to_msk(lesson['to'])
        
        # Тип занятия
        lesson_type = "🟣 ОЧНО" if not lesson.get('isOnline', False) else "🟢 ОНЛАЙН"
        
        text += f"<b>#{i} │ {start_time}–{end_time} │ {lesson_type}</b>\n"
        text += f"📚 <b>{lesson['discipline']['name']}</b>\n"
        
        if lesson.get('classroom') and lesson['classroom'].get('name'):
            text += f"📍 {lesson['classroom']['name']}\n"
        
        if lesson.get('learningGroup') and lesson['learningGroup'].get('name'):
            text += f"👥 {lesson['learningGroup']['name']}\n"
        
        if lesson.get('teacher') and lesson['teacher'].get('name'):
            text += f"👨‍🏫 {lesson['teacher']['name']}\n"
        
        if lesson.get('meetingLink'):
            text += f"🔗 <a href='{lesson['meetingLink']}'>ПРИСОЕДИНИТЬСЯ</a>\n"
        
        text += "─" * 30 + "\n"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 ПОЛНОЕ РАСПИСАНИЕ", callback_data="schedule_full")],
            [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="schedule")]
        ]
    )
    
    await call.message.delete()
    await call.message.answer(text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)

@schedulerlist.callback_query(F.data == "schedule_full")
async def show_full_schedule(call: CallbackQuery):
    await call.answer("🔄 ФОРМИРУЕМ РАСПИСАНИЕ...")
    
    user = await User.get_or_none(telegram_id=call.from_user.id)
    
    if not user or not user.email or not user.password:
        await call.answer("❌ Данные пользователя не найдены", show_alert=True)
        return
    
    schedule_data = await get_schedule(user.email, user.password)
    
    if not schedule_data or 'data' not in schedule_data:
        await call.answer("❌ Ошибка получения расписания", show_alert=True)
        return
    
    lessons = schedule_data['data']['manyClasses']
    
    if not lessons:
        await call.message.answer("📭 НА ЭТОЙ НЕДЕЛЕ ЗАНЯТИЙ НЕТ!")
        return
    
    # Создаем изображение с расписанием
    img_bytes = create_schedule_image(lessons)
    
    # Статистика
    online_count = sum(1 for l in lessons if l.get('isOnline', False))
    offline_count = len(lessons) - online_count
    
    # Кнопки
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 СЕГОДНЯ", callback_data="schedule_today")],
            [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="schedule")]
        ]
    )
    
    # Отправляем фото
    await call.message.answer_photo(
        BufferedInputFile(img_bytes.getvalue(), filename="schedule.png"),
        caption=f"📊 <b>СТАТИСТИКА:</b>\n"
                f"• Всего занятий: <b>{len(lessons)}</b>\n"
                f"• Очные: <b>{offline_count}</b>\n"
                f"• Онлайн: <b>{online_count}</b>\n\n"
                f"<i>Для возврата нажмите кнопку ниже</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )