# check_exists.py - модуль, который проверяет данные пользователя на корректность
import requests

URL = "https://api.newlxp.ru"


def login_data(email, password):
    """Логинимся"""

    data = {"email": email, "password": password}
    response = requests.get(URL, data=data)

    if response.status_code == 200:
        return True
    return False