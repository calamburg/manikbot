import asyncio

from aiogram import (
    Bot,
    Dispatcher
)

from aiogram.fsm.storage.memory import (
    MemoryStorage
)

from config import TOKEN

from database import init_db

from scheduler import (
    scheduler,
    restore_reminders
)

from handlers.user import router as user_router
from handlers.booking import router as booking_router
from handlers.admin import router as admin_router


async def main():

    await init_db()


    bot = Bot(
        token=TOKEN
    )

    dp = Dispatcher(
        storage=MemoryStorage()
    )


    dp.include_router(
        user_router
    )

    dp.include_router(
        booking_router
    )

    dp.include_router(
        admin_router
    )

    scheduler.start()

    await restore_reminders(
        bot
    )

    print(
        "🤖 Бот запущений..."
    )

    try:

        await dp.start_polling(
            bot
        )

    finally:

        scheduler.shutdown()

        await bot.session.close()


if __name__ == "__main__":

    asyncio.run(
        main()
    )