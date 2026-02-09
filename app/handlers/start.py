from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram import Router

# состояния
from aiogram.fsm.context import FSMContext
from states.login import LoginForm

from aiogram.filters import CommandStart, StateFilter

# клавиатуры:
from keyboard.inline_kbs import start_command, buttons_account

# БД
from db.models import User

# API Newlxp
from api.check_exist import login_data
from api.get_scheduler import add_to_data

import locale
from datetime import datetime

# Локаль: RUS
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

starter = Router()
@starter.message(CommandStart(),StateFilter("*"))
async def start(message: Message, state: FSMContext):
    await state.clear() # Сбрасываем состояние при старте
    user = await User.get_or_none(telegram_id= message.from_user.id) # или другой идентификатор if user: await message.answer( f"Ваш профиль:\nEmail: {user.email}" ) return 

    if user:
        dt = datetime.fromisoformat(f"{user.createdAt}".replace("Z", "+00:00"))

        await message.answer_photo(f"{user.avatar}", caption=f"""
<b> 💁🏻‍♀️ Ваш профиль </b>
                                   
🔹 Имя: {user.firstName}
🔹 Фамилия: {user.lastName}
🔹 Почта: {user.email}
🖥 Дата поступления: <tg-spoiler>{dt.strftime("%d %B %Y")}</tg-spoiler>

📞 Номер: <tg-spoiler>{user.phoneNumber}</tg-spoiler>
🎲 Роль: <b>{'Студент' if user.role else 'Преподаватель'}</b>

""", parse_mode="HTML", reply_markup=buttons_account())
        
    else:
        await message.answer(
    """
    Приветствую тебя, дорогой студент ITHub'a
    Я - бот, который поможет тебе с раписаниями, графикой и прочее!
    Нажмите далее чтобы продолжить.""", reply_markup=start_command()
        )

@starter.callback_query(lambda c: c.data == "start")
async def enter_information(call: CallbackQuery, state: FSMContext):


    await call.answer(show_alert=True)
    await call.message.answer("Отлично!\nОтправьте мне данные от LXP!\nПример - \nMaga@magas.ithub.ru\nLox123")
    await state.set_state(LoginForm.data)

@starter.message(LoginForm.data)
async def process_form(message: Message, state: FSMContext):
    data = message.text.split()

    if len(data) != 2:
        await message.answer("Некорректный формат. Введите:\nemail password")
        return

    email, password = data

    user = User.get_or_none(telegram_id=message.from_user.id)


    if login_data(email, password):
        # пользователя нет — создаём
        user = await User.create(
            email=email,
            password=password,
            telegram_id=message.from_user.id
        )

        await add_to_data(email, password, message.from_user.id)

        await message.answer("Аккаунт создан! Вы вошли")
    elif user:
        # пользователь есть и пароль верный
        await message.answer("С возвращением! Вы вошли в аккаунт")

    else:
        await message.answer("Данные неверны! Проверьте еще раз.")
    await state.clear()
