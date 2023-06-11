# TODO: write autotests
# TODO: Refactor with classes in outer modules (how to pass dp and how not to use global postgres_engine)
import yaml
import logging
import argparse
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, types, executor
from sqlalchemy import select
from funcs import *

from model import Config, Deal
from postgres import PostgresEngine


logging.basicConfig(
    format='[%(asctime)s | %(levelname)s]: %(message)s',
    datefmt='%m.%d.%Y %H:%M:%S',
    level=logging.INFO
)

parser = argparse.ArgumentParser()
parser.add_argument('--config', '-c', type=str, help='config path')
args = parser.parse_args()
config_path_str = args.config or os.environ.get('APP_CONFIG_PATH')

if config_path_str:
    config_path = Path(config_path_str).resolve()
    logging.info(f'Starting service with config {config_path}')
else:
    raise ValueError('App config path should be provided in -c argument')

logging.info(f'Starting service with config {config_path}')
with open(config_path) as f:
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
    # postgres_engine.drop_and_create_all_tables()
except Exception:
    logging.error(f'[x] Error while initializing Postgres engine')
    raise

postgres_engine.create_all_tables()


@dp.message_handler(commands=['start', 'help'])
async def process_start_command(message: types.Message) -> None:
    global TG_USERS

    output_text = 'Введи бытовое дело в виде текстового сообщения'
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=1)
    markup.add(types.KeyboardButton('Мои дела в этом месяце'))
    for tg_user_id, tg_user_name in TG_USERS.items():
        if tg_user_id != message.from_user.id:
            markup.add(types.KeyboardButton('Дела ' + tg_user_name + ' в этом месяце'))
    markup.add(types.KeyboardButton('Отчет по делам за прошлый месяц'))
    await message.answer(output_text, reply_markup=markup)


@dp.message_handler(regexp=r'.+ела.* месяц.?')
async def view_my_costs(message: types.Message) -> None:

    global postgres_engine
    global TG_USERS

    output_text = ''

    try:
        day_from = first_day_of_current_month()
        day_to = first_day_of_next_month()
        month_name = get_month_name(day_from.month)
        if message.text == 'Мои дела в этом месяце':
            users = {message.from_user.id: TG_USERS[message.from_user.id]}
        elif message.text == 'Отчет по делам за прошлый месяц':
            day_from = first_day_of_last_month()
            day_to = first_day_of_current_month()
            month_name = get_month_name(day_from.month)
            users = TG_USERS
        elif 'Дела ' in message.text:
            user_name = message.text.split('Дела ')[1].split(' в этом месяце')[0]
            user_tg_id = int(next(filter(lambda x: TG_USERS[x] == user_name, TG_USERS.keys())))
            users = {user_tg_id: user_name}
        else:
            raise ValueError

        try:
            session = postgres_engine.session()

            for user_tg_id, user_name in users.items():
                output_text = f'Дела {user_name} за {month_name}:\n'

                stmt = select(Deal).order_by(Deal.ts).where(
                    Deal.user_telegram_id == user_tg_id
                ).where(
                    Deal.ts >= day_from
                ).where(
                    Deal.ts < day_to
                )

                for deal in session.scalars(stmt):
                    output_text += f'    {deal.ts.strftime("%d")} {deal.name}\n'

                await message.answer(output_text)

        except Exception as e:
            logging.error(f'Error while reading database: {e}')
            output_text += f'!ERR! Ошибка чтения из базы данных'
        finally:
            session.close()
            logging.debug('[x] Postgres session closed')

    except (IndexError, ValueError) as e:
        logging.error(f'Error while parsing button message text: {e}')
    except Exception:
        raise


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
