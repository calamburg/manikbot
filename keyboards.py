from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard(is_admin: bool = False):
    buttons = [
        [
            InlineKeyboardButton(
                text="📅 Записатися",
                callback_data="booking_start"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Мій запис",
                callback_data="my_booking"
            )
        ],
        [
            InlineKeyboardButton(
                text="💰 Прайси",
                callback_data="prices"
            ),
            InlineKeyboardButton(
                text="📸 Портфоліо",
                callback_data="portfolio"
            )
        ]
    ]

    if is_admin:
        buttons.append([
            InlineKeyboardButton(
                text="⚙️ Адмін-панель",
                callback_data="admin_panel"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def service_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💅 Френч",
                    callback_data="service:french"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◼️ Квадрат",
                    callback_data="service:square"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Головне меню",
                    callback_data="main_menu"
                )
            ]
        ]
    )

def back_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Головне меню",
                    callback_data="main_menu"
                )
            ]
        ]
    )


def confirm_booking_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Підтвердити",
                    callback_data="booking_confirm"
                ),
                InlineKeyboardButton(
                    text="❌ Скасувати",
                    callback_data="booking_cancel"
                )
            ]
        ]
    )


def cancel_my_booking_keyboard(booking_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Скасувати запис",
                    callback_data=f"user_cancel:{booking_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Меню",
                    callback_data="main_menu"
                )
            ]
        ]
    )


def portfolio_keyboard(url: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📸 Дивитися портфоліо",
                    url=url
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Меню",
                    callback_data="main_menu"
                )
            ]
        ]
    )