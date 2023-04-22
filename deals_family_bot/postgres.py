import logging

from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from model import DatabaseConfig, Base


class PostgresEngine:

    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config
        try:
            self._engine = create_engine(
                f'postgresql://{self._config.db_name}:{self._config.password}@{self._config.host}:{self._config.port}',
                echo=False
            )
            self._engine.connect()
            logging.info('[x] Postgres engine created')
        except Exception:
            logging.error('Error while creating Postgres Engine')
            raise

    def session(self) -> Session:
        try:
            result = Session(bind=self._engine)
            logging.debug('[x] Postgres session created')
            return result
        except:
            logging.error('Error while creating Postgres session')
            raise

    def drop_all_tables(self) -> None:
        try:
            Base.metadata.drop_all(self._engine)
            logging.info('[x] All service tables dropped')
        except Exception as e:
            logging.error(f'Error while dropping tables: {e}')

    def create_all_tables(self) -> None:
        try:
            Base.metadata.create_all(self._engine)
            logging.info('[x] All service tables created')
        except Exception as e:
            logging.error(f'Error while creating tables: {e}')

    def drop_and_create_all_tables(self) -> None:
        self.drop_all_tables()
        self.create_all_tables()
