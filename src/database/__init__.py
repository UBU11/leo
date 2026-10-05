from src.database.models import LEAD_STATUSES, LeadStatus

__all__ = ["get_db", "get_db_connection", "init_db", "LEAD_STATUSES", "LeadStatus"]


def __getattr__(name: str):
    if name in ("get_db", "get_db_connection", "init_db"):
        from src.database import connection

        return getattr(connection, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
