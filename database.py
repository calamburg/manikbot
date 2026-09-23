import aiosqlite

from config import DATABASE_PATH


# =========================================================
# ПІДКЛЮЧЕННЯ ДО БАЗИ
# =========================================================

async def get_db():
    """
    Створює підключення до SQLite.

    row_factory дозволяє звертатися до колонок
    за їх назвами:

    row["work_date"]
    row["slot_time"]
    """

    db = await aiosqlite.connect(
        DATABASE_PATH
    )

    db.row_factory = aiosqlite.Row

    # Дозволяємо використання foreign keys
    await db.execute(
        "PRAGMA foreign_keys = ON"
    )

    return db


# =========================================================
# СТВОРЕННЯ ТАБЛИЦЬ
# =========================================================

async def init_db():
    """
    Створює таблиці при першому запуску бота.
    """

    db = await get_db()

    await db.executescript(
        """
        CREATE TABLE IF NOT EXISTS work_days (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            work_date TEXT NOT NULL UNIQUE,

            is_closed INTEGER NOT NULL DEFAULT 0
        );


        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            work_date TEXT NOT NULL,

            slot_time TEXT NOT NULL,

            UNIQUE(work_date, slot_time),

            FOREIGN KEY(work_date)
                REFERENCES work_days(work_date)
                ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            name TEXT NOT NULL,

            phone TEXT NOT NULL,
            
            service TEXT NOT NULL,

            work_date TEXT NOT NULL,

            slot_time TEXT NOT NULL,

            created_at TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(work_date, slot_time),

            FOREIGN KEY(work_date)
                REFERENCES work_days(work_date)
                ON DELETE CASCADE
        );


        CREATE INDEX IF NOT EXISTS idx_bookings_user_id
        ON bookings(user_id);


        CREATE INDEX IF NOT EXISTS idx_bookings_work_date
        ON bookings(work_date);
        """
    )

    await db.commit()
    await db.close()


# =========================================================
# РОБОЧІ ДНІ
# =========================================================

async def add_work_day(
    work_date: str
):
    """
    Додає робочий день.

    Якщо день вже існує —
    нічого не робить.
    """

    db = await get_db()

    await db.execute(
        """
        INSERT OR IGNORE INTO work_days (
            work_date,
            is_closed
        )
        VALUES (?, 0)
        """,
        (work_date,)
    )

    await db.commit()
    await db.close()


async def get_work_day(
    work_date: str
):
    """
    Отримує інформацію про конкретний день.
    """

    db = await get_db()

    cursor = await db.execute(
        """
        SELECT *
        FROM work_days
        WHERE work_date = ?
        """,
        (work_date,)
    )

    result = await cursor.fetchone()

    await db.close()

    return result


async def get_work_days():
    """
    Повертає всі робочі дні.
    """

    db = await get_db()

    cursor = await db.execute(
        """
        SELECT *
        FROM work_days
        ORDER BY work_date
        """
    )

    result = await cursor.fetchall()

    await db.close()

    return result


async def close_work_day(
    work_date: str
):
    """
    Повністю закриває день.

    Важливо:
    записи клієнтів НЕ видаляються.
    Просто день перестає бути доступним
    для нових записів.
    """

    db = await get_db()

    await db.execute(
        """
        UPDATE work_days
        SET is_closed = 1
        WHERE work_date = ?
        """,
        (work_date,)
    )

    await db.commit()
    await db.close()


async def reopen_work_day(
    work_date: str
):
    """
    Знову відкриває робочий день.
    """

    db = await get_db()

    await db.execute(
        """
        UPDATE work_days
        SET is_closed = 0
        WHERE work_date = ?
        """,
        (work_date,)
    )

    await db.commit()
    await db.close()


# =========================================================
# ЧАСОВІ СЛОТИ
# =========================================================

async def add_slot(
    work_date: str,
    slot_time: str
):
    """
    Додає часовий слот.

    UNIQUE(work_date, slot_time)
    не дозволить створити однаковий слот двічі.
    """

    db = await get_db()

    await db.execute(
        """
        INSERT OR IGNORE INTO slots (
            work_date,
            slot_time
        )
        VALUES (?, ?)
        """,
        (
            work_date,
            slot_time
        )
    )

    await db.commit()
    await db.close()


async def delete_slot(
    slot_id: int
):
    """
    Видаляє часовий слот.

    Адмін-панель перед цим перевіряє,
    чи не зайнятий слот.
    """

    db = await get_db()

    await db.execute(
        """
        DELETE FROM slots
        WHERE id = ?
        """,
        (slot_id,)
    )

    await db.commit()
    await db.close()


async def get_slots_for_date(
    work_date: str
):
    """
    Повертає всі слоти конкретного дня.

    Додатково повертається booking_id.

    Якщо booking_id IS NULL —
    слот вільний.

    Якщо booking_id має значення —
    слот зайнятий.
    """

    db = await get_db()

    cursor = await db.execute(
        """
        SELECT
            slots.id,
            slots.work_date,
            slots.slot_time,
            bookings.id AS booking_id

        FROM slots

        LEFT JOIN bookings
            ON bookings.work_date = slots.work_date
            AND bookings.slot_time = slots.slot_time

        WHERE slots.work_date = ?

        ORDER BY slots.slot_time
        """,
        (work_date,)
    )

    result = await cursor.fetchall()

    await db.close()

    return result


async def get_free_slots(
    work_date: str
):
    """
    Повертає тільки вільні слоти.

    Закритий день також не повинен
    віддавати слоти клієнту.
    """

    db = await get_db()

    cursor = await db.execute(
        """
        SELECT
            slots.id,
            slots.work_date,
            slots.slot_time

        FROM slots

        INNER JOIN work_days
            ON work_days.work_date = slots.work_date

        LEFT JOIN bookings
            ON bookings.work_date = slots.work_date
            AND bookings.slot_time = slots.slot_time

        WHERE slots.work_date = ?

          AND work_days.is_closed = 0

          AND bookings.id IS NULL

        ORDER BY slots.slot_time
        """,
        (work_date,)
    )

    result = await cursor.fetchall()

    await db.close()

    return result


# =========================================================
# БРОНЮВАННЯ
# =========================================================

async def user_has_booking(
    user_id: int
):
    """
    Перевіряє, чи є у користувача активний запис.
    """

    db = await get_db()

    cursor = await db.execute(
        """
        SELECT *
        FROM bookings
        WHERE user_id = ?
        LIMIT 1
        """,
        (user_id,)
    )

    result = await cursor.fetchone()

    await db.close()

    return result


async def get_user_booking(
    user_id: int
):
    """
    Повертає активний запис користувача.
    """

    return await user_has_booking(
        user_id
    )


async def get_booking(
    booking_id: int
):
    """
    Повертає запис за його ID.
    """

    db = await get_db()

    cursor = await db.execute(
        """
        SELECT *
        FROM bookings
        WHERE id = ?
        """,
        (booking_id,)
    )

    result = await cursor.fetchone()

    await db.close()

    return result


async def create_booking(
    user_id: int,
    name: str,
    phone: str,
    service: str,
    work_date: str,
    slot_time: str
):
    """
    Створює бронювання.

    Повертає:

        (True, "success")

    або:

        (False, причина)

    Використовується транзакція BEGIN IMMEDIATE,
    щоб два користувачі не змогли одночасно
    зайняти один слот.
    """

    db = await get_db()

    try:

        # -------------------------------------------------
        # Блокуємо операцію запису
        # -------------------------------------------------

        await db.execute(
            "BEGIN IMMEDIATE"
        )

        # -------------------------------------------------
        # Перевірка: користувач вже має запис?
        # -------------------------------------------------

        cursor = await db.execute(
            """
            SELECT id
            FROM bookings
            WHERE user_id = ?
            LIMIT 1
            """,
            (user_id,)
        )

        existing_booking = await cursor.fetchone()

        if existing_booking:

            await db.rollback()

            return (
                False,
                "already_booked"
            )

        # -------------------------------------------------
        # Перевірка робочого дня
        # -------------------------------------------------

        cursor = await db.execute(
            """
            SELECT
                is_closed
            FROM work_days
            WHERE work_date = ?
            """,
            (work_date,)
        )

        work_day = await cursor.fetchone()

        if not work_day:

            await db.rollback()

            return (
                False,
                "day_not_available"
            )

        # -------------------------------------------------
        # День закритий?
        # -------------------------------------------------

        if work_day["is_closed"]:

            await db.rollback()

            return (
                False,
                "day_closed"
            )

        # -------------------------------------------------
        # Перевірка існування слота
        # -------------------------------------------------

        cursor = await db.execute(
            """
            SELECT id
            FROM slots
            WHERE work_date = ?
              AND slot_time = ?
            """,
            (
                work_date,
                slot_time
            )
        )

        slot = await cursor.fetchone()

        if not slot:

            await db.rollback()

            return (
                False,
                "slot_not_found"
            )

        # -------------------------------------------------
        # Перевірка, чи слот вже зайнятий
        # -------------------------------------------------

        cursor = await db.execute(
            """
            SELECT id
            FROM bookings
            WHERE work_date = ?
              AND slot_time = ?
            LIMIT 1
            """,
            (
                work_date,
                slot_time
            )
        )

        existing_slot = await cursor.fetchone()

        if existing_slot:

            await db.rollback()

            return (
                False,
                "slot_taken"
            )

        # -------------------------------------------------
        # Створення запису
        # -------------------------------------------------

        await db.execute(
            """
            INSERT INTO bookings (
                user_id,
                name,
                phone,
                service,
                work_date,
                slot_time
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name,
                phone,
                service,
                work_date,
                slot_time
            )
        )

        await db.commit()

        return (
            True,
            "success"
        )

    except Exception:

        await db.rollback()

        raise

    finally:

        await db.close()


# =========================================================
# ОТРИМАННЯ ЗАПИСІВ
# =========================================================

async def get_bookings_for_date(
    work_date: str
):
    """
    Повертає всі записи на певну дату.
    """

    db = await get_db()

    cursor = await db.execute(
        """
        SELECT *
        FROM bookings
        WHERE work_date = ?
        ORDER BY slot_time
        """,
        (work_date,)
    )

    result = await cursor.fetchall()

    await db.close()

    return result


async def get_all_future_bookings():
    """
    Повертає всі майбутні записи.

    Використовується scheduler.py
    для відновлення нагадувань після запуску бота.
    """

    db = await get_db()

    cursor = await db.execute(
        """
        SELECT *
        FROM bookings
        ORDER BY work_date, slot_time
        """
    )

    result = await cursor.fetchall()

    await db.close()

    return result


# =========================================================
# СКАСУВАННЯ ЗАПИСУ
# =========================================================

async def cancel_booking(
    booking_id: int
):
    """
    Скасовує запис.

    Повертає дані скасованого запису,
    щоб scheduler та handlers могли
    використати їх після видалення.
    """

    db = await get_db()

    try:

        # Спочатку отримуємо запис
        cursor = await db.execute(
            """
            SELECT *
            FROM bookings
            WHERE id = ?
            """,
            (booking_id,)
        )

        booking = await cursor.fetchone()

        if not booking:

            return None

        # Видаляємо запис
        await db.execute(
            """
            DELETE FROM bookings
            WHERE id = ?
            """,
            (booking_id,)
        )

        await db.commit()

        return booking

    finally:

        await db.close()
