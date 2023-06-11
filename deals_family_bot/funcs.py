import datetime


def first_day_of_current_month() -> datetime:
    return datetime.datetime(
        year=datetime.datetime.now().year,
        month=datetime.datetime.now().month,
        day=1
    )


def num_with_delimiters(num: int, delimiter: str = ' ') -> str:
    return f'{num:,}'.replace(',', delimiter)


def first_day_of_next_month() -> datetime:
    next_month_datetime = first_day_of_current_month() + datetime.timedelta(days=32)
    return datetime.datetime(
        year=next_month_datetime.year,
        month=next_month_datetime.month,
        day=1
    )


def get_month_name(month_num: int) -> str:
    if month_num in range(1, 13):
        months = ('январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь')
        return months[month_num-1]
    else:
        raise ValueError('Month number should be integer from 1 to 12')


def last_day_of_last_month() -> datetime:
    return first_day_of_current_month() - datetime.timedelta(days=1)


def first_day_of_last_month() -> datetime:
    return datetime.datetime(
        year=last_day_of_last_month().year,
        month=last_day_of_last_month().month,
        day=1
    )