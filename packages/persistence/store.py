"""Explicit transactions and short-lived database connections."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


class Store:
    def __init__(self, url: str) -> None:
        self.engine: Engine = create_engine(
            url,
            pool_pre_ping=True,
            hide_parameters=True,
            connect_args={"connect_timeout": 3, "options": "-c statement_timeout=10000"}
            if url.startswith("postgresql")
            else {},
        )
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    def session(self) -> Session:
        return self.sessions()
