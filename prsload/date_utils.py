from datetime import datetime


def parse_str_to_date(date_str: str) -> datetime:
    if date_str.endswith("Z"):
        date_str = date_str.replace("Z", "+00:00")
    return datetime.fromisoformat(date_str)
