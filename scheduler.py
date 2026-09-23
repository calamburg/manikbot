
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TIMEZONE

from database import (
    get_booking,
    get_all_future_bookings
)


# =========================================================
# TIMEZONE
# =========================================================

timezone = ZoneInfo(
    TIMEZONE
)


# =========================================================
# SCHEDULER
# =========================================================

scheduler = AsyncIOScheduler(
    timezone=timezone
)


# =========================================================
# ID ЗАДАЧІ
# =========================================================

def reminder_job_id(
    booking_id: int
) -> str:
    """
    Формує унікальний ID задачі.

    Наприклад:

    booking_reminder_15
    """

    return (
        f"booking_reminder_{booking_id}"
    )


# =========================================================
# ВІДПРАВКА НАГАДУВАННЯ
# =========================================================

async def send_reminder(
    bot,
    booking_id: int
):
    """
    Відправляє нагадування клієнту.

    Перед відправкою ще раз перевіряємо,
    чи існує запис у БД.

    Це захищає від ситуації:

    запис скасували,
    але стара задача scheduler
    все одно запустилася.
    """

    booking = await get_booking(
        booking_id
    )

    # Якщо запису вже немає —
    # нічого не відправляємо.
    if not booking:

        return

    try:

        await bot.send_message(
            booking["user_id"],
            (
                "🔔 <b>Нагадування про запис</b>\n\n"
                f"💅 Послуга: <b>{booking['service']}</b>\n"
                f"📅 Завтра о <b>{booking['slot_time']}</b>\n\n"
                "Чекаємо на вас ❤️"
            ),
            parse_mode="HTML"
        )

    except Exception as error:

        print(
            "❌ Помилка відправки нагадування: "
            f"{error}"
        )


# =========================================================
# ВИДАЛЕННЯ НАГАДУВАННЯ
# =========================================================

def remove_reminder(
    booking_id: int
):
    """
    Видаляє нагадування конкретного запису.

    Якщо задачі немає —
    помилку не видаємо.
    """

    job_id = reminder_job_id(
        booking_id
    )

    try:

        scheduler.remove_job(
            job_id
        )

        print(
            f"🗑 Нагадування {job_id} видалено."
        )

    except Exception:

        # Job могла вже виконатися
        # або не існувати.
        pass


# =========================================================
# СТВОРЕННЯ НАГАДУВАННЯ
# =========================================================

def schedule_reminder(
    bot,
    booking_id: int,
    work_date: str,
    slot_time: str
):
    """
    Створює нагадування рівно за 24 години
    до запису.

    Якщо до запису менше 24 годин —
    нагадування не створюється.

    Повертає:

        True  — нагадування створено

        False — нагадування не потрібно створювати
    """

    # -----------------------------------------------------
    # Формуємо дату та час запису
    # -----------------------------------------------------

    visit_datetime = datetime.strptime(
        f"{work_date} {slot_time}",
        "%Y-%m-%d %H:%M"
    )

    # Додаємо часову зону
    visit_datetime = visit_datetime.replace(
        tzinfo=timezone
    )

    # -----------------------------------------------------
    # Час нагадування
    # -----------------------------------------------------

    reminder_datetime = (
        visit_datetime
        - timedelta(hours=24)
    )

    # -----------------------------------------------------
    # Поточний час
    # -----------------------------------------------------

    now = datetime.now(
        timezone
    )

    # -----------------------------------------------------
    # Якщо запис вже минув
    # -----------------------------------------------------

    if visit_datetime <= now:

        return False

    # -----------------------------------------------------
    # Якщо до запису менше 24 годин
    # -----------------------------------------------------

    if reminder_datetime <= now:

        print(
            (
                f"ℹ️ Нагадування для запису "
                f"{booking_id} не створено: "
                "до візиту менше 24 годин."
            )
        )

        return False

    # -----------------------------------------------------
    # Якщо стара задача існує —
    # видаляємо її
    # -----------------------------------------------------

    remove_reminder(
        booking_id
    )

    # -----------------------------------------------------
    # Створюємо нову задачу
    # -----------------------------------------------------

    scheduler.add_job(
        send_reminder,

        trigger="date",

        run_date=reminder_datetime,

        args=[
            bot,
            booking_id
        ],

        id=reminder_job_id(
            booking_id
        ),

        replace_existing=True
    )

    print(
        (
            f"⏰ Нагадування створено.\n"
            f"Запис: {booking_id}\n"
            f"Нагадування: "
            f"{reminder_datetime}"
        )
    )

    return True


# =========================================================
# ВІДНОВЛЕННЯ НАГАДУВАНЬ
# =========================================================

async def restore_reminders(
    bot
):
    """
    Відновлює нагадування після перезапуску бота.

    SQLite є основним джерелом даних.

    APScheduler після перезапуску порожній,
    тому ми читаємо записи з БД
    і створюємо jobs заново.
    """

    print(
        "🔄 Відновлення нагадувань..."
    )

    bookings = await get_all_future_bookings()

    restored_count = 0

    for booking in bookings:

        created = schedule_reminder(
            bot=bot,

            booking_id=booking["id"],

            work_date=booking["work_date"],

            slot_time=booking["slot_time"]
        )

        if created:

            restored_count += 1

    print(
        (
            "✅ Відновлення завершено. "
            f"Створено нагадувань: "
            f"{restored_count}"
        )
    )
