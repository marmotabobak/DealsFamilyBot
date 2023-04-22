# TODO: write autotests
# TODO: Refactor with classes in outer modules (how to pass dp and how not to use global postgres_engine)
import yaml
import logging
import datetime

from aiogram import Bot, Dispatcher, types, executor
from sqlalchemy import select, func

from model import Config, Deal
from postgres import PostgresEngine


logging.basicConfig(
    format='[%(asctime)s | %(levelname)s]: %(message)s',
    datefmt='%m.%d.%Y %H:%M:%S',
    level=logging.INFO
)

CONFIG_FILE_PATH = '../configs/dev.yml'

logging.info(f'Starting service with config {CONFIG_FILE_PATH}')
with open(CONFIG_FILE_PATH) as f:
    data = yaml.safe_load(f)

config = Config.parse_obj(data)
logging.info(f'[x] Service started')

TG_USERS = {user.tg_bot_user_id: user.tg_bot_user_name for user in config.telegram.tg_bot_users}
logging.info(f'[x] {len(TG_USERS)} user{"s" if len(TG_USERS) > 1 else ""} info loaded from config')

try:
    bot = Bot(token=config.telegram.tg_bot_api_token)
    dp = Dispatcher(bot)
    logging.info(f'[x] Telegram bot initialized')
except Exception:
    logging.error(f'[x] Error while initializing Telegram bot')
    raise

try:
    postgres_engine = PostgresEngine(config=config.db)
except Exception:
    logging.error(f'[x] Error while initializing Postgres engine')
    raise

postgres_engine.create_all_tables()

def first_day_of_current_month() -> datetime:
    return datetime.datetime(
        year=datetime.datetime.now().year,
        month=datetime.datetime.now().month,
        day=1
    )


def num_with_delimiters(num: int, delimiter: str = ' ') -> str:
    return f'{num:,}'.replace(',', delimiter)


@dp.message_handler(commands=['start', 'help'])
async def process_start_command(message: types.Message) -> None:
    global TG_USERS

    output_text = 'Введи бытовое дело в виде текстового сообщения'
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=1)
    markup.add(types.KeyboardButton('Мои дела в этом месяце'))
    for tg_user_id, tg_user_name in TG_USERS.items():
        if tg_user_id != message.from_user.id:
            markup.add(types.KeyboardButton('Дела ' + tg_user_name + ' в этом месяце'))
    await message.answer(output_text, reply_markup=markup)


@dp.message_handler(regexp=r'.+ела .*в этом месяце')
async def view_my_costs(message: types.Message) -> None:

    global postgres_engine
    global TG_USERS

    output_text = ''

    try:
        if 'Мои дела' in message.text:
            user_tg_id = message.from_user.id
        else:
            another_user_name = message.text.split('Дела ')[1].split(' в этом месяце')[0]
            user_tg_id = int(next(filter(lambda x: TG_USERS[x] == another_user_name, TG_USERS.keys())))
    except IndexError as e:
        user_tg_id = None
        logging.error(f'Error while parsing button text for user_name: {e}')
        output_text = f'!ERR! Ошибка определения имени пользователя'
    except Exception:
        raise

    if user_tg_id:
        output_text = ''

        session = postgres_engine.session()
        try:
            stmt = select(Deal).order_by(Deal.ts).where(
                Deal.user_telegram_id == user_tg_id
            ).where(
                Deal.ts >= first_day_of_current_month()
            )

            for deal in session.scalars(stmt):
                output_text += f'{deal.ts.strftime("%d")} {deal.name}\n'

        except Exception as e:
            logging.error(f'Error while reading database: {e}')
            output_text += f'!ERR! Ошибка чтения из базы данных'
        finally:
            session.close()
            logging.debug('[x] Postgres session closed')

    if not output_text:
        output_text = 'Данных за период нет...'

    await message.answer(output_text)


@dp.message_handler(lambda message: message.from_user.id in (
        user.tg_bot_user_id for user in config.telegram.tg_bot_users
))
async def process_regular_message(message: types.Message):
    global postgres_engine

    if message.text:
        now_ts = datetime.datetime.now()
        session = postgres_engine.session()
        try:

            session.add(
                Deal(
                    name=message.text,
                    ts=now_ts,
                    user_telegram_id=message.from_user.id
                )
            )
            session.commit()

            output_text = f'Внесено дело:\n    время: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}'\
                          f'\n    название: {message.text}'

            logging.info('[x] Data added to database')
        except Exception as e:
            output_text = '!ERR! Ошибка записи данных в базу'
            logging.error(f'Error while writing to database: {e}')
        finally:
            session.close()
            logging.debug('[x] Postgres session closed')

    else:
        logging.error('Empty data - skipping...')
        output_text = 'Пустое значение - пропускаю...'

    await message.answer(output_text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
