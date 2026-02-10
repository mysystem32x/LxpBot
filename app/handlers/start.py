from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram import Router, F

from aiogram.fsm.context import FSMContext
from states.login import LoginForm

from aiogram.filters import CommandStart, StateFilter

from keyboard.inline_kbs import start_command, buttons_account, back_to_main

from db.models import User

from api.check_exist import login_data
from api.get_scheduler import add_to_data

from datetime import datetime

starter = Router()

async def show_profile(message_or_call, user):
    try:
        # Исправляем отображение даты поступления (убираем крокозябры)
        dt_str = user.createdAt
        if dt_str:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            date_display = dt.strftime("%d.%m.%Y")
        else:
            date_display = "Не указана"
    except Exception as e:
        print(f"Date parsing error: {e}")
        date_display = "Ошибка даты"

    # Исправляем логику ролей (STUDENT -> Студент, остальное -> Преподаватель)
    role_display = "Студент" if user.role == "STUDENT" else "Преподаватель"

    caption = f"""
<b>👤 Ваш профиль</b>
                                   
🔹 Имя: {user.firstName or 'Не указано'}
🔹 Фамилия: {user.lastName or 'Не указано'}
🔹 Почта: {user.email}
📅 Дата поступления: <code>{date_display}</code>

📞 Номер: <code>{user.phoneNumber or 'Не указано'}</code>
🎲 Роль: <b>{role_display}</b>
"""
    user_id = message_or_call.from_user.id
    if isinstance(message_or_call, Message):
        await message_or_call.answer_photo(f"{user.avatar}", caption=caption, parse_mode="HTML", reply_markup=buttons_account(user_id))
    else:
        await message_or_call.message.delete()
        await message_or_call.message.answer_photo(f"{user.avatar}", caption=caption, parse_mode="HTML", reply_markup=buttons_account(user_id))

@starter.message(CommandStart(), StateFilter("*"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    user = await User.get_or_none(telegram_id=message.from_user.id)

    if user:
        await show_profile(message, user)
    else:
        await message.answer(
            "Приветствую тебя, студент ITHub!\n"
            "Я — бот, который поможет тебе с расписанием и заданиями.\n"
            "Нажми кнопку ниже, чтобы войти.", 
            reply_markup=start_command()
        )

@starter.callback_query(F.data == "profile")
async def profile_callback(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await User.get_or_none(telegram_id=call.from_user.id)
    if user:
        await show_profile(call, user)
    else:
        await call.answer("Пользователь не найден", show_alert=True)

@starter.callback_query(F.data == "start")
async def enter_information(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("Введите данные от LXP через пробел или с новой строки:\n\nEmail\nПароль")
    await state.set_state(LoginForm.data)

@starter.message(LoginForm.data)
async def process_form(message: Message, state: FSMContext):
    data = message.text.split()

    if len(data) < 2:
        await message.answer("Некорректный формат. Введите email и пароль через пробел.")
        return

    email = data[0]
    password = data[1]
    
    if login_data(email, password):
        user = await User.get_or_none(telegram_id=message.from_user.id)
        if not user:
            user = await User.create(
                email=email,
                password=password,
                telegram_id=message.from_user.id
            )
        else:
            user.email = email
            user.password = password
            await user.save()

        await add_to_data(email, password, message.from_user.id)
        await message.answer("✅ Авторизация успешна!", reply_markup=back_to_main())
    else:
        await message.answer("❌ Данные неверны! Проверьте еще раз.", reply_markup=start_command())
    
    await state.clear()
