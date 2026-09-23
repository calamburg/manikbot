import calendar as py_calendar

from datetime import date

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


MONTHS = [
    "Січень",
    "Лютий",
    "Березень",
    "Квітень",
    "Травень",
    "Червень",
    "Липень",
    "Серпень",
    "Вересень",
    "Жовтень",
    "Листопад",
    "Грудень"
]

WEEKDAYS = [
    "Пн",
    "Вт",
    "Ср",
    "Чт",
    "Пт",
    "Сб",
    "Нд"
]


def get_next_month(year: int, month: int):
    if month == 12:
        return year + 1, 1

    return year, month + 1

def build_admin_calendar(year: int, month: int):
    today = date.today()

    keyboard = []
    keyboard.append([
        InlineKeyboardButton(
            text=f"📅 {MONTHS[month - 1]} {year}",
            callback_data="ignore"
        )
    ])
    keyboard.append([
        InlineKeyboardButton(
            text=day,
            callback_data="ignore"
        )
        for day in WEEKDAYS
    ])
    for week in py_calendar.monthcalendar(year, month):
        row = []
        for day_number in week:
            if day_number == 0:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue
            current_date = date(year, month, day_number)
            if current_date < today:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue
            date_str = current_date.isoformat()
            row.append(
                InlineKeyboardButton(
                    text=str(day_number),
                    callback_data=f"admin_workday:{date_str}"
                )
            )
        keyboard.append(row)
    next_year, next_month = get_next_month(year, month)
    navigation = []
    navigation.append(
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"admin_calendar:{next_year}:{next_month}"
        )
    )
    keyboard.append(navigation)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def build_admin_slot_calendar(
    year: int,
    month: int,
    available_dates: set[str]
):
    today = date.today()

    keyboard = []

    # Назва місяця
    keyboard.append([
        InlineKeyboardButton(
            text=f"📅 {MONTHS[month - 1]} {year}",
            callback_data="ignore"
        )
    ])

    # Дні тижня
    keyboard.append([
        InlineKeyboardButton(
            text=day,
            callback_data="ignore"
        )
        for day in WEEKDAYS
    ])

    # Дні місяця
    for week in py_calendar.monthcalendar(year, month):
        row = []

        for day_number in week:

            if day_number == 0:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue

            current_date = date(year, month, day_number)
            date_str = current_date.isoformat()

            # Минулі дати недоступні
            if current_date < today:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue

            # Робочі дні можна вибирати
            if date_str in available_dates:
                row.append(
                    InlineKeyboardButton(
                        text=str(day_number),
                        callback_data=f"admin_slot_date:{date_str}"
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(
                        text=f"{day_number} ❌",
                        callback_data="ignore"
                    )
                )

        keyboard.append(row)

    # Навігація
    next_year, next_month = get_next_month(year, month)

    navigation = [
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"admin_slot_calendar:{next_year}:{next_month}"
        )
    ]

    keyboard.append(navigation)

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


def build_calendar(
    year: int,
    month: int,
    available_dates: set[str]
):
    today = date.today()

    current_year = today.year
    current_month = today.month

    next_year, next_month = get_next_month(
        current_year,
        current_month
    )

    keyboard = []

    keyboard.append([
        InlineKeyboardButton(
            text=f"📅 {MONTHS[month - 1]} {year}",
            callback_data="ignore"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text=day,
            callback_data="ignore"
        )
        for day in WEEKDAYS
    ])

    for week in py_calendar.monthcalendar(
        year,
        month
    ):

        row = []

        for day_number in week:

            if day_number == 0:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue

            current_date = date(
                year,
                month,
                day_number
            )

            date_str = current_date.isoformat()

            # Дата поза дозволеним періодом
            if current_date < today:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )

            elif current_date > date(
                next_year,
                next_month,
                1
            ):
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )

            elif date_str in available_dates:
                row.append(
                    InlineKeyboardButton(
                        text=str(day_number),
                        callback_data=f"date:{date_str}"
                    )
                )

            else:
                row.append(
                    InlineKeyboardButton(
                        text=f"{day_number} ❌",
                        callback_data="ignore"
                    )
                )

        keyboard.append(row)

    navigation = []

    # Назад
    if (year, month) > (
        current_year,
        current_month
    ):
        prev_year = year
        prev_month = month - 1

        if prev_month == 0:
            prev_year -= 1
            prev_month = 12

        navigation.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"calendar:{prev_year}:{prev_month}"
            )
        )

    # Вперед
    if (year, month) < (
        next_year,
        next_month
    ):
        navigation.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"calendar:{next_year}:{next_month}"
            )
        )

    if navigation:
        keyboard.append(navigation)

    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ Меню",
            callback_data="main_menu"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

def build_admin_delete_slot_calendar(
    year: int,
    month: int,
    available_dates: set[str]
):
    today = date.today()

    keyboard = []

    keyboard.append([
        InlineKeyboardButton(
            text=f"📅 {MONTHS[month - 1]} {year}",
            callback_data="ignore"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text=day,
            callback_data="ignore"
        )
        for day in WEEKDAYS
    ])

    for week in py_calendar.monthcalendar(year, month):
        row = []

        for day_number in week:

            if day_number == 0:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue

            current_date = date(year, month, day_number)
            date_str = current_date.isoformat()

            if current_date < today:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue

            if date_str in available_dates:
                row.append(
                    InlineKeyboardButton(
                        text=str(day_number),
                        callback_data=f"admin_delete_slot_date:{date_str}"
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(
                        text=f"{day_number} ❌",
                        callback_data="ignore"
                    )
                )

        keyboard.append(row)

    next_year, next_month = get_next_month(year, month)

    keyboard.append([
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"admin_delete_slot_calendar:{next_year}:{next_month}"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

def build_admin_close_day_calendar(
    year: int,
    month: int,
    available_dates: set[str]
):
    today = date.today()

    keyboard = []

    keyboard.append([
        InlineKeyboardButton(
            text=f"📅 {MONTHS[month - 1]} {year}",
            callback_data="ignore"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text=day,
            callback_data="ignore"
        )
        for day in WEEKDAYS
    ])

    for week in py_calendar.monthcalendar(year, month):
        row = []

        for day_number in week:

            if day_number == 0:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue

            current_date = date(year, month, day_number)
            date_str = current_date.isoformat()

            if current_date < today:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue

            if date_str in available_dates:
                row.append(
                    InlineKeyboardButton(
                        text=str(day_number),
                        callback_data=f"admin_close_date:{date_str}"
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(
                        text=f"{day_number} ❌",
                        callback_data="ignore"
                    )
                )

        keyboard.append(row)

    next_year, next_month = get_next_month(year, month)

    keyboard.append([
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"admin_close_calendar:{next_year}:{next_month}"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

def build_admin_schedule_calendar(
    year: int,
    month: int,
    available_dates: set[str]
):
    today = date.today()

    keyboard = []

    keyboard.append([
        InlineKeyboardButton(
            text=f"📅 {MONTHS[month - 1]} {year}",
            callback_data="ignore"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text=day,
            callback_data="ignore"
        )
        for day in WEEKDAYS
    ])

    for week in py_calendar.monthcalendar(year, month):
        row = []

        for day_number in week:
            if day_number == 0:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue

            current_date = date(year, month, day_number)
            date_str = current_date.isoformat()

            if current_date < today:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue

            if date_str in available_dates:
                row.append(
                    InlineKeyboardButton(
                        text=str(day_number),
                        callback_data=f"admin_schedule_date:{date_str}"
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(
                        text=f"{day_number} ❌",
                        callback_data="ignore"
                    )
                )

        keyboard.append(row)

    next_year, next_month = get_next_month(year, month)

    keyboard.append([
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"admin_schedule_calendar:{next_year}:{next_month}"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

def build_admin_open_day_calendar(
    year: int,
    month: int,
    available_dates: set[str]
):
    today = date.today()

    keyboard = []

    keyboard.append([
        InlineKeyboardButton(
            text=f"📅 {MONTHS[month - 1]} {year}",
            callback_data="ignore"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text=day,
            callback_data="ignore"
        )
        for day in WEEKDAYS
    ])

    for week in py_calendar.monthcalendar(year, month):
        row = []

        for day_number in week:
            if day_number == 0:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue

            current_date = date(year, month, day_number)
            date_str = current_date.isoformat()

            if current_date < today:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue

            if date_str in available_dates:
                row.append(
                    InlineKeyboardButton(
                        text=str(day_number),
                        callback_data=f"admin_open_date:{date_str}"
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(
                        text=f"{day_number} ❌",
                        callback_data="ignore"
                    )
                )

        keyboard.append(row)

    next_year, next_month = get_next_month(year, month)

    keyboard.append([
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"admin_open_calendar:{next_year}:{next_month}"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )

def build_admin_schedule_calendar(
    year: int,
    month: int,
    available_dates: set[str]
):
    today = date.today()

    keyboard = []

    keyboard.append([
        InlineKeyboardButton(
            text=f"📅 {MONTHS[month - 1]} {year}",
            callback_data="ignore"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text=day,
            callback_data="ignore"
        )
        for day in WEEKDAYS
    ])

    for week in py_calendar.monthcalendar(year, month):
        row = []

        for day_number in week:
            if day_number == 0:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue

            current_date = date(year, month, day_number)
            date_str = current_date.isoformat()

            if current_date < today:
                row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
                continue

            if date_str in available_dates:
                row.append(
                    InlineKeyboardButton(
                        text=str(day_number),
                        callback_data=f"admin_schedule_date:{date_str}"
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(
                        text=f"{day_number} ❌",
                        callback_data="ignore"
                    )
                )

        keyboard.append(row)

    next_year, next_month = get_next_month(year, month)

    keyboard.append([
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"admin_schedule_calendar:{next_year}:{next_month}"
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )