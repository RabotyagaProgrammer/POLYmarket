import random


def generate_otp():
    """Генерирует случайный 6-значный код."""
    return str(random.randint(10000, 99999))
