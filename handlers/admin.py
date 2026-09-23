from datetime import datetime, date


from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from calendar_keyboard import build_admin_delete_slot_calendar, build_admin_open_day_calendar
from calendar_keyboard import build_admin_slot_calendar, build_admin_schedule_calendar
from calendar_keyboard import build_admin_calendar, build_admin_close_day_calendar
from config import ID

from database import (
    add_work_day,
    add_slot,
    delete_slot,
    close_work_day,
    reopen_work_day,
    get_work_day,
    get_slots_for_date,
    get_bookings_for_date,
    cancel_booking,
    get_work_days
)

from scheduler import remove_reminder
from utils import format_date


router = Router()

def is_admin(user_id: int) -> bool:


    return user_id == ID

class AdminStates(StatesGroup):

    waiting_work_day = State()
    waiting_slot_date = State()
    waiting_slot_time = State()
    waiting_delete_slot_date = State()
    waiting_close_date = State()
    waiting_open_date = State()
    waiting_schedule_date = State()

def admin_panel_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 Додати робочий день",
                    callback_data="admin:add_day"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ Додати часовий слот",
                    callback_data="admin:add_slot"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Видалити часовий слот",
                    callback_data="admin:delete_slot"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔒 Закрити день",
                    callback_data="admin:close_day"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔓 Відкрити день",
                    callback_data="admin:open_day"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Переглянути розклад",
                    callback_data="admin:view_schedule"
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

@router.callback_query(F.data == "admin_panel")
async def open_admin_panel(
    callback: CallbackQuery,
    state: FSMContext
):

    # Перевірка доступу
    if not is_admin(callback.from_user.id):

        await callback.answer(
            "⛔ У вас немає доступу до адмін-панелі.",
            show_alert=True
        )

        return


    await state.clear()

    await callback.message.edit_text(
        (
            "⚙️ <b>АДМІН-ПАНЕЛЬ</b>\n\n"
            "Оберіть потрібну дію:"
        ),
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(F.data == "admin:cancel")
async def cancel_admin_action(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin(callback.from_user.id):
        return

    await state.clear()

    await callback.message.edit_text(
        (
            "⚙️ <b>АДМІН-ПАНЕЛЬ</b>\n\n"
            "Оберіть потрібну дію:"
        ),
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


def admin_cancel_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Скасувати",
                    callback_data="admin:cancel"
                )
            ]
        ]
    )

@router.callback_query(F.data == "admin:add_day")
async def start_add_work_day(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin(callback.from_user.id):
        return

    today = date.today()

    await callback.message.edit_text(
        "📅 <b>Оберіть дату для робочого дня:</b>",
        reply_markup=build_admin_calendar(
            today.year,
            today.month
        ),
        parse_mode="HTML"
    )


    await callback.answer()

@router.callback_query(F.data.startswith("admin_workday:"))
async def select_admin_workday(
    callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    date_text = callback.data.split(":", 1)[1]
    work_day = await get_work_day(date_text)
    if work_day:
        await callback.answer(
            "⚠️ Цей день уже доданий як робочий.",
            show_alert=True
        )
        return
    await add_work_day(date_text)
    await state.clear()
    await callback.message.edit_text(
            text="✅ Робочий день додано!",
            reply_markup=admin_panel_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin:add_slot")
async def start_add_slot(
    callback: CallbackQuery,
    state: FSMContext
):
    if not is_admin(callback.from_user.id):
        return

    work_days = await get_work_days()

    available_dates = {
        day["work_date"]
        for day in work_days
        if not day["is_closed"]
    }

    today = date.today()

    await state.clear()

    await callback.message.edit_text(
        "📅 <b>Оберіть робочий день:</b>",
        reply_markup=build_admin_slot_calendar(
            today.year,
            today.month,
            available_dates
        ),
        parse_mode="HTML"
    )

    await callback.answer()


@router.message(AdminStates.waiting_slot_date)
async def get_slot_date(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    date_text = message.text.strip()

    try:

        selected_date = datetime.strptime(
            date_text,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        await message.answer(
            (
                "❌ Неправильний формат.\n\n"
                "Приклад:\n"
                "<code>2026-09-25</code>"
            ),
            reply_markup=admin_cancel_keyboard(),
            parse_mode="HTML"
        )

        return


    work_day = await get_work_day(
        selected_date.isoformat()
    )

    if not work_day:

        await message.answer(
            (
                "❌ <b>Цей день ще не доданий як робочий.</b>\n\n"
                "Спочатку скористайтеся пунктом "
                "«Додати робочий день»."
            ),
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )

        await state.clear()

        return

    if work_day["is_closed"]:

        await message.answer(
            (
                "🔒 <b>Цей день закритий.</b>\n\n"
                "Спочатку відкрийте його."
            ),
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )

        await state.clear()

        return

    await state.update_data(
        slot_date=selected_date.isoformat()
    )

    await state.set_state(
        AdminStates.waiting_slot_time
    )

    await message.answer(
        (
            "🕐 <b>Тепер введіть час.</b>\n\n"
            "Формат:\n"
            "<code>10:00</code>\n\n"
            "Наприклад:\n"
            "<code>10:00</code>\n"
            "<code>11:30</code>\n"
            "<code>14:00</code>"
        ),
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_slot_time)
async def save_slot(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    time_text = message.text.strip()

    # Перевіряємо час
    try:

        datetime.strptime(
            time_text,
            "%H:%M"
        )

    except ValueError:

        await message.answer(
            (
                "❌ <b>Неправильний формат часу.</b>\n\n"
                "Використовуйте:\n"
                "<code>10:00</code>"
            ),
            reply_markup=admin_cancel_keyboard(),
            parse_mode="HTML"
        )

        return

    data = await state.get_data()

    slot_date = data["slot_date"]

    await add_slot(
        slot_date,
        time_text
    )

    await state.clear()

    await message.answer(
        (
            "✅ <b>Часовий слот додано!</b>\n\n"
            f"📅 Дата: <b>{format_date(slot_date)}</b>\n"
            f"🕐 Час: <b>{time_text}</b>"
        ),
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin:delete_slot")
async def start_delete_slot(
    callback: CallbackQuery,
    state: FSMContext
):
    if not is_admin(callback.from_user.id):
        return

    work_days = await get_work_days()

    available_dates = {
        day["work_date"]
        for day in work_days
        if not day["is_closed"]
    }

    today = date.today()

    await state.clear()

    await callback.message.edit_text(
        "➖ <b>Оберіть день, з якого потрібно видалити часовий слот:</b>",
        reply_markup=build_admin_delete_slot_calendar(
            today.year,
            today.month,
            available_dates
        ),
        parse_mode="HTML"
    )

    await callback.answer()

@router.message(AdminStates.waiting_delete_slot_date)
async def show_slots_for_delete(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    date_text = message.text.strip()

    try:

        datetime.strptime(
            date_text,
            "%Y-%m-%d"
        )

    except ValueError:

        await message.answer(
            (
                "❌ Неправильний формат дати.\n\n"
                "<code>2026-09-25</code>"
            ),
            reply_markup=admin_cancel_keyboard(),
            parse_mode="HTML"
        )

        return

    slots = await get_slots_for_date(
        date_text
    )

    if not slots:

        await state.clear()

        await message.answer(
            (
                "📭 <b>На цей день немає слотів.</b>"
            ),
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )

        return

    buttons = []

    for slot in slots:


        if slot["booking_id"]:

            buttons.append([
                InlineKeyboardButton(
                    text=f"🔴 {slot['slot_time']} — зайнято",
                    callback_data="admin:ignore"
                )
            ])

        else:

            buttons.append([
                InlineKeyboardButton(
                    text=f"🗑 {slot['slot_time']}",
                    callback_data=f"admin:delete_slot:{slot['id']}"
                )
            ])

    buttons.append([
        InlineKeyboardButton(
            text="❌ Скасувати",
            callback_data="admin:cancel"
        )
    ])

    await state.clear()

    await message.answer(
        (
            f"📅 <b>Слоти на {format_date(date_text)}</b>\n\n"
            "🟢 Вільний слот — можна видалити.\n"
            "🔴 Зайнятий — спочатку скасуйте запис."
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin:delete_slot:"))
async def confirm_delete_slot(
    callback: CallbackQuery
):

    if not is_admin(callback.from_user.id):
        return

    slot_id = int(
        callback.data.split(":")[2]
    )

    await delete_slot(
        slot_id
    )

    await callback.message.edit_text(
        (
            "✅ <b>Часовий слот видалено.</b>\n\n"
            "Ви можете повернутися до адмін-панелі."
        ),
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer(
        "Слот видалено."
    )

@router.callback_query(F.data == "admin:close_day")
async def start_close_day(
    callback: CallbackQuery,
    state: FSMContext
):
    if not is_admin(callback.from_user.id):
        return

    work_days = await get_work_days()

    available_dates = {
        day["work_date"]
        for day in work_days
        if not day["is_closed"]
    }

    today = date.today()

    await state.clear()

    await callback.message.edit_text(
        "🔒 <b>Оберіть день, який потрібно закрити:</b>",
        reply_markup=build_admin_close_day_calendar(
            today.year,
            today.month,
            available_dates
        ),
        parse_mode="HTML"
    )

    await callback.answer()


@router.callback_query(
    F.data.startswith("admin_schedule_date:")
)
async def select_schedule_date(
    callback: CallbackQuery
):
    if not is_admin(callback.from_user.id):
        return

    date_text = callback.data.split(":", 1)[1]

    work_day = await get_work_day(date_text)

    if not work_day:
        await callback.answer(
            "❌ Цей день не є робочим.",
            show_alert=True
        )
        return

    slots = await get_slots_for_date(date_text)
    bookings = await get_bookings_for_date(date_text)

    booking_by_time = {
        booking["slot_time"]: booking
        for booking in bookings
    }

    lines = [
        "📋 <b>Розклад</b>",
        "",
        f"📅 <b>{format_date(date_text)}</b>",
        ""
    ]

    if work_day["is_closed"]:
        lines.append("🔒 <b>День закритий</b>")
        lines.append("")

    if not slots:
        lines.append("Часових слотів немає.")
    else:
        for slot in slots:
            slot_time = slot["slot_time"]

            booking = booking_by_time.get(slot_time)

            if booking:
                lines.append(
                    f"🔴 <b>{slot_time}</b> — "
                    f"{booking['name']} "
                    f"({booking['phone']})"
                )
                lines.append(
                    f"   💅 {booking['service']}"
                )
            else:
                lines.append(
                    f"🟢 <b>{slot_time}</b> — вільно"
                )

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("admin_close_date:")
)
async def select_close_day(
    callback: CallbackQuery,
    state: FSMContext
):
    if not is_admin(callback.from_user.id):
        return

    date_text = callback.data.split(":", 1)[1]

    work_day = await get_work_day(date_text)

    if not work_day:
        await callback.answer(
            "❌ Цей день не є робочим.",
            show_alert=True
        )
        return

    if work_day["is_closed"]:
        await callback.answer(
            "⚠️ Цей день уже закритий.",
            show_alert=True
        )
        return

    await close_work_day(date_text)

    await state.clear()

    await callback.message.edit_text(
        (
            "🔒 <b>День повністю закрито.</b>\n\n"
            f"📅 {format_date(date_text)}\n\n"
            "Нові клієнти не зможуть записатися "
            "на цей день."
        ),
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(F.data == "admin:open_day")
async def start_open_day(
    callback: CallbackQuery,
    state: FSMContext
):
    if not is_admin(callback.from_user.id):
        return

    work_days = await get_work_days()

    available_dates = {
        day["work_date"]
        for day in work_days
        if day["is_closed"]
    }

    today = date.today()

    await state.clear()

    await callback.message.edit_text(
        "🔓 <b>Оберіть день, який потрібно відкрити:</b>",
        reply_markup=build_admin_open_day_calendar(
            today.year,
            today.month,
            available_dates
        ),
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("admin_open_date:")
)
async def select_open_day(
    callback: CallbackQuery,
    state: FSMContext
):
    if not is_admin(callback.from_user.id):
        return

    date_text = callback.data.split(":", 1)[1]

    work_day = await get_work_day(date_text)

    if not work_day:
        await callback.answer(
            "❌ Цей день не є робочим.",
            show_alert=True
        )
        return

    if not work_day["is_closed"]:
        await callback.answer(
            "⚠️ Цей день уже відкритий.",
            show_alert=True
        )
        return

    await reopen_work_day(date_text)

    await state.clear()

    await callback.message.edit_text(
        (
            "🔓 <b>День відкрито!</b>\n\n"
            f"📅 Дата: <b>{format_date(date_text)}</b>"
        ),
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("admin_open_calendar:")
)
async def change_open_day_calendar(
    callback: CallbackQuery
):
    if not is_admin(callback.from_user.id):
        return

    _, year, month = callback.data.split(":")

    year = int(year)
    month = int(month)

    work_days = await get_work_days()

    available_dates = {
        day["work_date"]
        for day in work_days
        if day["is_closed"]
    }

    await callback.message.edit_reply_markup(
        reply_markup=build_admin_open_day_calendar(
            year,
            month,
            available_dates
        )
    )

    await callback.answer()

@router.message(AdminStates.waiting_open_date)
async def open_day(
    message: Message,
    state: FSMContext
):

    if not is_admin(message.from_user.id):
        return

    date_text = message.text.strip()

    try:

        datetime.strptime(
            date_text,
            "%Y-%m-%d"
        )

    except ValueError:

        await message.answer(
            "❌ Неправильний формат дати.",
            reply_markup=admin_cancel_keyboard()
        )

        return

    work_day = await get_work_day(
        date_text
    )

    if not work_day:

        await state.clear()

        await message.answer(
            (
                "❌ <b>Такого робочого дня немає.</b>"
            ),
            reply_markup=admin_panel_keyboard(),
            parse_mode="HTML"
        )

        return

    await reopen_work_day(
        date_text
    )

    await state.clear()

    await message.answer(
        (
            "🔓 <b>День знову відкрито.</b>\n\n"
            f"📅 {format_date(date_text)}\n\n"
            "Клієнти знову зможуть бачити "
            "цей день, якщо на ньому є вільні слоти."
        ),
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin:view_schedule")
async def start_view_schedule(
    callback: CallbackQuery,
    state: FSMContext
):
    if not is_admin(callback.from_user.id):
        return

    work_days = await get_work_days()

    available_dates = {
        day["work_date"]
        for day in work_days
    }

    today = date.today()

    await state.clear()

    await callback.message.edit_text(
        "📋 <b>Оберіть день для перегляду розкладу:</b>",
        reply_markup=build_admin_schedule_calendar(
            today.year,
            today.month,
            available_dates
        ),
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("admin_schedule_date:")
)
async def select_schedule_date(
    callback: CallbackQuery
):
    if not is_admin(callback.from_user.id):
        return

    date_text = callback.data.split(":", 1)[1]

    work_day = await get_work_day(date_text)

    if not work_day:
        await callback.answer(
            "❌ Цей день не є робочим.",
            show_alert=True
        )
        return

    slots = await get_slots_for_date(date_text)
    bookings = await get_bookings_for_date(date_text)

    booking_by_time = {
        booking["slot_time"]: booking
        for booking in bookings
    }

    lines = [
        "📋 <b>Розклад</b>",
        "",
        f"📅 <b>{format_date(date_text)}</b>",
        ""
    ]

    if work_day["is_closed"]:
        lines.append("🔒 <b>День закритий</b>")
        lines.append("")

    if not slots:
        lines.append("Часових слотів немає.")
    else:
        for slot in slots:
            slot_time = slot["slot_time"]

            booking = booking_by_time.get(slot_time)

            if booking:
                lines.append(
                    f"🔴 <b>{slot_time}</b> — "
                    f"{booking['name']} "
                    f"({booking['phone']})"
                )
                lines.append(
                    f"   💅 {booking['service']}"
                )
            else:
                lines.append(
                    f"🟢 <b>{slot_time}</b> — вільно"
                )

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("admin_schedule_calendar:")
)
async def change_schedule_calendar(
    callback: CallbackQuery
):
    if not is_admin(callback.from_user.id):
        return

    _, year, month = callback.data.split(":")

    year = int(year)
    month = int(month)

    work_days = await get_work_days()

    available_dates = {
        day["work_date"]
        for day in work_days
    }

    await callback.message.edit_reply_markup(
        reply_markup=build_admin_schedule_calendar(
            year,
            month,
            available_dates
        )
    )

    await callback.answer()

@router.callback_query(F.data == "admin:ignore")
async def admin_ignore(
    callback: CallbackQuery
):

    if not is_admin(callback.from_user.id):
        return

    await callback.answer(
        "🔴 Цей слот вже зайнятий."
    )

@router.callback_query(
    F.data.startswith("admin:cancel_booking:")
)
async def admin_cancel_booking(
    callback: CallbackQuery
):

    if not is_admin(callback.from_user.id):
        return

    booking_id = int(
        callback.data.split(":")[2]
    )


    booking = await cancel_booking(
        booking_id
    )

    if not booking:

        await callback.answer(
            "❌ Цей запис вже скасований.",
            show_alert=True
        )

        return


    remove_reminder(
        booking_id
    )

    try:

        await callback.bot.send_message(
            booking["user_id"],
            (
                "⚠️ <b>Ваш запис було скасовано.</b>\n\n"
                f"💅 Послуга: <b>{booking['service']}</b>\n"
                f"📅 Дата: <b>{format_date(booking['work_date'])}</b>\n"
                f"🕐 Час: <b>{booking['slot_time']}</b>\n\n"
                "Будь ласка, оберіть інший доступний час."
            ),
            parse_mode="HTML"
        )

    except Exception as error:

        print(
            f"Не вдалося повідомити клієнта: {error}"
        )

    await callback.message.edit_text(
        (
            "✅ <b>Запис скасовано.</b>\n\n"
            f"👤 Клієнт: <b>{booking['name']}</b>\n"
            f"💅 Послуга: <b>{booking['service']}</b>\n"
            f"📱 Телефон: <b>{booking['phone']}</b>\n"
            f"📅 Дата: <b>{format_date(booking['work_date'])}</b>\n"
            f"🕐 Час: <b>{booking['slot_time']}</b>\n\n"
            "🟢 Цей час тепер знову доступний."
        ),
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer(
        "Запис скасовано."
    )

@router.callback_query(F.data.startswith("admin_slot_date:"))
async def select_admin_slot_date(
    callback: CallbackQuery,
    state: FSMContext
):
    if not is_admin(callback.from_user.id):
        return

    date_text = callback.data.split(":", 1)[1]

    work_day = await get_work_day(date_text)

    if not work_day:
        await callback.answer(
            "❌ Цей день не є робочим.",
            show_alert=True
        )
        return

    if work_day["is_closed"]:
        await callback.answer(
            "❌ Цей день закритий.",
            show_alert=True
        )
        return

    await state.update_data(
        slot_date=date_text
    )

    await state.set_state(
        AdminStates.waiting_slot_time
    )

    await callback.message.edit_text(
        (
            "🕐 <b>Додайте часовий слот</b>\n\n"
            f"📅 Дата: <b>{format_date(date_text)}</b>\n\n"
            "Введіть час у форматі:\n"
            "<code>10:00</code>"
        ),
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("admin_slot_calendar:")
)
async def change_admin_slot_calendar(
    callback: CallbackQuery
):
    if not is_admin(callback.from_user.id):
        return

    _, year, month = callback.data.split(":")

    year = int(year)
    month = int(month)

    work_days = await get_work_days()

    available_dates = {
        day["work_date"]
        for day in work_days
        if not day["is_closed"]
    }

    await callback.message.edit_reply_markup(
        reply_markup=build_admin_slot_calendar(
            year,
            month,
            available_dates
        )
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("admin_delete_slot_date:")
)
async def select_delete_slot_date(
    callback: CallbackQuery,
    state: FSMContext
):
    if not is_admin(callback.from_user.id):
        return

    date_text = callback.data.split(":", 1)[1]

    slots = await get_slots_for_date(date_text)

    if not slots:
        await callback.answer(
            "❌ На цей день немає часових слотів.",
            show_alert=True
        )
        return

    await state.update_data(
        delete_slot_date=date_text
    )

    keyboard = []

    for slot in slots:
        keyboard.append([
            InlineKeyboardButton(
                text=f"🕐 {slot['slot_time']}",
                callback_data=f"admin_delete_slot:{slot['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin:delete_slot"
        )
    ])

    await callback.message.edit_text(
        (
            "➖ <b>Оберіть часовий слот для видалення:</b>\n\n"
            f"📅 Дата: <b>{format_date(date_text)}</b>"
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("admin_delete_slot:")
)
async def confirm_delete_slot(
    callback: CallbackQuery,
    state: FSMContext
):
    if not is_admin(callback.from_user.id):
        return

    slot_id = int(
        callback.data.split(":", 1)[1]
    )

    await delete_slot(slot_id)

    await state.clear()

    await callback.message.edit_text(
        "✅ <b>Часовий слот видалено!</b>",
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("admin_delete_slot_calendar:")
)
async def change_delete_slot_calendar(
    callback: CallbackQuery
):
    if not is_admin(callback.from_user.id):
        return

    _, year, month = callback.data.split(":")

    year = int(year)
    month = int(month)

    work_days = await get_work_days()

    available_dates = {
        day["work_date"]
        for day in work_days
        if not day["is_closed"]
    }

    await callback.message.edit_reply_markup(
        reply_markup=build_admin_delete_slot_calendar(
            year,
            month,
            available_dates
        )
    )

    await callback.answer()

@router.callback_query(
    F.data.startswith("admin_schedule_calendar:")
)
async def change_schedule_calendar(
    callback: CallbackQuery
):
    if not is_admin(callback.from_user.id):
        return

    _, year, month = callback.data.split(":")

    year = int(year)
    month = int(month)

    work_days = await get_work_days()

    available_dates = {
        day["work_date"]
        for day in work_days
    }

    await callback.message.edit_reply_markup(
        reply_markup=build_admin_schedule_calendar(
            year,
            month,
            available_dates
        )
    )

    await callback.answer()


