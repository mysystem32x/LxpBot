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

import locale
from datetime import datetime

try:
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
except:
    pass

starter = Router()

async def show_profile(message_or_call, user):
    dt = datetime.fromisoformat(f"{user.createdAt}".replace("Z", "+00:00"))
    caption = f"""
<b> 💁🏻‍♀️ Ваш профиль </b>
                                   
🔹 Имя: {user.firstName}
🔹 Фамилия: {user.lastName}
🔹 Почта: {user.email}
🖥 Дата поступления: <tg-spoiler>{dt.strftime("%d %B %Y")}</tg-spoiler>

📞 Номер: <tg-spoiler>{user.phoneNumber}</tg-spoiler>
🎲 Роль: <b>{'Студент' if user.role == 'student' else 'Преподаватель'}</b>
"""
    if isinstance(message_or_call, Message):
        await message_or_call.answer_photo(f"{user.avatar}", caption=caption, parse_mode="HTML", reply_markup=buttons_account())
    else:
        await message_or_call.message.delete()
        await message_or_call.message.answer_photo(f"{user.avatar}", caption=caption, parse_mode="HTML", reply_markup=buttons_account())

@starter.message(CommandStart(), StateFilter("*"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    user = await User.get_or_none(telegram_id=message.from_user.id)

    if user:
        await show_profile(message, user)
    else:
        await message.answer(
            "Приветствую тебя, дорогой студент ITHub'a\n"
            "Я - бот, который поможет тебе с расписаниями, заданиями и многим другим!\n"
            "Нажмите кнопку ниже, чтобы войти.", 
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
    await call.message.answer("Отлично!\nОтправьте мне данные от LXP!\nПример:\nemail\npassword")
    await state.set_state(LoginForm.data)

@starter.message(LoginForm.data)
async def process_form(message: Message, state: FSMContext):
    data = message.text.split()

    if len(data) != 2:
        await message.answer("Некорректный формат. Введите email и пароль через пробел или на разных строках.")
        return

    email, password = data
    
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
