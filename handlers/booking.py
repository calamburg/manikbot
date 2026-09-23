from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from datetime import date

from config import ADMIN_ID, CHANNEL_ID

from database import (
    get_work_days,
    get_free_slots,
    get_user_booking,
    create_booking,
    cancel_booking
)

from calendar_keyboard import build_calendar

from keyboards import (
    confirm_booking_keyboard,
    cancel_my_booking_keyboard,
    main_menu_keyboard,
    service_keyboard
)

from scheduler import (
    schedule_reminder,
    remove_reminder
)

from utils import (
    format_date,
    validate_phone
)


router = Router()



# =========================================================
# КЛАВІАТУРА ЧАСУ
# =========================================================

def slots_keyboard(
    slots,
    work_date: str
):
    """
    Створює клавіатуру з вільними часовими слотами.
    """

    buttons = []

    for slot in slots:

        buttons.append([
            InlineKeyboardButton(
                text=f"🕐 {slot['slot_time']}",
                callback_data=(
                    f"slot:{work_date}:{slot['slot_time']}"
                )
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ До вибору дати",
            callback_data="back_to_calendar"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# =========================================================
# FSM
# =========================================================

class BookingStates(StatesGroup):

    waiting_service = State()
    waiting_name = State()
    waiting_phone = State()
    waiting_confirmation = State()


# =========================================================
# ПОЧАТОК ЗАПИСУ
# =========================================================

@router.callback_query(F.data == "booking_start")
async def booking_start(
    callback: CallbackQuery,
    state: FSMContext
):

    # Перевіряємо, чи вже є активний запис
    existing = await get_user_booking(
        callback.from_user.id
    )

    if existing:

        await callback.message.edit_text(
            (
                "⚠️ <b>У вас вже є активний запис.</b>\n\n"
                f"💅 Послуга: <b>{existing['service']}</b>\n"
                f"📅 {format_date(existing['work_date'])}\n"
                f"🕐 {existing['slot_time']}\n"
                f"👤 {existing['name']}\n\n"
                "Спочатку скасуйте поточний запис."
            ),
            reply_markup=cancel_my_booking_keyboard(
                existing["id"]
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    # Очищаємо старий стан перед новим записом
    await state.clear()

    # Переходимо до введення послуги
    await state.set_state(
        BookingStates.waiting_service
    )

    await callback.message.edit_text(
        (
            "💅 <b>Введіть назву послуги</b>\n\n"
            "Наприклад:\n"
            "• Комбінований манікюр\n"
            "• Манікюр з покриттям\n"
            "• Нарощування нігтів"
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ВИБІР ПОСЛУГИ
# =========================================================

@router.message(BookingStates.waiting_service)
async def enter_service(
    message: Message,
    state: FSMContext
):
    service = message.text.strip()

    if not service:
        await message.answer(
            "❌ Будь ласка, напишіть назву послуги."
        )
        return

    # Зберігаємо послугу у FSM
    await state.update_data(
        service=service
    )

    # Отримуємо доступні робочі дні
    work_days = await get_work_days()

    available_dates = {
        day["work_date"]
        for day in work_days
        if not day["is_closed"]
    }

    today = date.today()

    await message.answer(
        (
            "📅 <b>Оберіть дату</b>\n\n"
            f"💅 Послуга: <b>{service}</b>\n\n"
            "Доступні дні позначені без ❌."
        ),
        reply_markup=build_calendar(
            today.year,
            today.month,
            available_dates
        ),
        parse_mode="HTML"
    )

# =========================================================
# КАЛЕНДАР
# =========================================================

@router.callback_query(F.data.startswith("calendar:"))
async def change_calendar(
    callback: CallbackQuery
):

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
        reply_markup=build_calendar(
            year,
            month,
            available_dates
        )
    )

    await callback.answer()

# =========================================================
# НАЗАД ДО ВВЕДЕННЯ ПОСЛУГИ
# =========================================================

@router.callback_query(F.data == "back_to_services")
async def back_to_services(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.set_state(
        BookingStates.waiting_service
    )

    await callback.message.edit_text(
        (
            "💅 <b>Введіть назву послуги</b>\n\n"
            "Напишіть назву послуги повідомленням."
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ВИБІР ДАТИ
# =========================================================

@router.callback_query(F.data.startswith("date:"))
async def select_date(
    callback: CallbackQuery,
    state: FSMContext
):

    work_date = callback.data.split(
        ":",
        1
    )[1]

    # Перевіряємо, чи є вільний час
    slots = await get_free_slots(
        work_date
    )

    if not slots:

        await callback.answer(
            "На цей день немає вільного часу.",
            show_alert=True
        )
        return

    # Отримуємо дані з FSM
    data = await state.get_data()

    service = data.get("service")

    if not service:

        await callback.answer(
            "❌ Не вдалося визначити послугу.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        (
            "🕐 <b>Оберіть час</b>\n\n"
            f"💅 Послуга: <b>{service}</b>\n"
            f"📅 Дата: <b>{format_date(work_date)}</b>"
        ),
        reply_markup=slots_keyboard(
            slots,
            work_date
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# НАЗАД ДО КАЛЕНДАРЯ
# =========================================================

@router.callback_query(
    F.data == "back_to_calendar"
)
async def back_to_calendar(
    callback: CallbackQuery,
    state: FSMContext
):

    data = await state.get_data()

    service = data.get(
        "service",
        "Не вказано"
    )

    work_days = await get_work_days()

    available_dates = {
        day["work_date"]
        for day in work_days
        if not day["is_closed"]
    }

    today = date.today()

    await callback.message.edit_text(
        (
            "📅 <b>Оберіть дату</b>\n\n"
            f"💅 Послуга: <b>{service}</b>"
        ),
        reply_markup=build_calendar(
            today.year,
            today.month,
            available_dates
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ВИБІР ЧАСУ
# =========================================================

@router.callback_query(F.data.startswith("slot:"))
async def select_slot(
    callback: CallbackQuery,
    state: FSMContext
):

    _, work_date, slot_time = callback.data.split(
        ":",
        2
    )

    # Повторно перевіряємо, що слот ще вільний
    slots = await get_free_slots(
        work_date
    )

    available_times = {
        slot["slot_time"]
        for slot in slots
    }

    if slot_time not in available_times:

        await callback.answer(
            "Цей час вже зайнятий.",
            show_alert=True
        )
        return

    data = await state.get_data()

    service = data.get(
        "service"
    )

    if not service:

        await callback.answer(
            "❌ Не вибрана послуга.",
            show_alert=True
        )
        return

    # Зберігаємо дату та час
    await state.update_data(
        work_date=work_date,
        slot_time=slot_time
    )

    await state.set_state(
        BookingStates.waiting_name
    )

    await callback.message.edit_text(
        (
            "👤 <b>Введіть ваше ім'я</b>\n\n"
            f"💅 Послуга: <b>{service}</b>\n"
            f"📅 {format_date(work_date)}\n"
            f"🕐 {slot_time}"
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ІМ'Я
# =========================================================

@router.message(
    BookingStates.waiting_name
)
async def enter_name(
    message: Message,
    state: FSMContext
):

    name = message.text.strip()

    if len(name) < 2:

        await message.answer(
            "❌ Ім'я занадто коротке.\n\n"
            "Будь ласка, введіть ваше ім'я."
        )

        return

    await state.update_data(
        name=name
    )

    await state.set_state(
        BookingStates.waiting_phone
    )

    await message.answer(
        (
            "📱 <b>Введіть номер телефону</b>\n\n"
            "Наприклад:\n"
            "<code>+380991234567</code>"
        ),
        parse_mode="HTML"
    )


# =========================================================
# ТЕЛЕФОН
# =========================================================

@router.message(
    BookingStates.waiting_phone
)
async def enter_phone(
    message: Message,
    state: FSMContext
):

    phone = message.text.strip()

    if not validate_phone(phone):

        await message.answer(
            "❌ Невірний формат номера.\n\n"
            "Спробуйте ще раз."
        )

        return

    await state.update_data(
        phone=phone
    )

    data = await state.get_data()

    await state.set_state(
        BookingStates.waiting_confirmation
    )

    await message.answer(
        (
            "📋 <b>Перевірте дані запису</b>\n\n"
            f"💅 Послуга: <b>{data['service']}</b>\n"
            f"👤 Ім'я: <b>{data['name']}</b>\n"
            f"📱 Телефон: <b>{data['phone']}</b>\n"
            f"📅 Дата: <b>{format_date(data['work_date'])}</b>\n"
            f"🕐 Час: <b>{data['slot_time']}</b>\n\n"
            "Все правильно?"
        ),
        reply_markup=confirm_booking_keyboard(),
        parse_mode="HTML"
    )


# =========================================================
# ПІДТВЕРДЖЕННЯ
# =========================================================

@router.callback_query(
    BookingStates.waiting_confirmation,
    F.data == "booking_confirm"
)
async def confirm_booking(
    callback: CallbackQuery,
    state: FSMContext
):

    data = await state.get_data()

    success, result = await create_booking(
        user_id=callback.from_user.id,
        name=data["name"],
        phone=data["phone"],
        service=data["service"],
        work_date=data["work_date"],
        slot_time=data["slot_time"]
    )

    if not success:

        await state.clear()

        messages = {
            "already_booked":
                "⚠️ У вас вже є активний запис.",

            "day_not_available":
                "❌ Цей день більше недоступний.",

            "day_closed":
                "❌ Цей день закритий.",

            "slot_not_found":
                "❌ Такий час більше недоступний.",

            "slot_taken":
                "❌ На жаль, цей час щойно забронювали."
        }

        await callback.message.edit_text(
            messages.get(
                result,
                "❌ Не вдалося створити запис."
            ),
            reply_markup=main_menu_keyboard(
                callback.from_user.id == ADMIN_ID
            )
        )

        await callback.answer()
        return

    # Отримуємо створений запис
    booking = await get_user_booking(
        callback.from_user.id
    )

    # Плануємо нагадування
    schedule_reminder(
        bot=callback.bot,
        booking_id=booking["id"],
        work_date=booking["work_date"],
        slot_time=booking["slot_time"]
    )

    await state.clear()

    # Повідомлення клієнту
    await callback.message.edit_text(
        (
            "✅ <b>Запис успішно створено!</b>\n\n"
            f"💅 Послуга: <b>{booking['service']}</b>\n"
            f"👤 {booking['name']}\n"
            f"📱 {booking['phone']}\n"
            f"📅 {format_date(booking['work_date'])}\n"
            f"🕐 {booking['slot_time']}\n\n"
            "Чекаємо на вас ❤️"
        ),
        reply_markup=main_menu_keyboard(
            callback.from_user.id == ADMIN_ID
        ),
        parse_mode="HTML"
    )

    # Повідомлення адміністратору
    await callback.bot.send_message(
        ADMIN_ID,
        (
            "🔔 <b>НОВИЙ ЗАПИС</b>\n\n"
            f"💅 Послуга: <b>{booking['service']}</b>\n"
            f"👤 Клієнт: <b>{booking['name']}</b>\n"
            f"📱 Телефон: <b>{booking['phone']}</b>\n"
            f"📅 Дата: <b>{format_date(booking['work_date'])}</b>\n"
            f"🕐 Час: <b>{booking['slot_time']}</b>\n"
            f"🆔 Telegram ID: <code>{booking['user_id']}</code>"
        ),
        parse_mode="HTML"
    )

    # Оновлення розкладу в каналі
    await send_channel_schedule(
        callback.bot,
        booking["work_date"]
    )

    await callback.answer()


# =========================================================
# СКАСУВАННЯ ПІДТВЕРДЖЕННЯ
# =========================================================

@router.callback_query(
    BookingStates.waiting_confirmation,
    F.data == "booking_cancel"
)
async def cancel_booking_process(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.clear()

    await callback.message.edit_text(
        "❌ Запис скасовано.",
        reply_markup=main_menu_keyboard(
            callback.from_user.id == ADMIN_ID
        )
    )

    await callback.answer()


# =========================================================
# МІЙ ЗАПИС
# =========================================================

@router.callback_query(
    F.data == "my_booking"
)
async def my_booking(
    callback: CallbackQuery
):

    booking = await get_user_booking(
        callback.from_user.id
    )

    if not booking:

        await callback.message.edit_text(
            (
                "📭 <b>У вас немає активних записів.</b>\n\n"
                "Оберіть дату та час, щоб записатися."
            ),
            reply_markup=main_menu_keyboard(
                callback.from_user.id == ADMIN_ID
            ),
            parse_mode="HTML"
        )

        await callback.answer()
        return

    await callback.message.edit_text(
        (
            "📋 <b>Ваш запис</b>\n\n"
            f"💅 Послуга: <b>{booking['service']}</b>\n"
            f"👤 {booking['name']}\n"
            f"📱 {booking['phone']}\n"
            f"📅 {format_date(booking['work_date'])}\n"
            f"🕐 {booking['slot_time']}"
        ),
        reply_markup=cancel_my_booking_keyboard(
            booking["id"]
        ),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# СКАСУВАННЯ КЛІЄНТОМ
# =========================================================

@router.callback_query(
    F.data.startswith("user_cancel:")
)
async def user_cancel_booking(
    callback: CallbackQuery
):

    booking_id = int(
        callback.data.split(":")[1]
    )

    booking = await get_user_booking(
        callback.from_user.id
    )

    if not booking or booking["id"] != booking_id:

        await callback.answer(
            "Цей запис вам не належить.",
            show_alert=True
        )

        return

    cancelled = await cancel_booking(
        booking_id
    )

    if cancelled:

        # Видаляємо нагадування
        remove_reminder(
            booking_id
        )

        await callback.message.edit_text(
            (
                "✅ <b>Ваш запис скасовано.</b>\n\n"
                f"💅 Послуга: <b>{cancelled['service']}</b>\n"
                f"📅 {format_date(cancelled['work_date'])}\n"
                f"🕐 {cancelled['slot_time']}\n\n"
                "Цей час знову доступний для запису."
            ),
            reply_markup=main_menu_keyboard(
                callback.from_user.id == ADMIN_ID
            ),
            parse_mode="HTML"
        )

        # Повідомлення адміністратору
        await callback.bot.send_message(
            ADMIN_ID,
            (
                "❌ <b>КЛІЄНТ СКАСУВАВ ЗАПИС</b>\n\n"
                f"💅 Послуга: <b>{cancelled['service']}</b>\n"
                f"👤 {cancelled['name']}\n"
                f"📱 {cancelled['phone']}\n"
                f"📅 {format_date(cancelled['work_date'])}\n"
                f"🕐 {cancelled['slot_time']}"
            ),
            parse_mode="HTML"
        )

        # Оновлюємо канал
        await send_channel_schedule(
            callback.bot,
            cancelled["work_date"]
        )

    await callback.answer()


# =========================================================
# КАНАЛ
# =========================================================

async def send_channel_schedule(
    bot,
    work_date: str
):
    """
    Формує розклад певного дня
    та надсилає його в канал.
    """

    from database import get_slots_for_date

    slots = await get_slots_for_date(
        work_date
    )

    lines = []

    for slot in slots:

        if slot["booking_id"]:
            status = "🔴 Зайнято"
        else:
            status = "🟢 Вільно"

        lines.append(
            f"🕐 <b>{slot['slot_time']}</b> — {status}"
        )

    if not lines:

        text = (
            f"📅 <b>Розклад на "
            f"{format_date(work_date)}</b>\n\n"
            "Слотів немає."
        )

    else:

        text = (
            f"📅 <b>Розклад на "
            f"{format_date(work_date)}</b>\n\n"
            + "\n".join)

