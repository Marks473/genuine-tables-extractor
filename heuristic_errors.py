"""
Исключения эвристического разбора таблицы.

Каждому виду нарушения структуры соответствует своё исключение, поэтому по
типу ошибки видно, на какой проверке таблица была отбракована:

* :class:`TitleTypeError` -- в заголовке оказался недопустимый тип данных;
* :class:`DataTypeError`  -- типы данных в столбце не согласуются между собой;
* :class:`LayoutError`    -- нарушена геометрия таблицы (ширины и объединения).
"""


class TitleTypeError(Exception):
    def __init__(self, message: str = ""):
        super().__init__(f"TitleTypeError: {message}")

class DataTypeError(Exception):
    def __init__(self, message: str = ""):
        super().__init__(f"DataTypeError: {message}")

class LayoutError(Exception):
    def __init__(self, message: str = ""):
        super().__init__(f"LayoutError: {message}")
