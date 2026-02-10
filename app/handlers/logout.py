# deativate.py - модуль, который выходит с аккаунта
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram import Router, F
from db.models import User

# Спрашиваем юзера, действительно ли он хочет выйти с аккаунта
leave = Router()

@leave.callback_query(F.data == "logout")
async def leave_acc(call: CallbackQuery):
    await call.answer(show_alert=True)
    await call.message.delete()
    await call.message.answer(
        "<b>Вы действительно хотите выйти с аккаунта?</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Да", callback_data="Yes"),
                    InlineKeyboardButton(text="❌ Нет, я остаюсь", callback_data="No")
                ]
            ]
        )
    )
@leave.callback_query(F.data=="Yes")
async def leave_acc(call: CallbackQuery):
    await call.answer(show_alert=True)

    user = await User.get_or_none(telegram_id=call.from_user.id)
    await user.delete()

    from keyboard.inline_kbs import start_command
    await call.message.edit_text(
        "<b> Вы вышли с аккаунта :( </b>", parse_mode="HTML", reply_markup=start_command()
    )

@leave.callback_query(F.data=="No")
async def leave_acc(call: CallbackQuery):
    await call.answer()
    from .start import show_profile
    user = await User.get_or_none(telegram_id=call.from_user.id)
    if user:
        await show_profile(call, user)
    else:
        await call.message.edit_text("<b>Вы отменили операцию.</b>", parse_mode="HTML")
