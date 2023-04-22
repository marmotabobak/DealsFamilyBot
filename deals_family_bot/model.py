from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, BigInteger, Text, Integer, DateTime
from pydantic import BaseModel
from typing import List


Base = declarative_base()


class TelegramUserConfig(BaseModel):
    tg_bot_user_id: int
    tg_bot_user_name: str


class TelegramConfig(BaseModel):
    tg_bot_api_token: str
    tg_bot_admins: List[int]
    tg_bot_users: List[TelegramUserConfig]


class DatabaseConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str
    db_name: str


class Config(BaseModel):
    db: DatabaseConfig
    telegram: TelegramConfig


class Deal(Base):
    __tablename__ = 'deal'
    __table_args__ = {'schema': 'family_deal_bot'}

    id = Column('deal_id', BigInteger, quote=False, primary_key=True)
    name = Column('deal_name', Text, quote=False)
    ts = Column('deal_ts', DateTime, quote=False)
    user_telegram_id = Column('user_tg_id', Integer, quote=False)