
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TIMEZONE

from database import (
    get_booking,
    get_all_future_bookings
)


timezone = ZoneInfo(
    TIMEZONE)

scheduler = AsyncIOScheduler(
    timezone=timezone)

def reminder_job_id(
    booking_id: int) -> str:

    return (
        f"booking_reminder_{booking_id}")

async def send_reminder(
    bot,
    booking_id: int):

    booking = await get_booking(
        booking_id)


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

def remove_reminder(
    booking_id: int):


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


        pass

def schedule_reminder(
    bot,
    booking_id: int,
    work_date: str,
    slot_time: str
):

    visit_datetime = datetime.strptime(
        f"{work_date} {slot_time}",
        "%Y-%m-%d %H:%M"
    )


    visit_datetime = visit_datetime.replace(
        tzinfo=timezone
    )

    reminder_datetime = (
        visit_datetime
        - timedelta(hours=24)
    )


    now = datetime.now(
        timezone
    )

    if visit_datetime <= now:

        return False

    if reminder_datetime <= now:

        print(
            (
                f"ℹ️ Нагадування для запису "
                f"{booking_id} не створено: "
                "до візиту менше 24 годин."
            )
        )

        return False


    remove_reminder(
        booking_id
    )

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

async def restore_reminders(
    bot):


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
