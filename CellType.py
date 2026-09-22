from enum import Enum, auto
import re
from typing import Set


class ClassCell(Enum):
    CELL_TITLE = auto()
    CELL_DATA = auto()
    CELL_RESULT = auto()
    CELL_NOT_DEFINE = auto()
    CELL_SIDEBAR = auto()


class DataType(Enum):
    """Основные типы данных (Уровень 2 из диаграммы)."""
    GENUINE = auto()
    FORM = auto()
    STRING = auto()
    MEDIA = auto()
    OTHER = auto()
    NO_DATA = auto()
    LINK = auto()


class DetailedDataType(Enum):
    """Детализированные типы данных (Уровень 3 из диаграммы)."""
    # Для Форм
    BUTTON = auto()
    INPUT_BOX = auto()
    # Для Медиа
    PHOTO = auto()
    VIDEO = auto()
    AUDIO = auto()
    MIXED = auto()  # Медиа + ссылка + текст
    # Для Подлинных
    DATE = auto()
    TIME = auto()
    MONEY = auto()
    PERCENT = auto()
    MEASUREMENT = auto()  # Размерная величина с единицами измерения
    DIMENSION = auto()  # Число без единиц измерения
    # Для Строки
    STRING = auto()
    # Для Ссылки
    LINK = auto()
    # Для остальных
    OTHER = auto()
    # Для нет данных
    NO_DATA = auto()


# =====================================================================
# Константы и вспомогательные функции
# =====================================================================

# Теги для оформления текста
TEXT_FORMATTING_TAGS = {
    'b', 'strong', 'i', 'em', 'u', 's', 'strike', 'del', 'ins',
    'mark', 'small', 'sub', 'sup', 'code', 'kbd', 'samp', 'var',
    'pre', 'span', 'font', 'br', 'wbr', 'dfn', 'div', 'h1', 'h2',
    'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'h9', 'p', 'abbr',
}

# Медиа теги
MEDIA_TAGS = {'img', 'video', 'audio', 'picture', 'source'}

# Теги форм
FORM_TAGS = {'input', 'button', 'select', 'textarea'}

# Множество для NO_DATA
NO_DATA_VALUES = {'', '-', '—', 'n/d', ' ', 'н/д', 'н/a', 'N/A', 'n/a', 'NA'}


def _has_only_formatting_tags(tags: Set[str], base_tag: str = 'td') -> bool:
    """
    Проверяет, содержит ли множество тегов только теги оформления текста.

    Args:
        tags: множество тегов
        base_tag: базовый тег ячейки (td или th)

    Returns:
        True если только теги оформления (и базовый тег), иначе False
    """
    # Убираем базовый тег (td или th)
    tags_without_base = tags - {base_tag, 'td', 'th'}

    # Если тегов не осталось - значит только базовый тег
    if not tags_without_base:
        return True

    # Проверяем, что все оставшиеся теги - это теги форматирования
    return tags_without_base.issubset(TEXT_FORMATTING_TAGS)


def _has_only_formatting_and_link_tags(tags: Set[str], base_tag: str = 'td') -> bool:
    """
    Проверяет, содержит ли множество только теги оформления и ссылку.

    Args:
        tags: множество тегов
        base_tag: базовый тег ячейки

    Returns:
        True если только теги оформления и/или ссылка
    """
    tags_without_base = tags - {base_tag, 'td', 'th'}
    allowed_tags = TEXT_FORMATTING_TAGS | {'a'}
    return tags_without_base.issubset(allowed_tags)


# =====================================================================
# Паттерны для распознавания типов данных
# =====================================================================

# Паттерны для дат
DATE_PATTERNS = [
    # Форматы: 2024-01-15, 15.01.2024, 15/01/2024, 01-15-2024 и т.д.
    r'\b\d{1,4}[-/.\\ ]\d{1,2}[-/.\\ ]\d{1,4}\b',

    # Форматы: "15 января 2024", "январь 2024", "15 январь 2024" и т.д.
    r'\b(?:\d{1,2}\s+)?(январ[ьяь]|феврал[ьяь]|март[а]?|апрел[ья]|ма[йя]|июн[ьяь]|июл[ьяь]|август[а]?|сентябр[ьяь]|октябр[ьяь]|ноябр[ьяь]|декабр[ьяь])\.?,?\s+\d{2,4}\b',

    # Форматы с сокращениями: "15 янв. 2024", "сен 2024"
    r'\b(?:\d{1,2}\s+)?(янв|фев|мар|апр|май|июн|июл|авг|сен|окт|ноя|дек)\.?\s+\d{2,4}\b',

    # Форматы: "January 15, 2024", "Jan 15 2024", "Jan. 15, 2024"
    r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
    r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\b',

    # Форматы: "2024 January 15", "2024 January"
    r'\b\d{4}\s+(January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+\d{1,2})?\b',
]

# Паттерны для времени
TIME_PATTERNS = [
    # Форматы: 14:30, 14:30:00, 14:30:00.123
    r'\b\d{1,2}:\d{2}(:\d{2})?(\.\d+)?\b',
    # Форматы с AM/PM: 2:30 PM, 02:30 pm
    r'\b\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM|am|pm)\b',
]

# Паттерны для денег
MONEY_PATTERNS = [
    # $100, €50, £30, ¥1000, ₽500 (символ валюты перед числом)
    r'[$€£¥₽]\s*\d{1,3}([,\s]\d{3})*([.,]\d{1,2})?',

    # 100$, 50€, 30£, 1000¥, 500₽ (символ валюты после числа)
    r'\d{1,3}([,\s]\d{3})*([.,]\d{1,2})?\s*[$€£¥₽]',

    # 100 USD, 50 EUR, 30 GBP (буквенные коды валют)
    r'\d{1,3}([,\s]\d{3})*([.,]\d{1,2})?\s+(USD|EUR|GBP|JPY|RUB|usd|eur|gbp|jpy|rub|руб|р|руб.)\b',
]

# Паттерн для процентов
PERCENT_PATTERN = r'\d+([.,]\d+)?\s*%'

# Паттерн для размерных величин (MEASUREMENT)
# Поддерживаются единицы измерения:
UNITS_PATTERN_CORE = r'\d+([.,]\d+)?\s*(мм|см|м|км|mm|cm|m|km|миллиметр|сантиметр|метр|километр|millimeter|centimeter|meter|kilometer|' \
                      r'дюйм|дюйма|дюймов|фут|фута|футов|ярд|ярда|ярдов|миля|мили|миль|inch|inches|in|ft|foot|feet|yard|yards|yd|mile|miles|mi|' \
                      r'м²|см²|км²|мм²|sq m|sq cm|sq km|sq mm|square meter|square centimeter|' \
                      r'л|мл|литр|литра|литров|миллилитр|миллилитра|миллилитров|l|ml|liter|liters|milliliter|milliliters|' \
                      r'г|г/л|кг|т|мг|грамм|грамма|граммов|килограмм|килограмма|килограммов|тонн|тонна|тонны|g|kg|mg|ton|tons|tonne|tonnes|gram|grams|kilogram|kilograms|' \
                      r'°C|°F|°K|градус|градуса|градусов|celsius|fahrenheit|kelvin|' \
                      r'Вт|кВт|МВт|ватт|ватта|ваттов|киловатт|киловатта|киловаттов|w|kw|mw|watt|watts|kilowatt|kilowatts|' \
                      r'В|в|вольт|вольта|вольтов|v|volt|volts|' \
                      r'А|а|ампер|ампера|амперов|a|amp|amps|ampere|amperes|' \
                      r'Гц|гц|герц|герца|герцов|hz|hertz|' \
                      r'Па|па|паскаль|паскаля|паскалей|pa|pascal|pascals|' \
                      r'бит|бита|битов|байт|байта|байтов|кб|мб|гб|тб|kb|mb|gb|tb|byte|bytes|kilobyte|megabyte|gigabyte|terabyte)' \
                      r'\b'

MEASUREMENT_PATTERN = f"^\s*({UNITS_PATTERN_CORE})\s*$"

# Паттерн для чисел без единиц измерения (DIMENSION)
DIMENSION_PATTERNS = [
    # 1. Целое число (положительное или отрицательное): 12, -12, - 12
    r'^\s*-?\s*\d+\s*$',

    # 2. Дробное число (положительное или отрицательное): 12.5, -12,5, - 12.5
    r'^\s*-?\s*\d+[.,]\d+\s*$',


    # 3. Целые числа с пробелами (положительные или отрицательные):
    #    -12 123, 123 456 789, - 12 123
    r'^\s*-?\s*\d+(?:\s+\d+)+\s*$',

    # 4. Дробные числа с пробелами (положительные или отрицательные):
    #    -12 123.5, 123 456,78, - 12 345.67
    r'^\s*-?\s*\d+(?:\s+\d+)*\s+\d+[.,]\d+\s*$',

    # 5. Дробные числа с пробелами без целой части (положительные или отрицательные):
    #    -.5, ,78, -.67
    r'^\s*[+-]?[.,]\d+\s*$',

    # 6. Разряды, разделённые запятой (английская запись): 1,368,524, -12,345.67
    #    Требуется не менее двух групп ровно по три цифры, иначе запись
    #    неотличима от обычного дробного числа вида 154,977
    r'^\s*-?\s*\d{1,3}(?:,\d{3})+(?:\.\d+)?\s*$',

    # 7. Разряды, разделённые точкой (европейская запись): 1.368.524, -12.345,67
    r'^\s*-?\s*\d{1,3}(?:\.\d{3})+(?:,\d+)?\s*$',
]


# =====================================================================
# Основные функции
# =====================================================================

def detailType(tags: set, contents: str) -> DetailedDataType:
    """
    Определяет детальный тип данных ячейки.

    Args:
        tags: множество всех тегов в ячейке
        contents: текстовое содержимое ячейки

    Returns:
        DetailedDataType - детальный тип ячейки
    """
    # Нормализуем контент
    content_stripped = contents.strip()
    content_lower = content_stripped.lower()

    # Определяем базовый тег
    base_tag = 'th' if 'th' in tags else 'td'

    # 1. NO_DATA - пустая ячейка или специальные значения
    if (content_stripped in NO_DATA_VALUES) and _has_only_formatting_tags(tags, base_tag):
        return DetailedDataType.NO_DATA

    # 2. BUTTON - только кнопка + теги оформления
    if 'button' in tags:
        tags_without_form = tags - FORM_TAGS
        if _has_only_formatting_tags(tags_without_form, base_tag):
            return DetailedDataType.BUTTON

    # 3. INPUT_BOX - только input/select/textarea + теги оформления
    input_tags = {'input', 'select', 'textarea'}
    if tags & input_tags:
        tags_without_form = tags - FORM_TAGS
        if _has_only_formatting_tags(tags_without_form, base_tag):
            return DetailedDataType.INPUT_BOX

    # Проверяем наличие медиа тегов
    has_img = 'img' in tags
    has_video = 'video' in tags
    has_audio = 'audio' in tags
    has_media = has_img or has_video or has_audio
    has_link = 'a' in tags
    has_text = len(content_stripped) > 0

    # 4-6. PHOTO, VIDEO, AUDIO - только медиа тег без текста
    if has_img and not has_text:
        return DetailedDataType.PHOTO
    if has_video and not has_text:
        return DetailedDataType.VIDEO
    if has_audio and not has_text:
        return DetailedDataType.AUDIO

    # 7. MIXED - медиа + (ссылка или текст)
    if has_media:
        # Если есть медиа и (ссылка ИЛИ текст) - это MIXED
        if (has_link and has_text) or (has_media and has_text and len(content_stripped) > 3):
            return DetailedDataType.MIXED
        # Если есть медиа и ссылка без текста
        if has_link:
            return DetailedDataType.MIXED

    # Проверяем, что теги только для оформления (и возможно ссылки)
    only_formatting = _has_only_formatting_tags(tags, base_tag)
    only_formatting_and_link = _has_only_formatting_and_link_tags(tags, base_tag)

    # 8. DATE - дата в любом формате
    if only_formatting_and_link:
        for pattern in DATE_PATTERNS:
            if re.search(pattern, contents, re.IGNORECASE):
                return DetailedDataType.DATE

    # 9. TIME - время в любом формате
    if only_formatting_and_link:
        for pattern in TIME_PATTERNS:
            if re.search(pattern, contents):
                return DetailedDataType.TIME

    # 10. MONEY - деньги
    if only_formatting_and_link:
        for pattern in MONEY_PATTERNS:
            if re.search(pattern, contents):
                return DetailedDataType.MONEY

    # 11. PERCENT - проценты
    if only_formatting_and_link:
        if re.search(PERCENT_PATTERN, contents):
            return DetailedDataType.PERCENT

    # 12. MEASUREMENT - размерные величины с единицами измерения
    # ВАЖНО: Проверяется ПЕРЕД DIMENSION!
    if only_formatting_and_link:
        if re.search(MEASUREMENT_PATTERN, content_stripped, re.IGNORECASE):
            return DetailedDataType.MEASUREMENT

    # 13. DIMENSION - числа без единиц измерения (целые или дробные)
    if only_formatting_and_link:
        for pattern in DIMENSION_PATTERNS:
            if re.match(pattern, content_stripped):
                return DetailedDataType.DIMENSION

    # 14. LINK - только ссылка + теги оформления
    if has_link and only_formatting_and_link:
        return DetailedDataType.LINK

    # 15. STRING - обычный текст (только теги оформления, без ссылок)
    if only_formatting and has_text:
        return DetailedDataType.STRING

    # 16. OTHER - все остальное
    return DetailedDataType.OTHER


def type(tags: set, contents: str) -> DataType:
    """
    Определяет основной тип данных ячейки на основе детального типа.

    Args:
        tags: множество всех тегов в ячейке
        contents: текстовое содержимое ячейки

    Returns:
        DataType - основной тип ячейки
    """
    # Получаем детальный тип
    detail_type = detailType(tags, contents)

    # 1. GENUINE - подлинные данные
    genuine_types = {
        DetailedDataType.DATE,
        DetailedDataType.TIME,
        DetailedDataType.MONEY,
        DetailedDataType.PERCENT,
        DetailedDataType.MEASUREMENT,  # Добавлен новый тип!
        DetailedDataType.DIMENSION,
    }
    if detail_type in genuine_types:
        return DataType.GENUINE

    # 2. FORM - формы
    form_types = {
        DetailedDataType.BUTTON,
        DetailedDataType.INPUT_BOX,
    }
    if detail_type in form_types:
        return DataType.FORM

    # 3. STRING - строковые данные
    if detail_type == DetailedDataType.STRING:
        return DataType.STRING

    # 4. MEDIA - медиа данные
    media_types = {
        DetailedDataType.PHOTO,
        DetailedDataType.VIDEO,
        DetailedDataType.AUDIO,
        DetailedDataType.MIXED,
    }
    if detail_type in media_types:
        return DataType.MEDIA

    # 5. NO_DATA - нет данных
    if detail_type == DetailedDataType.NO_DATA:
        return DataType.NO_DATA

    # 6. LINK - ссылки
    if detail_type == DetailedDataType.LINK:
        return DataType.LINK

    # 7. OTHER - все остальное
    return DataType.OTHER


# =====================================================================
# Тестовый код для проверки
# =====================================================================

if __name__ == "__main__":
    # Примеры тестирования
    test_cases = [
        # (tags, content, описание)
        ({'td', 'b'}, '2024-01-15', 'Дата с жирным шрифтом'),
        ({'td'}, '14:30:00', 'Время'),
        ({'td'}, '$100.50', 'Деньги'),
        ({'td', 'i'}, '75.5%', 'Проценты'),
        ({'td'}, '10 см', 'Размерная величина (см)'),
        ({'td'}, '12.5 mm', 'Размерная величина (mm)'),
        ({'td'}, '100 км', 'Размерная величина (км)'),
        ({'td'}, '5.5 inches', 'Размерная величина (inches)'),
        ({'td'}, '250 кг', 'Размерная величина (кг)'),
        ({'td'}, '3.5 л', 'Размерная величина (л)'),
        ({'td'}, '25°C', 'Размерная величина (градусы)'),
        ({'td'}, '12.5', 'Число без единиц (DIMENSION)'),
        ({'td'}, '100', 'Целое число (DIMENSION)'),
        ({'td', 'button'}, 'Нажми', 'Кнопка'),
        ({'td', 'input'}, '', 'Поле ввода'),
        ({'td', 'img'}, '', 'Изображение'),
        ({'td', 'a'}, 'Ссылка', 'Ссылка'),
        ({'td'}, '', 'Пустая ячейка'),
        ({'td', 'b', 'i'}, 'Обычный текст', 'Текст с форматированием'),
        ({'td', 'img', 'a'}, '21 руб.', 'Смешанный тип'),
    ]

    print("=" * 90)
    print("Тестирование функций type() и detailType() с поддержкой MEASUREMENT")
    print("=" * 90)

    for tags, content, description in test_cases:
        data_type = type(tags, content)
        detail_type = detailType(tags, content)
        print(f"\n📋 {description}")
        print(f"   Теги: {tags}")
        print(f"   Контент: '{content}'")
        print(f"   ➜ DataType: {data_type.name}")
        print(f"   ➜ DetailedDataType: {detail_type.name}")