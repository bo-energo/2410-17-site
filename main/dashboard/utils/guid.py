from uuid import uuid4


def generate() -> str:
    """Генерация уникального идентификатора"""
    return str(uuid4())
