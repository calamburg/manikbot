from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from config import ADMIN_ID, PORTFOLIO_URL

from keyboards import (
    main_menu_keyboard,
    back_menu_keyboard,
    portfolio_keyboard
)


router = Router()


@router.message(F.text == "/start")
async def start_handler(message: Message):

    is_admin = message.from_user.id == ADMIN_ID

    await message.answer(
        (
            "💅 <b>Вітаємо!</b>\n\n"
            "Тут ви можете зручно записатися "
            "на процедуру.\n\n"
            "Оберіть потрібний пункт:"
        ),
        reply_markup=main_menu_keyboard(
            is_admin=is_admin
        ),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(
    callback: CallbackQuery
):

    is_admin = callback.from_user.id == ADMIN_ID

    await callback.message.edit_text(
        (
            "💅 <b>Головне меню</b>\n\n"
            "Оберіть потрібний пункт:"
        ),
        reply_markup=main_menu_keyboard(
            is_admin=is_admin
        ),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "prices")
async def prices_handler(
    callback: CallbackQuery
):

    await callback.message.edit_text(
        (
            "💰 <b>ПРАЙС</b>\n\n"
            "🇫🇷 Френч — <b>1000₽</b>\n"
            "◼️ Квадрат — <b>500₽</b>"
        ),
        reply_markup=back_menu_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "portfolio")
async def portfolio_handler(
    callback: CallbackQuery
):

    await callback.message.edit_text(
        (
            "📸 <b>Портфоліо</b>\n\n"
            "Перегляньте мої роботи "
            "та оберіть свій улюблений дизайн 💅"
        ),
        reply_markup=portfolio_keyboard(
            PORTFOLIO_URL
        ),
        parse_mode="HTML"
    )

    await callback.answer()