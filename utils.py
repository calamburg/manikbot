from datetime import datetime


def format_date(date_string: str):


    date_object = datetime.strptime(
        date_string,
        "%Y-%m-%d"
    )

    return date_object.strftime(
        "%d.%m.%Y"
    )


def validate_phone(phone: str):


    phone = phone.strip()

    allowed = set(
        "0123456789+()- "
    )

    if not all(
        char in allowed
        for char in phone
    ):
        return False

    digits = "".join(
        char
        for char in phone
        if char.isdigit()
    )

    return 9 <= len(digits) <= 15